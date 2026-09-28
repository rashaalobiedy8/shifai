"""
فحص التفاعلات الدوائية
========================
- فهرس hash سريع: (drug1_lower, drug2_lower) → وصف
- قاموس عربي-إنجليزي للأدوية الشائعة
- rapidfuzz للبحث الضبابي عند عدم وجود تطابق دقيق
"""
import pandas as pd
from pathlib import Path
from functools import lru_cache

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

try:
    from src.config import INTERACTIONS_FILE
except ImportError:
    INTERACTIONS_FILE = Path(__file__).parent.parent / 'data' / 'raw' / 'db_drug_interactions.xlsx'


# ============ قاموس الترجمة العربي ============
ARABIC_DRUG_MAP = {
    # مسكنات
    'باراسيتامول': 'Acetaminophen',
    'أسيتامينوفين': 'Acetaminophen',
    'باراسيتامول': 'Acetaminophen',
    'إيبوبروفين': 'Ibuprofen',
    'أسبرين': 'Aspirin',
    'نابروكسين': 'Naproxen',
    'ديكلوفيناك': 'Diclofenac',
    'كيتوبروفين': 'Ketoprofen',
    'مورفين': 'Morphine',
    'ترامادول': 'Tramadol',
    'كودايين': 'Codeine',

    # مضادات حيوية
    'أموكسيسيلين': 'Amoxicillin',
    'أمبيسيلين': 'Ampicillin',
    'أزيثرومايسين': 'Azithromycin',
    'كلاريثرومايسين': 'Clarithromycin',
    'سيبروفلوكساسين': 'Ciprofloxacin',
    'ميترونيدازول': 'Metronidazole',
    'دوكسيسايكلين': 'Doxycycline',
    'تتراسايكلين': 'Tetracycline',

    # معدية
    'أوميبرازول': 'Omeprazole',
    'إيزوميبرازول': 'Esomeprazole',
    'بانتوبرازول': 'Pantoprazole',
    'رانييتيدين': 'Ranitidine',
    'ميتوكلوبراميد': 'Metoclopramide',

    # قلب وضغط
    'أتورفاستاتين': 'Atorvastatin',
    'سيمفاستاتين': 'Simvastatin',
    'روزوفاستاتين': 'Rosuvastatin',
    'أملوديبين': 'Amlodipine',
    'ليسينوبريل': 'Lisinopril',
    'إينالابريل': 'Enalapril',
    'فالسارتان': 'Valsartan',
    'لوسارتان': 'Losartan',
    'ميتوبرولول': 'Metoprolol',
    'أتينولول': 'Atenolol',
    'وارفارين': 'Warfarin',
    'كلوبيدوغريل': 'Clopidogrel',
    'ديجوكسين': 'Digoxin',
    'فوروسيميد': 'Furosemide',
    'هيدروكلوروثيازيد': 'Hydrochlorothiazide',

    # سكر
    'ميتفورمين': 'Metformin',
    'غلوكوفاج': 'Metformin',
    'إنسولين': 'Insulin',
    'غليبوريد': 'Glyburide',
    'غليميبيريد': 'Glimepiride',

    # نفسية
    'سيرترالين': 'Sertraline',
    'فلوكسيتين': 'Fluoxetine',
    'باروكسيتين': 'Paroxetine',
    'أميتريبتيلين': 'Amitriptyline',
    'ديازيبام': 'Diazepam',
    'ألبرازولام': 'Alprazolam',
    'زولبيديم': 'Zolpidem',

    # غدة درقية
    'ليفوثيروكسين': 'Levothyroxine',

    # حساسية
    'ديفينهيدرامين': 'Diphenhydramine',
    'لوراتادين': 'Loratadine',
    'سيتيريزين': 'Cetirizine',

    # فطريات
    'فلوكونازول': 'Fluconazole',
    'كلوتريمازول': 'Clotrimazole',
}
# مرادفات الأسماء الشائعة → الأسماء العلمية في الداتابيس
DRUG_SYNONYMS = {
    # ===== Aspirin =====
    'aspirin': 'acetylsalicylic acid',
    'aspirine': 'acetylsalicylic acid',
    'asa': 'acetylsalicylic acid',
    'أسبرين': 'acetylsalicylic acid',

    # ===== Paracetamol / Tylenol / Panadol =====
    'paracetamol': 'acetaminophen',
    'tylenol': 'acetaminophen',
    'panadol': 'acetaminophen',
    'adol': 'acetaminophen',
    'باراسيتامول': 'acetaminophen',
    'أسيتامينوفين': 'acetaminophen',
    'بنادول': 'acetaminophen',
    'أدول': 'acetaminophen',

    # ===== Ibuprofen =====
    'ibuprofen': 'ibuprofen',
    'advil': 'ibuprofen',
    'brufen': 'ibuprofen',
    'إيبوبروفين': 'ibuprofen',
    'بروفين': 'ibuprofen',

    # ===== Diclofenac =====
    'diclofenac': 'diclofenac',
    'voltaren': 'diclofenac',
    'cataflam': 'diclofenac',
    'ديكلوفيناك': 'diclofenac',
    'فولتارين': 'diclofenac',

    # ===== Metformin =====
    'metformin': 'metformin',
    'glucophage': 'metformin',
    'ميتفورمين': 'metformin',
    'غلوكوفاج': 'metformin',

    # ===== Atorvastatin =====
    'atorvastatin': 'atorvastatin',
    'lipitor': 'atorvastatin',
    'أتورفاستاتين': 'atorvastatin',
    'ليبيتور': 'atorvastatin',

    # ===== Bisoprolol =====
    'bisoprolol': 'bisoprolol',
    'concor': 'bisoprolol',
    'بيسوبرولول': 'bisoprolol',
    'كونكور': 'bisoprolol',

    # ===== Omeprazole =====
    'omeprazole': 'omeprazole',
    'losec': 'omeprazole',
    'أوميبرازول': 'omeprazole',
    'لوسك': 'omeprazole',

    # ===== Amoxicillin =====
    'amoxicillin': 'amoxicillin',
    'amoxil': 'amoxicillin',
    'أموكسيسيلين': 'amoxicillin',
    'أموكسيل': 'amoxicillin',
}


