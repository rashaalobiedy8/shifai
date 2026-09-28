"""
تحميل البيانات من الملفات
"""
import pandas as pd
from pathlib import Path
from . import config


def load_drug_data() -> pd.DataFrame:
    """تحميل بيانات drug200 للتدريب"""
    if not config.DRUG_DATA_FILE.exists():
        raise FileNotFoundError(
            f"ملف بيانات الأدوية غير موجود: {config.DRUG_DATA_FILE}\n"
            f"تأكد من وجود الملف في: {config.RAW_DATA_DIR}"
        )
    
    df = pd.read_excel(config.DRUG_DATA_FILE)
    print(f"✅ تم تحميل drug200: {df.shape[0]} صف، {df.shape[1]} عمود")
    return df


def load_interactions() -> pd.DataFrame:
    """تحميل قاعدة التفاعلات الدوائية"""
    if not config.INTERACTIONS_FILE.exists():
        print(f"⚠️ ملف التفاعلات غير موجود: {config.INTERACTIONS_FILE}")
        return None
    
    df = pd.read_excel(config.INTERACTIONS_FILE)
    print(f"✅ تم تحميل التفاعلات: {df.shape[0]} صف")
    return df


def load_pk_ddi() -> pd.DataFrame:
    """تحميل قاعدة PK-DDI"""
    if not config.PK_DDI_FILE.exists():
        print(f"⚠️ ملف PK-DDI غير موجود: {config.PK_DDI_FILE}")
        return None
    
    df = pd.read_excel(config.PK_DDI_FILE)
    print(f"✅ تم تحميل PK-DDI: {df.shape[0]} صف")
    return df


def load_qa_data() -> pd.DataFrame:
    """تحميل بيانات الأسئلة الطبية"""
    if not config.QA_DATA_FILE.exists():
        print(f"⚠️ ملف الأسئلة غير موجود: {config.QA_DATA_FILE}")
        return None
    
    # نجرب CSV أولاً
    if config.QA_DATA_FILE.suffix == '.csv':
        df = pd.read_csv(config.QA_DATA_FILE)
    else:
        df = pd.read_excel(config.QA_DATA_FILE)
    
    print(f"✅ تم تحميل الأسئلة: {df.shape[0]} صف")
    return df