"""Uninvestigated Closures signal calculator for the Alert Fatigue Quantifier.

Computes the rolling count of alerts resolved as dismissed without any enrichment
actions taken or text notes recorded.
"""

import pandas as pd
from signals.rolling_window import prepare_rolling_dataframe


def calculate_uninvestigated_closures(df: pd.DataFrame, window_minutes: int = 60) -> pd.Series:
    """Calculates the rolling count of uninvestigated alert closures.

    Args:
        df: Input log DataFrame.
        window_minutes: Window size in minutes. Defaults to 60.

    Returns:
        A pandas Series of integer counts, aligned with the original DataFrame index.
    """
    df_sorted = prepare_rolling_dataframe(df)

    # Shortcut criteria: dismissed, zero enrichment, and empty notes
    df_sorted["_is_shortcut"] = (
        (df_sorted["closure_type"] == "dismissed") &
        (df_sorted["enrichment_actions"] == 0) &
        ((df_sorted["notes"].isnull()) | (df_sorted["notes"].str.strip() == ""))
    ).astype(int)

    results = []
    for _, group in df_sorted.groupby("analyst_id"):
        group_indexed = group.set_index("closure_timestamp_dt")
        rolling_val = group_indexed["_is_shortcut"].rolling(f"{window_minutes}min").sum()
        rolling_val.index = group.index
        results.append(rolling_val)

    if not results:
        return pd.Series(0, index=df.index).astype(int)

    return pd.concat(results).reindex(df.index).fillna(0).astype(int)
