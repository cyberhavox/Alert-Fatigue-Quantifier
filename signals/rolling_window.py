"""Shared rolling window utility for the signals engine.

This module provides utility functions to standardize DataFrame preprocessing
(sorting, datetime conversions) for rolling time-based computations.
"""

import pandas as pd


def prepare_rolling_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares and standardizes the DataFrame for rolling window analysis.

    Converts raw timestamp string columns to datetime objects and sorts the
    records chronologically by closure timestamp to prepare for pandas rolling
    operations.

    Args:
        df: Input log DataFrame.

    Returns:
        A copy of the input DataFrame sorted chronologically by closure time.
    """
    df_sorted = df.copy()
    df_sorted["triage_timestamp_dt"] = pd.to_datetime(df_sorted["triage_timestamp"])
    df_sorted["closure_timestamp_dt"] = pd.to_datetime(df_sorted["closure_timestamp"])
    return df_sorted.sort_values(by="closure_timestamp_dt")
