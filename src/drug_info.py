"""
drug_info.py — البحث في قاعدة معلومات الأدوية
==============================================
يقرأ cleaned_drugs_info.xlsx ويوفر:
- get_drug_info: كل معلومات دواء
- search_by_condition: أدوية تعالج حالة معينة
- search_by_side_effect: أدوية لها أثر جانبي معين
- drug_exists: هل الدواء موجود
- suggest_similar: اقتراحات بأسماء مشابهة
- get_stats: إحصائيات القاعدة

يعتمد على interactions.py للترجمة العربية والمرادفات.
"""

from pathlib import Path
from functools import lru_cache

import pandas as pd

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# استيراد الترجمة العربية + المرادفات من interactions.py
from src.interactions import ARABIC_DRUG_MAP, DRUG_SYNONYMS


def normalize(name):
    """تطبيع اسم الدواء: strip + ترجمة عربي + lowercase + مرادفات"""
    if not name:
        return ''
    name = str(name).strip()
    if name in ARABIC_DRUG_MAP:
        name = ARABIC_DRUG_MAP[name]
    name = name.lower()
    if name in DRUG_SYNONYMS:
        name = DRUG_SYNONYMS[name]
    return name


# ============================================================
# مسار الملف
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent
DRUGS_FILE = PROJECT_ROOT / 'data' / 'raw' / 'cleaned_drugs_info.xlsx'


# ============================================================
# الكلاس الرئيسي
# ============================================================
class DrugInfoChecker:
    """بحث وتنقيب في قاعدة معلومات الأدوية"""

    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path else DRUGS_FILE
        if not self.file_path.exists():
            raise FileNotFoundError(f"❌ ملف الأدوية غير موجود: {self.file_path}")

        print("⏳ جاري تحميل قاعدة معلومات الأدوية...")
        self.df = pd.read_excel(self.file_path)
        self.df.columns = [c.strip().lower() for c in self.df.columns]

        # تنظيف أولي
        for col in ['drug_name', 'generic_name', 'medical_condition', 'brand_names', 'side_effects']:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('').astype(str).str.strip()

        # بناء الفهارس
        self._build_indexes()

        print(f"✅ تم التحميل! إجمالي: {len(self.df)} صف")

    # --------------------------------------------------------
    # بناء الفهارس
    # --------------------------------------------------------
    def _build_indexes(self):
        """فهارس للبحث السريع"""
        # 1) drug_name.lower() → صف
        self.by_drug_name = {}
        for _, row in self.df.iterrows():
            key = normalize(row['drug_name'])
            if key and key not in self.by_drug_name:
                self.by_drug_name[key] = row

        # 2) brand_name.lower() → drug_name الأصلي
        self.by_brand = {}
        for _, row in self.df.iterrows():
            brand_str = row.get('brand_names', '')
            if not brand_str:
                continue
            for brand in brand_str.split(','):
                b = brand.strip().lower()
                if b and b not in self.by_brand:
                    self.by_brand[b] = row['drug_name']

        # 3) condition.lower() → قائمة أدوية
        self.by_condition = {}
        for _, row in self.df.iterrows():
            cond = row.get('medical_condition', '').strip().lower()
            if cond:
                self.by_condition.setdefault(cond, []).append(row['drug_name'])

        # 4) كل الأسماء للـ fuzzy
        self.all_names = list(self.by_drug_name.keys()) + list(self.by_brand.keys())

    # --------------------------------------------------------
    # البحث الرئيسي
    # --------------------------------------------------------
    def _resolve_drug(self, name):
        if not name:
            return None
        key = normalize(name)

        # 1) الأولوية لـ brand_names (لو اسم تجاري معروف)
        if key in self.by_brand:
            original = self.by_brand[key]
            resolved = self.by_drug_name.get(normalize(original))
            if resolved is not None:
                return resolved

        # 2) مباشرة في drug_name
        if key in self.by_drug_name:
            return self.by_drug_name[key]

        # 3) fuzzy
        if HAS_RAPIDFUZZ and self.all_names:
            match = process.extractOne(key, self.all_names, scorer=fuzz.ratio)
            if match and match[1] >= 85:
                matched = match[0]
                # الأفضلية brand_names
                if matched in self.by_brand:
                    return self.by_drug_name.get(normalize(self.by_brand[matched]))
                if matched in self.by_drug_name:
                    return self.by_drug_name[matched]

        return None

    # --------------------------------------------------------
    # API العام
    # --------------------------------------------------------
    def drug_exists(self, name):
        """هل الدواء موجود في القاعدة؟"""
        return self._resolve_drug(name) is not None

    def get_drug_info(self, name):
        """
        يرجع dict فيه كل معلومات الدواء:
        - found, drug_name, generic_name, medical_condition,
          side_effects, brand_names
        """
        row = self._resolve_drug(name)
        if row is None:
            return {
                'found': False,
                'query': name,
                'drug_name': None,
                'generic_name': None,
                'medical_condition': None,
                'side_effects': None,
                'brand_names': [],
                'suggestions': self.suggest_similar(name)
            }

        brands = [b.strip() for b in row.get('brand_names', '').split(',') if b.strip()]
        return {
            'found': True,
            'query': name,
            'drug_name': row['drug_name'],
            'generic_name': row.get('generic_name') or row['drug_name'],
            'medical_condition': row.get('medical_condition', ''),
            'side_effects': row.get('side_effects', ''),
            'brand_names': brands,
            'suggestions': []
        }

    def search_by_condition(self, condition):
        """أدوية تعالج حالة معينة"""
        if not condition:
            return []
        key = condition.strip().lower()
        drugs = self.by_condition.get(key, [])

        # fuzzy لو مفيش نتيجة مباشرة
        if not drugs and HAS_RAPIDFUZZ and self.by_condition:
            match = process.extractOne(key, list(self.by_condition.keys()), scorer=fuzz.ratio)
            if match and match[1] >= 80:
                drugs = self.by_condition[match[0]]
        return sorted(set(drugs))

    def search_by_side_effect(self, effect, limit=20):
        """أدوية لها أثر جانبي معين (بحث نصي في side_effects)"""
        if not effect:
            return []
        key = effect.strip().lower()
        matches = self.df[
            self.df['side_effects'].str.lower().str.contains(key, na=False, regex=False)
        ]
        return matches['drug_name'].head(limit).tolist()

    def suggest_similar(self, name, limit=5, threshold=70):
        """اقتراحات أدوية مشابهة (fuzzy)"""
        if not name or not HAS_RAPIDFUZZ or not self.all_names:
            return []
        key = normalize(name)
        matches = process.extract(key, self.all_names, scorer=fuzz.ratio, limit=limit)
        return [m[0] for m in matches if m[1] >= threshold]

    def get_stats(self):
        """إحصائيات القاعدة"""
        return {
            'total_drugs': len(self.df),
            'unique_drug_names': self.df['drug_name'].nunique(),
            'unique_conditions': self.df['medical_condition'].nunique(),
            'total_brands': len(self.by_brand),
            'fuzzy_enabled': HAS_RAPIDFUZZ,
            'arabic_map_size': len(ARABIC_DRUG_MAP),
            'synonyms_size': len(DRUG_SYNONYMS),
        }


