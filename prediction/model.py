"""Machine learning model management for predicting analyst fatigue risks.

Handles training, prediction, serialization, and deserialization of the
Random Forest Classifier.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def train_predictive_model(
    features: pd.DataFrame,
    labels: pd.Series
) -> RandomForestClassifier:
    """Trains a Random Forest Classifier to predict fatigue risk.

    Args:
        features: Feature matrix containing signals, time features, and lags.
        labels: Target series containing binary fatigue risk labels.

    Returns:
        The trained RandomForestClassifier instance.
    """
    # Initialize Random Forest with regularized parameters to prevent overfitting
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced"
    )
    
    model.fit(features, labels)
    return model


def predict_fatigue_risk(
    model: RandomForestClassifier,
    X: pd.DataFrame
) -> np.ndarray:
    """Generates fatigue risk predictions for the given feature matrix.

    Args:
        model: The trained RandomForestClassifier instance.
        X: Feature matrix of observations.

    Returns:
        A 1D numpy array of binary predictions (0 or 1).
    """
    return model.predict(X)


def save_model(model: RandomForestClassifier, filepath: str) -> None:
    """Serializes and saves the trained model to a pickle file.

    Args:
        model: The trained RandomForestClassifier instance.
        filepath: Absolute or relative target file path.
    """
    dir_path = os.path.dirname(filepath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        
    with open(filepath, "wb") as f:
        pickle.dump(model, f)


def load_model(filepath: str) -> RandomForestClassifier:
    """Loads a serialized model from a pickle file.

    Args:
        filepath: Absolute or relative source file path.

    Returns:
        The loaded RandomForestClassifier instance.

    Raises:
        FileNotFoundError: If the model file is not found at the path.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found at: {filepath}")
        
    with open(filepath, "rb") as f:
        model = pickle.load(f)
        
    return model
