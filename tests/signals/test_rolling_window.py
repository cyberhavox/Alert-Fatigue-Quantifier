"""Unit tests for the rolling window preparation utility.
"""

import pandas as pd
from signals.rolling_window import prepare_rolling_dataframe


def test_prepare_rolling_dataframe_sorting() -> None:
    """Verifies that the preparation function sorts records chronologically."""
    df = pd.DataFrame({
        "closure_timestamp": [
            "2026-06-20T10:10:00Z",
            "2026-06-20T10:00:00Z",
            "2026-06-20T10:05:00Z"
        ],
        "triage_timestamp": [
            "2026-06-20T10:09:00Z",
            "2026-06-20T09:59:00Z",
            "2026-06-20T10:04:00Z"
        ]
    })
    
    prepared_df = prepare_rolling_dataframe(df)
    
    # Assert sorted order
    assert prepared_df.iloc[0]["closure_timestamp"] == "2026-06-20T10:00:00Z"
    assert prepared_df.iloc[1]["closure_timestamp"] == "2026-06-20T10:05:00Z"
    assert prepared_df.iloc[2]["closure_timestamp"] == "2026-06-20T10:10:00Z"
    assert "closure_timestamp_dt" in prepared_df.columns
