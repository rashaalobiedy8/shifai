"""
إدارة الملف الصحي الرقمي - تخزين محلي في JSON
================================================
كل مستخدم له ملف JSON منفصل في data/users/patient_<ID>.json
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path

# المسار - نستخدم نفس بنية config.py
try:
    from src.config import DATA_DIR
except ImportError:
    DATA_DIR = Path(__file__).parent.parent / 'data'

RECORDS_DIR = DATA_DIR / 'users'
RECORDS_DIR.mkdir(parents=True, exist_ok=True)


class HealthRecord:
    """ملف صحي رقمي لمستخدم واحد"""

    def __init__(self, patient_id=None, name=None, age=None, gender=None,
                 blood_type=None, chronic_diseases=None, allergies=None):
        """
        إنشاء ملف جديد أو تحميل موجود:
        - لو عطيت patient_id موجود، يُحمّل
        - لو عطيت بيانات جديدة، يُنشأ
        """
        if patient_id is None:
            # توليد رقم فريد
            seed = f"{name}|{age}|{datetime.now().isoformat()}"
            patient_id = hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]

        self.patient_id = patient_id
        self.file = RECORDS_DIR / f"patient_{patient_id}.json"

        if self.file.exists():
            self._load()
        else:
            self.data = {
                'patient_id': patient_id,
                'name': name,
                'age': age,
                'gender': gender,
                'blood_type': blood_type,
                'chronic_diseases': self._split(chronic_diseases),
                'allergies': self._split(allergies),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'visits': [],
                'prescriptions': []
            }
            self._save()

    # ============ أدوات داخلية ============

    @staticmethod
    def _split(text):
        """يحول نص 'أ, ب, ج' إلى قائمة"""
        if not text:
            return []
        if isinstance(text, list):
            return [x.strip() for x in text if x.strip()]
        return [x.strip() for x in str(text).split(',') if x.strip()]

    def _save(self):
        """حفظ الملف على القرص"""
        self.data['updated_at'] = datetime.now().isoformat()
        self.file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    def _load(self):
        """تحميل الملف من القرص"""
        self.data = json.loads(self.file.read_text(encoding='utf-8'))

    # ============ عمليات الملف الصحي ============

    def add_visit(self, symptoms, diagnosis, drugs=None, notes=None):
        """إضافة زيارة طبية"""
        visit = {
            'date': datetime.now().isoformat(),
            'symptoms': self._split(symptoms),
            'diagnosis': diagnosis,
            'drugs': self._split(drugs),
            'notes': notes
        }
        self.data['visits'].append(visit)
        self._save()
        return visit

    def add_prescription(self, drug, dose, duration, doctor=None):
        """إضافة وصفة طبية"""
        rx = {
            'date': datetime.now().isoformat(),
            'drug': drug,
            'dose': dose,
            'duration': duration,
            'doctor': doctor
        }
        self.data['prescriptions'].append(rx)
        self._save()
        return rx

    def check_allergy(self, drug):
        """
        فحص إن كان الدواء ضمن قائمة الحساسية
        يرجع dict فيه:
        - has_allergy: True/False
        - matched: اسم الحساسية المطابق (لو موجود)
        """
        drug_l = drug.lower().strip()
        for allergy in self.data.get('allergies', []):
            a_l = allergy.lower().strip()
            if drug_l in a_l or a_l in drug_l:
                return {'has_allergy': True, 'matched': allergy}
        return {'has_allergy': False, 'matched': None}

    def check_chronic_conflict(self, drug_condition):
        """
        فحص إن كان الدواء يتعارض مع مرض مزمن
        (مقارنة نصية بسيطة - للتوسع لاحقاً)
        """
        cond_l = drug_condition.lower().strip()
        conflicts = []
        for disease in self.data.get('chronic_diseases', []):
            d_l = disease.lower().strip()
            if d_l in cond_l or cond_l in d_l:
                conflicts.append(disease)
        return conflicts

    def get_summary(self):
        """ملخص سريع للملف"""
        return {
            'patient_id': self.patient_id,
            'name': self.data.get('name'),
            'age': self.data.get('age'),
            'gender': self.data.get('gender'),
            'blood_type': self.data.get('blood_type'),
            'chronic_diseases': self.data.get('chronic_diseases', []),
            'allergies': self.data.get('allergies', []),
            'visits_count': len(self.data.get('visits', [])),
            'prescriptions_count': len(self.data.get('prescriptions', [])),
        }

    # ============ طرق الفئة (class methods) ============

    @classmethod
    def load(cls, patient_id):
        """تحميل ملف موجود برقمه - يرجع None لو ما موجود"""
        file = RECORDS_DIR / f"patient_{patient_id}.json"
        if not file.exists():
            return None
        return cls(patient_id=patient_id)

    @classmethod
    def list_all(cls):
        """قائمة بكل الملفات المحفوظة"""
        files = list(RECORDS_DIR.glob('patient_*.json'))
        return [f.stem.replace('patient_', '') for f in files]

    @classmethod
    def delete(cls, patient_id):
        """حذف ملف صحي"""
        file = RECORDS_DIR / f"patient_{patient_id}.json"
        if file.exists():
            file.unlink()
            return True
        return False


# ============ اختبار سريع ============
if __name__ == '__main__':
    # إنشاء ملف تجريبي
    h = HealthRecord(
        name='أحمد محمد',
        age=35,
        gender='ذكر',
        blood_type='O+',
        chronic_diseases='سكري, ضغط',
        allergies='بنسلين, أسبرين'
    )
    print('✅ تم إنشاء ملف:', h.patient_id)
    print('📋 الملخص:', h.get_summary())

    # إضافة زيارة
    h.add_visit(
        symptoms='صداع, حرارة',
        diagnosis='إنفلونزا',
        drugs='باراسيتامول',
        notes='راحة 3 أيام'
    )
    print('✅ تمت إضافة زيارة')

    # فحص الحساسية
    print('🔍 فحص بنسلين:', h.check_allergy('بنسلين'))
    print('🔍 فحص باراسيتامول:', h.check_allergy('باراسيتامول'))

    # تحميل من جديد
    h2 = HealthRecord.load(h.patient_id)
    print('✅ تم التحميل:', h2.get_summary())