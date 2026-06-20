"""Unit tests for the uninvestigated closures signal calculator.
"""

import pandas as pd
import numpy as np
from signals.uninvestigated_closures import calculate_uninvestigated_closures


def test_calculate_uninvestigated_closures_correctness(mock_raw_data) -> None:
    """Verifies that the uninvestigated closures ratio is calculated correctly."""
    df = mock_raw_data.copy()
    
    ratios = calculate_uninvestigated_closures(df)
    
    assert isinstance(ratios, pd.Series)
    assert len(ratios) == len(df)
    assert ratios.index.equals(df.index)
    
    # Values should be bounded between 0 and 1
    assert ratios.min() >= 0.0
    assert ratios.max() <= 1.0


def test_calculate_uninvestigated_closures_empty_df() -> None:
    """Asserts that the calculator handles an empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        "analyst_id", "triage_timestamp", "closure_timestamp", "closure_type", "enrichment_actions", "notes"
    ])
    res = calculate_uninvestigated_closures(empty_df)
    assert len(res) == 0
