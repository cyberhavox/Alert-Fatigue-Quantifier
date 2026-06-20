"""Unit tests for the predictive modeling feature engineering module.
"""

import pandas as pd
from prediction.feature_engineering import build_feature_matrix


def test_build_feature_matrix_shapes(mock_signals_df) -> None:
    """Verifies that the feature matrix is constructed with correct columns and shapes."""
    df = mock_signals_df.copy()
    
    X, y = build_feature_matrix(df)
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert len(X) == len(df)
    assert len(y) == len(df)
    
    # Assert features are engineered
    expected_features = [
        "triage_interval", "uninvestigated_closures", "enrichment_depth",
        "escalation_deviations", "hourly_closure_rate", "hour_of_day",
        "afi_lag_1", "afi_lag_2"
    ]
    for feat in expected_features:
        assert feat in X.columns
        
    # Assert binary target classification labels
    assert set(y.unique()).issubset({0, 1})


def test_build_feature_matrix_threshold_labeling(mock_signals_df) -> None:
    """Verifies that targets are correctly labeled based on the AFI score > 70 rule."""
    df = mock_signals_df.copy()
    
    X, y = build_feature_matrix(df)
    
    # In mock_signals_df:
    # Rows 0-14 have AFI 45.0 (should be labeled 0)
    # Rows 15-29 have AFI 80.0 (should be labeled 1)
    # Note: build_feature_matrix sorts by analyst_id, check alignment
    sorted_df = df.copy()
    sorted_df["closure_dt"] = pd.to_datetime(sorted_df["closure_timestamp"])
    sorted_df = sorted_df.sort_values(by=["analyst_id", "closure_dt"]).reset_index(drop=True)
    
    for i, row in sorted_df.iterrows():
        expected_label = 1 if row["afi_score"] > 70.0 else 0
        assert y.iloc[i] == expected_label
