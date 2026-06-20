"""Unit tests for the enrichment depth signal calculator.
"""

import pandas as pd
from signals.enrichment_depth import calculate_enrichment_depth


def test_calculate_enrichment_depth_correctness(mock_raw_data) -> None:
    """Verifies that enrichment depth calculations are correct."""
    df = mock_raw_data.copy()
    
    depths = calculate_enrichment_depth(df)
    
    assert isinstance(depths, pd.Series)
    assert len(depths) == len(df)
    assert depths.index.equals(df.index)


def test_calculate_enrichment_depth_empty_df() -> None:
    """Asserts that the calculator handles an empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        "analyst_id", "triage_timestamp", "closure_timestamp", "enrichment_actions"
    ])
    res = calculate_enrichment_depth(empty_df)
    assert len(res) == 0
