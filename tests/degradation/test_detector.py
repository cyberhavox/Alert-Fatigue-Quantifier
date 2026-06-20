"""Unit tests for the degradation detector module.
"""

import pandas as pd
from degradation.detector import detect_degradation_anomalies


def test_detect_degradation_anomalies_correctness(mock_raw_data, mock_baseline_data) -> None:
    """Verifies that the degradation detector runs and outputs correct schema."""
    df = mock_raw_data.copy()
    
    # Run detector
    anomalies_df = detect_degradation_anomalies(df, mock_baseline_data)
    
    assert isinstance(anomalies_df, pd.DataFrame)
    
    # Assert output schema columns
    expected_cols = ["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]
    for col in expected_cols:
        assert col in anomalies_df.columns
        
    # Valid anomalies should have a p-value < 0.05
    if not anomalies_df.empty:
        assert (anomalies_df["p-value"] < 0.05).all()
        assert (anomalies_df["State"].isin(["ELEVATED", "HIGH", "CRITICAL"])).all()