# ============================================================
# اختبارات سريعة
# ============================================================
if __name__ == "__main__":
    checker = DrugInfoChecker()

    print("\n📊 الإحصائيات:")
    for k, v in checker.get_stats().items():
        print(f"   {k}: {v}")

    # اختبار 1: دواء معروف بالإنجليزي
    print("\n🔍 اختبار 1: doxycycline")
    info = checker.get_drug_info('doxycycline')
    print(f"   موجود: {info['found']}")
    if info['found']:
        print(f"   الاسم: {info['drug_name']}")
        print(f"   الحالة: {info['medical_condition']}")
        print(f"   عدد الأسماء التجارية: {len(info['brand_names'])}")
        print(f"   أول 3 brands: {info['brand_names'][:3]}")

    # اختبار 2: اسم تجاري
    print("\n🔍 اختبار 2: Aldactone (اسم تجاري)")
    info = checker.get_drug_info('Aldactone')
    print(f"   موجود: {info['found']}")
    if info['found']:
        print(f"   الاسم العلمي: {info['drug_name']}")

    # اختبار 3: بالعربي
    print("\n🔍 اختبار 3: أسبرين (بالعربي)")
    info = checker.get_drug_info('أسبرين')
    print(f"   موجود: {info['found']}")
    if info['found']:
        print(f"   الاسم العلمي: {info['drug_name']}")

    # اختبار 4: البحث بحالة
    print("\n🔍 اختبار 4: أدوية لـ Acne")
    drugs = checker.search_by_condition('Acne')
    print(f"   عدد الأدوية: {len(drugs)}")
    print(f"   أول 5: {drugs[:5]}")

    # اختبار 5: البحث بأثر جانبي
    print("\n🔍 اختبار 5: أدوية لها 'nausea'")
    drugs = checker.search_by_side_effect('nausea', limit=5)
    print(f"   عدد: {len(drugs)}")
    print(f"   أول 5: {drugs}")

    # اختبار 6: اقتراحات
    print("\n🔍 اختبار 6: اقتراحات لـ 'doxycyclin' (خطأ إملائي)")
    print(f"   {checker.suggest_similar('doxycyclin')}")