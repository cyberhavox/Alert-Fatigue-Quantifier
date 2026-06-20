"""Unit tests for the Analyst Fatigue Index (AFI) calculator module.
"""

import pandas as pd
import numpy as np
from scoring.afi_calculator import calculate_analyst_afi


def test_calculate_analyst_afi_correctness(mock_signals_df, mock_baseline_data) -> None:
    """Verifies that the composite AFI scores are calculated correctly per analyst."""
    df = mock_signals_df.copy()
    
    scored_df = calculate_analyst_afi(df, mock_baseline_data)
    
    # Assert columns added
    assert "afi_score" in scored_df.columns
    assert len(scored_df) == len(df)
    
    # AFI scores must be bounded in [0, 100]
    assert scored_df["afi_score"].min() >= 0.0
    assert scored_df["afi_score"].max() <= 100.0

    # Under nominal conditions (ANALYST_01), AFI should be lower than under fatigued conditions (ANALYST_02)
    nominal_afi_mean = scored_df[scored_df["analyst_id"] == "ANALYST_01"]["afi_score"].mean()
    fatigued_afi_mean = scored_df[scored_df["analyst_id"] == "ANALYST_02"]["afi_score"].mean()
    
    assert fatigued_afi_mean > nominal_afi_mean + 15.0
