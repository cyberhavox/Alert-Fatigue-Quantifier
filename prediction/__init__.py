"""Machine learning prediction module for the Alert Fatigue Quantifier.

This package provides feature engineering, model training, validation, and inference
methods to forecast upcoming analyst fatigue risks.
"""

from prediction.feature_engineering import build_feature_matrix
from prediction.model import train_predictive_model, predict_fatigue_risk, save_model, load_model
from prediction.validator import validate_model_performance

__all__ = [
    "build_feature_matrix",
    "train_predictive_model",
    "predict_fatigue_risk",
    "save_model",
    "load_model",
    "validate_model_performance",
]
