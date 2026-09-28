"""
إعدادات المشروع العامة
"""
from pathlib import Path

# المسارات الأساسية
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
MODELS_DIR = PROJECT_ROOT / 'models'

# مسارات الملفات
DRUG_DATA_FILE = RAW_DATA_DIR / 'drug200 (2).xlsx'
INTERACTIONS_FILE = RAW_DATA_DIR / 'db_drug_interactions.xlsx'
PK_DDI_FILE = RAW_DATA_DIR / 'PK-DDI DB.xlsx'
QA_DATA_FILE = RAW_DATA_DIR / 'AHD_english_small.csv'
MODEL_FILE = MODELS_DIR / 'drug_prediction_model.pkl'

# معلومات النموذج
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# قاموس أسماء الأدوية (للعرض)
DRUG_MAPPING = {
    'DrugY': 'مجموعة Y (دواء متعدد الاستخدامات)',
    'drugX': 'مجموعة X (مضاد حيوي)',
    'drugA': 'مجموعة A (خافض ضغط)',
    'drugB': 'مجموعة B (منظم سكر)',
    'drugC': 'مجموعة C (لعلاج الكوليسترول)',
}

# إخلاء المسؤولية
DISCLAIMER = (
    "⚠️ هذا النموذج تجريبي لأغراض العرض فقط، "
    "ولا يُستخدم للتشخيص أو العلاج الفعلي. "
    "يجب استشارة طبيب مختص."
)