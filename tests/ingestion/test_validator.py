"""Unit tests for the log schema validator module.
"""

import pytest
import pandas as pd
from ingestion.validator import validate_log_schema


def test_validate_log_schema_valid(mock_raw_data) -> None:
    """Verifies that a valid DataFrame passes validation checks."""
    df = mock_raw_data.copy()
    # Add datetime columns created by parser to mock full ingestion pipeline state
    df["triage_timestamp_dt"] = pd.to_datetime(df["triage_timestamp"])
    df["closure_timestamp_dt"] = pd.to_datetime(df["closure_timestamp"])

    assert validate_log_schema(df) is True


def test_validate_log_schema_missing_columns(mock_raw_data) -> None:
    """Asserts that schema validation raises ValueError when required columns are missing."""
    df_missing = mock_raw_data.drop(columns=["analyst_id"])
    with pytest.raises(ValueError, match="Ingested logs missing required columns"):
        validate_log_schema(df_missing)


def test_validate_log_schema_invalid_types(mock_raw_data) -> None:
    """Asserts that schema validation raises ValueError when columns have incorrect types."""
    df_invalid = mock_raw_data.copy()
    # Change enrichment actions from int to string representation
    df_invalid["enrichment_actions"] = "five"
    with pytest.raises(ValueError, match="Column 'enrichment_actions' contains non-integer values"):
        validate_log_schema(df_invalid)


def test_validate_log_schema_negative_values(mock_raw_data) -> None:
    """Asserts that validation raises ValueError when numeric fields have negative values."""
    df_negative = mock_raw_data.copy()
    df_negative.loc[0, "enrichment_actions"] = -1
    with pytest.raises(ValueError, match="Column 'enrichment_actions' contains negative counts"):
        validate_log_schema(df_negative)


def test_validate_log_schema_fills_null_notes(mock_raw_data) -> None:
    """Verifies that validation fills missing notes fields with empty strings."""
    df_null_notes = mock_raw_data.copy()
    # Inject a null value in notes column
    df_null_notes.loc[0, "notes"] = None
    
    validate_log_schema(df_null_notes)
    
    # Assert it was filled with empty string
    assert df_null_notes.loc[0, "notes"] == ""
