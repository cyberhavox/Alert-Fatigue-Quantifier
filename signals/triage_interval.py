"""Triage Interval signal calculator for the Alert Fatigue Quantifier.

Computes the rolling 60-minute mean duration between alert triage assignment
and closure for each analyst.
"""

import pandas as pd
from signals.rolling_window import prepare_rolling_dataframe


def calculate_triage_interval(df: pd.DataFrame, window_minutes: int = 60) -> pd.Series:
    """Calculates the rolling mean triage interval per analyst.

    Args:
        df: Input log DataFrame.
        window_minutes: Window size in minutes. Defaults to 60.

    Returns:
        A pandas Series of float values representing mean triage interval in
        seconds, aligned with the original DataFrame index.
    """
    df_sorted = prepare_rolling_dataframe(df)

    # Calculate individual triage durations in seconds
    df_sorted["_duration"] = (
        df_sorted["closure_timestamp_dt"] - df_sorted["triage_timestamp_dt"]
    ).dt.total_seconds()

    results = []
    for _, group in df_sorted.groupby("analyst_id"):
        # Set datetime index for time-based rolling window
        group_indexed = group.set_index("closure_timestamp_dt")
        rolling_val = group_indexed["_duration"].rolling(f"{window_minutes}min").mean()
        
        # Restore the group's original non-duplicate index
        rolling_val.index = group.index
        results.append(rolling_val)

    # Combine all analyst series and align with the original input DataFrame index
    if not results:
        return pd.Series(0.0, index=df.index)

    return pd.concat(results).reindex(df.index).fillna(0.0)
