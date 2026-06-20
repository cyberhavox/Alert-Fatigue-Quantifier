"""Unit tests for the hourly closure rate signal calculator.
"""

import pandas as pd
from signals.hourly_closure_rate import calculate_hourly_closure_rate


def test_calculate_hourly_closure_rate_correctness(mock_raw_data) -> None:
    """Verifies that hourly closure rates are calculated correctly."""
    df = mock_raw_data.copy()
    
    rates = calculate_hourly_closure_rate(df)
    
    assert isinstance(rates, pd.Series)
    assert len(rates) == len(df)
    assert rates.index.equals(df.index)


def test_calculate_hourly_closure_rate_empty_df() -> None:
    """Asserts that the calculator handles an empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        "analyst_id", "triage_timestamp", "closure_timestamp"
    ])
    res = calculate_hourly_closure_rate(empty_df)
    assert len(res) == 0
