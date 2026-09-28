"""
اختبارات النموذج
"""
import pickle
import pytest
from pathlib import Path

from src import config


def test_model_file_exists():
    """التأكد من وجود ملف النموذج"""
    assert config.MODEL_FILE.exists(), f"النموذج غير موجود: {config.MODEL_FILE}"


def test_model_loads():
    """التأكد من إمكانية تحميل النموذج"""
    with open(config.MODEL_FILE, 'rb') as f:
        package = pickle.load(f)

    assert 'model' in package
    assert 'le_sex' in package
    assert 'le_bp' in package
    assert 'le_cholesterol' in package
    assert 'le_drug' in package
    assert 'metadata' in package


def test_model_predicts():
    """التأكد من أن النموذج يتنبأ"""
    with open(config.MODEL_FILE, 'rb') as f:
        package = pickle.load(f)

    model = package['model']

    # مدخلات: Age, Sex_encoded, BP_encoded, Cholesterol_encoded, Na_to_K
    import pandas as pd
    sample = pd.DataFrame(
        [[45, 1, 2, 1, 15.0]],
        columns=['Age', 'Sex_encoded', 'BP_encoded', 'Cholesterol_encoded', 'Na_to_K']
    )
    prediction = model.predict(sample)

    assert len(prediction) == 1
    assert prediction[0] in range(len(package['le_drug'].classes_))


def test_model_metadata():
    """التأكد من البيانات الوصفية"""
    with open(config.MODEL_FILE, 'rb') as f:
        package = pickle.load(f)

    metadata = package['metadata']

    assert 'trained_at' in metadata
    assert 'test_accuracy' in metadata
    assert 'cv_accuracy_mean' in metadata
    assert 'disclaimer' in metadata

    # الدقة معقولة
    assert 0.5 < metadata['test_accuracy'] <= 1.0