"""Schema and boundary validation utilities for the Ingestion module.

This module validates that ingested pandas DataFrames conform to the required
10-field schema, checking value ranges, data types, and null constraints.
"""

import pandas as pd


def validate_log_schema(df: pd.DataFrame) -> bool:
    """Validates that a DataFrame conforms to the 10-field synthetic data schema.

    Args:
        df: The pandas DataFrame to validate.

    Returns:
        True if the schema and all constraints are valid.

    Raises:
        ValueError: If any validation checks fail (e.g., missing columns,
            invalid types, or values outside permitted ranges).
    """
    required_schema = {
        "analyst_id": "object",
        "alert_id": "object",
        "triage_timestamp": "object",
        "closure_timestamp": "object",
        "closure_type": "object",
        "severity_assigned": "object",
        "severity_verified": "object",
        "enrichment_actions": "int64",
        "escalation_flag": "bool",
        "notes": "object",
    }

    # 1. Verify all required columns are present
    missing_cols = [col for col in required_schema if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Ingested logs missing required columns: {missing_cols}")

    # 2. Check and coerce types where safe, or raise type errors
    # enrichment_actions: coerce to numeric first, check if integer
    try:
        df["enrichment_actions"] = df["enrichment_actions"].astype("int64")
    except Exception as exc:
        raise ValueError(f"Column 'enrichment_actions' contains non-integer values: {exc}") from exc

    # escalation_flag: coerce to bool
    try:
        df["escalation_flag"] = df["escalation_flag"].astype("bool")
    except Exception as exc:
        raise ValueError(f"Column 'escalation_flag' contains non-boolean values: {exc}") from exc

    # 3. Check for non-null requirements (all columns except 'notes')
    critical_cols = [col for col in required_schema if col != "notes"]
    for col in critical_cols:
        if df[col].isnull().any():
            raise ValueError(f"Required column '{col}' contains null values.")

    # 4. Fill null notes with empty string
    df["notes"] = df["notes"].fillna("")

    # 5. Validate categorical value ranges
    valid_closure_types = {"dismissed", "investigated", "escalated"}
    invalid_closures = set(df["closure_type"].unique()) - valid_closure_types
    if invalid_closures:
        raise ValueError(f"Invalid closure types detected: {invalid_closures}")

    valid_severities = {"low", "medium", "high", "critical"}
    invalid_assigned_sevs = set(df["severity_assigned"].unique()) - valid_severities
    if invalid_assigned_sevs:
        raise ValueError(f"Invalid severity_assigned detected: {invalid_assigned_sevs}")

    invalid_verified_sevs = set(df["severity_verified"].unique()) - valid_severities
    if invalid_verified_sevs:
        raise ValueError(f"Invalid severity_verified detected: {invalid_verified_sevs}")

    # 6. Validate value ranges
    if (df["enrichment_actions"] < 0).any():
        raise ValueError("Column 'enrichment_actions' contains negative counts.")

    # 7. Validate datetimes
    try:
        pd.to_datetime(df["triage_timestamp"], format="mixed")
        pd.to_datetime(df["closure_timestamp"], format="mixed")
    except Exception as exc:
        raise ValueError(f"Datetime formatting error in timestamp columns: {exc}") from exc

    return True
