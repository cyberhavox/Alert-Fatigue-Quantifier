"""Model validation module for the predictive machine learning model.

Provides functions to perform train-test splits and cross-validation, logging
key performance metrics (accuracy, precision, recall, and F1 score) to ensure
model generalizability and prevent data leakage.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, make_scorer
from sklearn.ensemble import RandomForestClassifier

# Configure logging
logger = logging.getLogger("AFQ.Prediction.Validator")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def validate_model_performance(
    model: RandomForestClassifier,
    X: pd.DataFrame,
    y: pd.Series
) -> dict[str, float]:
    """Evaluates the Random Forest model using a 70/30 split and 5-fold cross-validation.

    Computes and logs accuracy, precision, recall, and F1 scores. Ensures no data
    leakage occurs.

    Args:
        model: An untrained or trained RandomForestClassifier template.
        X: Feature matrix.
        y: Target binary risk series.

    Returns:
        A dictionary containing performance metrics for both the 70/30 split and cross-validation.
    """
    # 1. 70/30 Train-Test Split
    # Stratify split to preserve class distributions if both classes exist
    stratify_target = y if len(np.unique(y)) > 1 else None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.30,
        random_state=42,
        stratify=stratify_target
    )

    # Instantiate a clean clone of the model config for split evaluation
    split_model = RandomForestClassifier(
        n_estimators=model.n_estimators,
        max_depth=model.max_depth,
        min_samples_split=model.min_samples_split,
        min_samples_leaf=model.min_samples_leaf,
        random_state=model.random_state,
        class_weight=model.class_weight
    )
    
    split_model.fit(X_train, y_train)
    y_pred = split_model.predict(X_test)

    # Handle edge case where precision/recall are undefined (e.g. no positive predictions)
    # by setting zero_division=0.0
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0.0))
    recall = float(recall_score(y_test, y_pred, zero_division=0.0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0.0))

    logger.info("--- 70/30 Split Validation Metrics ---")
    logger.info(f"Accuracy:  {accuracy:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall:    {recall:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")

    # 2. 5-Fold Stratified Cross-Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Configure custom scorers with zero_division=0.0 to prevent UndefinedMetricWarning
    precision_scorer = make_scorer(precision_score, zero_division=0.0)
    recall_scorer = make_scorer(recall_score, zero_division=0.0)
    f1_scorer = make_scorer(f1_score, zero_division=0.0)
    
    scoring_metrics = {
        "accuracy": "accuracy",
        "precision": precision_scorer,
        "recall": recall_scorer,
        "f1": f1_scorer
    }
    
    cv_model = RandomForestClassifier(
        n_estimators=model.n_estimators,
        max_depth=model.max_depth,
        min_samples_split=model.min_samples_split,
        min_samples_leaf=model.min_samples_leaf,
        random_state=model.random_state,
        class_weight=model.class_weight
    )

    # Run CV on whole dataset (cross_validate takes care of splitting internally to prevent leakage)
    cv_results = cross_validate(
        cv_model, X, y,
        cv=cv,
        scoring=scoring_metrics,
        error_score="raise"
    )

    cv_accuracy = float(np.mean(cv_results["test_accuracy"]))
    cv_precision = float(np.mean(cv_results["test_precision"]))
    cv_recall = float(np.mean(cv_results["test_recall"]))
    cv_f1 = float(np.mean(cv_results["test_f1"]))

    logger.info("--- 5-Fold Cross Validation Metrics (Mean) ---")
    logger.info(f"CV Accuracy:  {cv_accuracy:.4f}")
    logger.info(f"CV Precision: {cv_precision:.4f}")
    logger.info(f"CV Recall:    {cv_recall:.4f}")
    logger.info(f"CV F1 Score:  {cv_f1:.4f}")

    metrics = {
        "split_accuracy": accuracy,
        "split_precision": precision,
        "split_recall": recall,
        "split_f1": f1,
        "cv_mean_accuracy": cv_accuracy,
        "cv_mean_precision": cv_precision,
        "cv_mean_recall": cv_recall,
        "cv_mean_f1": cv_f1
    }

    return metrics