class InteractionChecker:
    """فاحص التفاعلات الدوائية"""

    def __init__(self, use_fuzzy=True, fuzzy_threshold=85):
        """
        use_fuzzy: تفعيل البحث الضبابي
        fuzzy_threshold: نسبة التشابه الدنيا (0-100)
        """
        self.use_fuzzy = use_fuzzy and HAS_RAPIDFUZZ
        self.fuzzy_threshold = fuzzy_threshold
        self.df = None
        self.index = {}
        self.drugs_set = set()
        self._load_data()

    # ============ تحميل البيانات ============

    def _load_data(self):
        """تحميل Excel وبناء الفهرس"""
        try:
            self.df = pd.read_excel(INTERACTIONS_FILE)
            # تنظيف: strip + تعبئة النصوص
            self.df['Drug 1'] = self.df['Drug 1'].astype(str).str.strip()
            self.df['Drug 2'] = self.df['Drug 2'].astype(str).str.strip()
            self.df['Interaction Description'] = (
                self.df['Interaction Description'].astype(str).str.strip()
            )

            # بناء الفهرس: (lower1, lower2) مرتب أبجدياً
            for _, row in self.df.iterrows():
                d1 = row['Drug 1'].lower()
                d2 = row['Drug 2'].lower()
                key = tuple(sorted([d1, d2]))
                self.index[key] = row['Interaction Description']
                self.drugs_set.add(d1)
                self.drugs_set.add(d2)

        except Exception as e:
            raise RuntimeError(f"فشل تحميل ملف التفاعلات: {e}")

    # ============ تطبيع الأسماء ============

    @staticmethod
    def normalize(name):
        """تطبيع اسم الدواء: strip + lower + ترجمة عربي + مرادفات"""
        if not name:
            return ''
        name = str(name).strip()

        # 1) ترجمة عربي → إنجليزي (بالحالة الأصلية)
        if name in ARABIC_DRUG_MAP:
            name = ARABIC_DRUG_MAP[name]

        # 2) lowercase
        name = name.lower()

        # 3) مرادفات إنجليزي → اسم علمي في الداتابيس
        if name in DRUG_SYNONYMS:
            name = DRUG_SYNONYMS[name]

        return name
    # ============ البحث ============

    @lru_cache(maxsize=256)
    def suggest_similar(self, drug_name, top_n=5):
        """اقتراح أدوية مشابهة عند عدم وجود تطابق"""
        if not self.use_fuzzy or not self.drugs_set:
            return []

        query = self.normalize(drug_name)
        if not query:
            return []

        results = process.extract(
            query,
            list(self.drugs_set),
            scorer=fuzz.ratio,
            limit=top_n
        )
        return [
            {'name': r[0], 'score': r[1]}
            for r in results
            if r[1] >= self.fuzzy_threshold
        ]

    def drug_exists(self, drug_name):
        """هل الدواء موجود في القاعدة؟"""
        return self.normalize(drug_name) in self.drugs_set

    # ============ فحص التفاعلات ============

    def check_pair(self, drug1, drug2):
        """
        فحص تفاعل زوج واحد
        يرجع dict:
        - found: True/False
        - drug1, drug2: الأسماء كما أُدخلت
        - description: وصف التفاعل (لو موجود)
        - suggestions: اقتراحات (لو الدواء غير موجود)
        """
        d1 = self.normalize(drug1)
        d2 = self.normalize(drug2)

        result = {
            'drug1': drug1,
            'drug2': drug2,
            'found': False,
            'description': None,
            'suggestions': {}
        }

        # فحص وجود الدواءين
        if d1 not in self.drugs_set:
            result['suggestions']['drug1'] = self.suggest_similar(drug1)
        if d2 not in self.drugs_set:
            result['suggestions']['drug2'] = self.suggest_similar(drug2)

        # البحث في الفهرس
        key = tuple(sorted([d1, d2]))
        if key in self.index:
            result['found'] = True
            result['description'] = self.index[key]

        return result

    def check_multiple(self, drugs_list):
        """
        فحص كل الأزواج الممكنة من قائمة أدوية
        يرجع dict فيه:
        - interactions: list من التفاعلات المكتشفة
        - unknown_drugs: أدوية مو موجودة
        - total_pairs: عدد الأزواج المفحوصة
        """
        # تنظيف القائمة
        drugs = [d.strip() for d in drugs_list if d and str(d).strip()]

        if len(drugs) < 2:
            return {
                'interactions': [],
                'unknown_drugs': [],
                'total_pairs': 0,
                'message': 'يجب إدخال دواءين على الأقل'
            }

        interactions = []
        unknown = []

        # فحص كل زوج
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                r = self.check_pair(drugs[i], drugs[j])
                if r['found']:
                    interactions.append({
                        'drug1': drugs[i],
                        'drug2': drugs[j],
                        'description': r['description']
                    })

        # الأدوية غير المعروفة
        for d in drugs:
            if not self.drug_exists(d):
                unknown.append({
                    'name': d,
                    'suggestions': self.suggest_similar(d)
                })

        return {
            'interactions': interactions,
            'unknown_drugs': unknown,
            'total_pairs': len(drugs) * (len(drugs) - 1) // 2,
            'drugs_checked': drugs
        }

    def get_stats(self):
        """إحصائيات القاعدة"""
        return {
            'total_interactions': len(self.index),
            'unique_drugs': len(self.drugs_set),
            'fuzzy_enabled': self.use_fuzzy,
            'arabic_map_size': len(ARABIC_DRUG_MAP),
        }


