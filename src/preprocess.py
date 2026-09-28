"""
معالجة وتنظيف البيانات
"""
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from . import config


def prepare_training_data(df: pd.DataFrame):
    """
    تجهيز بيانات التدريب
    
    Returns:
        X, y, encoders
    """
    df = df.copy()
    
    # التحقق من الأعمدة
    required_cols = ['Age', 'Sex', 'BP', 'Cholesterol', 'Na_to_K', 'Drug']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"أعمدة مفقودة: {missing}")
    
    # إنشاء Label Encoders
    le_sex = LabelEncoder()
    le_bp = LabelEncoder()
    le_cholesterol = LabelEncoder()
    le_drug = LabelEncoder()
    
    # تحويل المتغيرات الفئوية
    df['Sex_encoded'] = le_sex.fit_transform(df['Sex'])
    df['BP_encoded'] = le_bp.fit_transform(df['BP'])
    df['Cholesterol_encoded'] = le_cholesterol.fit_transform(df['Cholesterol'])
    df['Drug_encoded'] = le_drug.fit_transform(df['Drug'])
    
    # المتغيرات المستقلة والتابعة
    feature_cols = ['Age', 'Sex_encoded', 'BP_encoded', 'Cholesterol_encoded', 'Na_to_K']
    X = df[feature_cols]
    y = df['Drug_encoded']
    
    encoders = {
        'le_sex': le_sex,
        'le_bp': le_bp,
        'le_cholesterol': le_cholesterol,
        'le_drug': le_drug,
    }
    
    print(f"✅ تم تجهيز البيانات: {X.shape[0]} صف، {X.shape[1]} ميزة")
    return X, y, encoders