"""Log parsing utilities for the Alert Fatigue Quantifier.

This module provides functions to parse raw CSV or JSON files containing SOC
analyst log data and load them into standardized pandas DataFrames.
"""

import os
import pandas as pd


def parse_log_file(file_path: str) -> pd.DataFrame:
    """Parses a log file (CSV or JSON) and returns a standard pandas DataFrame.

    Args:
        file_path: The absolute or relative path to the target log file.

    Returns:
        A pandas DataFrame containing the parsed log records.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file extension is unsupported or if parsing fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Log file not found at: {file_path}")

    _, ext = os.path.splitext(file_path.lower())

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Only CSV and JSON are permitted.")
    except Exception as exc:
        raise ValueError(f"Failed to parse log file: {exc}") from exc

    return df
