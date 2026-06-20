"""Unit tests for the triage interval signal calculator.
"""

import pandas as pd
import numpy as np
from signals.triage_interval import calculate_triage_interval


def test_calculate_triage_interval_correctness(mock_raw_data) -> None:
    """Verifies that mean triage interval is correctly calculated."""
    df = mock_raw_data.copy()
    
    triage_intervals = calculate_triage_interval(df)
    
    # Assert return type and length
    assert isinstance(triage_intervals, pd.Series)
    assert len(triage_intervals) == len(df)
    assert triage_intervals.index.equals(df.index)
    
    # In mock_raw_data, all triage intervals are set to 180 seconds.
    # Therefore, the rolling average should be 180 seconds.
    assert np.allclose(triage_intervals.values, 180.0)


def test_calculate_triage_interval_handles_empty_dataframe() -> None:
    """Asserts that the calculator handles an empty DataFrame without errors."""
    empty_df = pd.DataFrame(columns=[
        "analyst_id", "triage_timestamp", "closure_timestamp", "notes"
    ])
    res = calculate_triage_interval(empty_df)
    assert len(res) == 0
    assert isinstance(res, pd.Series)