# ============ اختبار سريع ============
if __name__ == '__main__':
    print('⏳ جاري تحميل القاعدة...')
    checker = InteractionChecker()
    print('✅ تم التحميل!')
    print('📊 الإحصائيات:', checker.get_stats())
    print()

    # اختبار 1: زوج معروف
    print('🔍 اختبار 1: Trioxsalen + Verteporfin')
    r = checker.check_pair('Trioxsalen', 'Verteporfin')
    print('   النتيجة:', r['found'])
    print('   الوصف:', r['description'][:100] if r['description'] else '—')
    print()

    # اختبار 2: بالعربي
    print('🔍 اختبار 2: أسبرين + وارفارين')
    r = checker.check_pair('أسبرين', 'وارفارين')
    print('   النتيجة:', r['found'])
    print('   الوصف:', r['description'][:100] if r['description'] else '—')
    print()

    # اختبار 3: دواء غير موجود + اقتراحات
    print('🔍 اختبار 3: Aspirin + UnknownDrug')
    r = checker.check_pair('Aspirin', 'UnknownDrug')
    print('   النتيجة:', r['found'])
    print('   اقتراحات لـ UnknownDrug:', r['suggestions'].get('drug2', []))
    print()

    # اختبار 4: قائمة متعددة
    print('🔍 اختبار 4: فحص 3 أدوية معاً')
    r = checker.check_multiple(['Aspirin', 'Warfarin', 'Ibuprofen'])
    print('   عدد الأزواج:', r['total_pairs'])
    print('   تفاعلات:', len(r['interactions']))
    for inter in r['interactions']:
        print(f"   ⚠️ {inter['drug1']} + {inter['drug2']}: {inter['description'][:80]}...")