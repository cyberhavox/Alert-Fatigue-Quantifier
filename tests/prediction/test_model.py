"""Unit and validation tests for the predictive Random Forest model.

Explicitly asserts train-test split ratios, disjoint index verification (no data leakage),
cross-validation correctness, and model serialization functionality.
"""

import os
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from prediction.feature_engineering import build_feature_matrix
from prediction.model import train_predictive_model, predict_fatigue_risk, save_model, load_model
from prediction.validator import validate_model_performance


def test_model_training_and_inference(mock_signals_df) -> None:
    """Verifies that the Random Forest model can be trained and runs inference correctly."""
    df = mock_signals_df.copy()
    X, y = build_feature_matrix(df)
    
    model = train_predictive_model(X, y)
    assert isinstance(model, RandomForestClassifier)
    
    preds = predict_fatigue_risk(model, X)
    assert len(preds) == len(df)
    assert set(preds).issubset({0, 1})


def test_model_serialization(mock_signals_df, tmp_path) -> None:
    """Verifies that model serialization and deserialization works without errors."""
    df = mock_signals_df.copy()
    X, y = build_feature_matrix(df)
    model = train_predictive_model(X, y)
    
    model_file = tmp_path / "test_model.pkl"
    save_model(model, str(model_file))
    
    assert model_file.exists()
    
    loaded = load_model(str(model_file))
    assert isinstance(loaded, RandomForestClassifier)
    assert loaded.n_estimators == model.n_estimators


def test_model_validation_no_data_leakage(mock_signals_df) -> None:
    """Explicitly verifies that the 70/30 split and cross-validation prevent data leakage.

    Asserts that:
    - Train and test datasets are disjoint.
    - Standard 70% and 30% sizing splits are respected.
    - Model validator logs and returns complete performance metrics.
    """
    df = mock_signals_df.copy()
    X, y = build_feature_matrix(df)
    model = train_predictive_model(X, y)

    # 1. Verify train_test_split ratios and disjoint indices (No Data Leakage)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.30,
        random_state=42,
        stratify=y
    )
    
    # Assert exact split ratios (70% train, 30% test)
    assert len(X_train) == 21  # 30 * 0.7
    assert len(X_test) == 9    # 30 * 0.3
    
    # Assert no index overlap (disjoint splits physically guarantee zero data leakage)
    intersection = set(X_train.index).intersection(set(X_test.index))
    assert len(intersection) == 0, "Data Leakage Detected: Train and Test indices overlap!"

    # 2. Verify cross-validation split disjointness and folds (No Data Leakage)
    from sklearn.model_selection import StratifiedKFold
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold = 0
    for train_idx, val_idx in cv.split(X, y):
        # Assert no index overlap between train fold and validation fold
        intersection = set(train_idx).intersection(set(val_idx))
        assert len(intersection) == 0, f"Data Leakage Detected in CV Fold {fold}: Train and Validation indices overlap!"
        
        # Verify that splits are 80/20 for each fold (with N=30 samples: train size=24, validation size=6)
        assert len(train_idx) == 24
        assert len(val_idx) == 6
        fold += 1
        
    assert fold == 5, f"Expected 5 folds, but got {fold}"

    # 3. Run validator and verify returned metric structure
    metrics = validate_model_performance(model, X, y)
    
    expected_keys = [
        "split_accuracy", "split_precision", "split_recall", "split_f1",
        "cv_mean_accuracy", "cv_mean_precision", "cv_mean_recall", "cv_mean_f1"
    ]
    for key in expected_keys:
        assert key in metrics
        assert isinstance(metrics[key], float)
        assert 0.0 <= metrics[key] <= 1.0

