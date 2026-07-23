"""Feature engineering module for the predictive machine learning model.

Extracts features from the scored alerts dataframe (signals, time components, and lag values)
and constructs target labels representing elevated/critical fatigue risk.
"""

import pandas as pd
import numpy as np


def build_feature_matrix(
    scored_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.Series]:
    """Constructs the feature matrix and target labels for the fatigue risk classifier.

    Features engineered:
    - Current rolling signals (triage interval, uninvestigated closures, etc.)
    - Hour of day (from closure timestamp)
    - Lagged AFI values (AFI at t-1 and t-2 to capture fatigue build-up)

    Target:
    - Binary flag representing whether the analyst's AFI is above the fatigue risk threshold (AFI > 70).

    Args:
        scored_df: DataFrame containing computed rolling signals and AFI scores.

    Returns:
        A tuple of (features_df, target_series).
    """
    df_sorted = scored_df.copy()
    
    # 1. Parse timestamps and sort to ensure chronological order per analyst
    df_sorted["closure_dt"] = pd.to_datetime(df_sorted["closure_timestamp"])
    df_sorted = df_sorted.sort_values(by=["analyst_id", "closure_dt"])

    # 2. Engineer time features
    df_sorted["hour_of_day"] = df_sorted["closure_dt"].dt.hour

    # 3. Engineer lag features of AFI score to capture fatigue accumulation
    # Fill first records for each analyst with nominal AFI (e.g., 50.0)
    df_sorted["afi_lag_1"] = (
        df_sorted.groupby("analyst_id")["afi_score"]
        .shift(1)
        .fillna(50.0)
    )
    df_sorted["afi_lag_2"] = (
        df_sorted.groupby("analyst_id")["afi_score"]
        .shift(2)
        .fillna(50.0)
    )

    # 4. Define feature columns
    feature_cols = [
        "triage_interval",
        "uninvestigated_closures",
        "enrichment_depth",
        "escalation_deviations",
        "hourly_closure_rate",
        "automation_bias_index",
        "context_switch_count",
        "hour_of_day",
        "afi_lag_1",
        "afi_lag_2"
    ]

    features = df_sorted[feature_cols].copy()
    
    # Target label: 1 if AFI score > 70.0 (high or critical fatigue), else 0
    # Threshold 70.0 corresponds to the high fatigue band boundary (from settings.py THRESHOLD_ELEVATED_MAX)
    target = (df_sorted["afi_score"] > 70.0).astype(int)

    return features, target
