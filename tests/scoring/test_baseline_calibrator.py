"""Unit tests for the historical baseline calibrator.

Verifies baseline calculation correctness and profile serialization using mock patches
to write to temporary testing directories.
"""

import os
import pytest
from unittest.mock import patch
from scoring.baseline_calibrator import build_and_save_baselines, load_baseline


def test_build_and_save_baselines_correctness(mock_raw_data, tmp_path) -> None:
    """Verifies baseline parameter calculations and JSON serialization."""
    df = mock_raw_data.copy()
    
    # Path settings to write baseline file to tmp_path instead of data/baseline/
    with patch("scoring.baseline_calibrator.PATH_BASELINE_LOGS", str(tmp_path)):
        build_and_save_baselines(df)
        
        # Verify baseline file exists for ANALYST_01
        expected_file = tmp_path / "baseline_ANALYST_01.json"
        assert expected_file.exists()
        
        # Load baseline back and verify parameters
        profile = load_baseline("ANALYST_01")
        assert profile["analyst_id"] == "ANALYST_01"
        assert "mean_triage_interval" in profile
        assert "std_triage_interval" in profile
        assert "mean_enrichment_depth" in profile
        assert "std_enrichment_depth" in profile
        assert profile["mean_triage_interval"] > 0.0


def test_load_baseline_missing_raises_error(tmp_path) -> None:
    """Asserts that load_baseline raises FileNotFoundError for non-existent profiles."""
    with patch("scoring.baseline_calibrator.PATH_BASELINE_LOGS", str(tmp_path)):
        with pytest.raises(FileNotFoundError, match="No baseline profile found"):
            load_baseline("NON_EXISTENT_ANALYST")
