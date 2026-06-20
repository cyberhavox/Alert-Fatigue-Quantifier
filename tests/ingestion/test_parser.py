"""Unit tests for the log ingestion parser module.
"""

import os
import pytest
import pandas as pd
from ingestion.parser import parse_log_file


def test_parse_log_file_valid_csv(tmp_path) -> None:
    """Verifies that a valid CSV file is parsed correctly with appropriate types."""
    # Create a temporary CSV file
    csv_file = tmp_path / "valid_logs.csv"
    csv_content = (
        "analyst_id,alert_id,triage_timestamp,closure_timestamp,closure_type,"
        "severity_assigned,severity_verified,enrichment_actions,escalation_flag,notes\n"
        "ANALYST_01,ALERT_000001,2026-06-20T10:00:00Z,2026-06-20T10:05:00Z,dismissed,"
        "medium,medium,5,False,Some investigation notes\n"
    )
    csv_file.write_text(csv_content)

    # Parse file
    df = parse_log_file(str(csv_file))

    # Assert schema and parsing results
    assert len(df) == 1
    assert df.loc[0, "analyst_id"] == "ANALYST_01"
    assert df.loc[0, "alert_id"] == "ALERT_000001"
    assert df.loc[0, "enrichment_actions"] == 5
    assert df.loc[0, "escalation_flag"] == False
    assert df.loc[0, "notes"] == "Some investigation notes"


def test_parse_log_file_unsupported_format(tmp_path) -> None:
    """Asserts that parsing raises ValueError for unsupported file extensions."""
    unsupported_file = tmp_path / "logs.xml"
    unsupported_file.write_text("<xml>dummy</xml>")

    with pytest.raises(ValueError, match="Failed to parse log file"):
        parse_log_file(str(unsupported_file))
