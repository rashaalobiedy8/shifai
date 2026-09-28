"""
تدريب نموذج التنبؤ بالدواء
"""
import pickle
import json
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix
)

from . import config
from .data_loader import load_drug_data
from .preprocess import prepare_training_data


def train(random_state=None):
    """تدريب النموذج وحفظه"""
    random_state = random_state or config.RANDOM_STATE
    
    print("=" * 60)
    print("🚀 بدء تدريب نموذج التنبؤ بالدواء")
    print("=" * 60)
    
    # 1. تحميل البيانات
    df = load_drug_data()
    
    # 2. تجهيز البيانات
    X, y, encoders = prepare_training_data(df)
    
    # 3. تقسيم البيانات (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config.TEST_SIZE,
        random_state=random_state,
        stratify=y,   # مهم: يحافظ على توزيع الفئات
    )
    print(f"\n📊 تقسيم البيانات:")
    print(f"  - تدريب: {len(X_train)} صف")
    print(f"  - اختبار: {len(X_test)} صف")
    
    # 4. إنشاء النموذج
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,              # نقلل لمنع overfitting
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=random_state,
        class_weight='balanced',  # يراعي عدم توازن الفئات
    )
    
    # 5. التدريب
    print(f"\n🏋️ جاري التدريب...")
    model.fit(X_train, y_train)
    
    # 6. التقييم على بيانات الاختبار
    y_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ دقة الاختبار: {test_accuracy * 100:.2f}%")
    print(f"\n📋 تقرير التصنيف:")
    print(classification_report(
        y_test, y_pred,
        target_names=encoders['le_drug'].classes_,
        zero_division=0,
    ))
    
    # 7. التحقق المتقاطع (الدقة الحقيقية)
    print(f"\n🔄 التحقق المتقاطع ({config.CV_FOLDS} folds)...")
    cv = StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
    
    print(f"  - الدقة: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    print(f"  - النتائج: {[f'{s*100:.1f}%' for s in cv_scores]}")
    
    # 8. تجهيز الحزمة للحفظ
    package = {
        'model': model,
        'le_sex': encoders['le_sex'],
        'le_bp': encoders['le_bp'],
        'le_cholesterol': encoders['le_cholesterol'],
        'le_drug': encoders['le_drug'],
        'metadata': {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': X.shape[1],
            'feature_names': X.columns.tolist(),
            'test_accuracy': float(test_accuracy),
            'cv_accuracy_mean': float(cv_scores.mean()),
            'cv_accuracy_std': float(cv_scores.std()),
            'drug_classes': encoders['le_drug'].classes_.tolist(),
            'drug_mapping': config.DRUG_MAPPING,
            'disclaimer': config.DISCLAIMER,
        },
    }
    
    # 9. الحفظ
    config.MODELS_DIR.mkdir(exist_ok=True)
    with open(config.MODEL_FILE, 'wb') as f:
        pickle.dump(package, f)
    
    print(f"\n💾 تم حفظ النموذج: {config.MODEL_FILE}")
    
    # 10. حفظ metadata منفصلة (للعرض)
    metadata_file = config.MODELS_DIR / 'model_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(package['metadata'], f, ensure_ascii=False, indent=2)
    
    print(f"📄 تم حفظ البيانات الوصفية: {metadata_file}")
    print("\n" + "=" * 60)
    print("✅ اكتمل التدريب بنجاح!")
    print("=" * 60)
    
    return package


if __name__ == '__main__':
    train()