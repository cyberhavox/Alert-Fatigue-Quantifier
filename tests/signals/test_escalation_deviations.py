"""Unit tests for the escalation deviations signal calculator.
"""

import pandas as pd
from signals.escalation_deviations import calculate_escalation_deviations


def test_calculate_escalation_deviations_correctness(mock_raw_data) -> None:
    """Verifies that escalation deviations are calculated correctly."""
    df = mock_raw_data.copy()
    
    deviations = calculate_escalation_deviations(df)
    
    assert isinstance(deviations, pd.Series)
    assert len(deviations) == len(df)
    assert deviations.index.equals(df.index)


def test_calculate_escalation_deviations_empty_df() -> None:
    """Asserts that the calculator handles an empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        "analyst_id", "triage_timestamp", "closure_timestamp", "escalation_flag"
    ])
    res = calculate_escalation_deviations(empty_df)
    assert len(res) == 0
