"""Enrichment Depth signal calculator for the Alert Fatigue Quantifier.

Computes the rolling 60-minute mean count of enrichment actions taken per alert
for each analyst.
"""

import pandas as pd
from signals.rolling_window import prepare_rolling_dataframe


def calculate_enrichment_depth(df: pd.DataFrame, window_minutes: int = 60) -> pd.Series:
    """Calculates the rolling mean enrichment actions depth per analyst.

    Args:
        df: Input log DataFrame.
        window_minutes: Window size in minutes. Defaults to 60.

    Returns:
        A pandas Series of float values representing mean enrichment actions,
        aligned with the original DataFrame index.
    """
    df_sorted = prepare_rolling_dataframe(df)

    results = []
    for _, group in df_sorted.groupby("analyst_id"):
        group_indexed = group.set_index("closure_timestamp_dt")
        rolling_val = group_indexed["enrichment_actions"].rolling(f"{window_minutes}min").mean()
        rolling_val.index = group.index
        results.append(rolling_val)

    if not results:
        return pd.Series(0.0, index=df.index)

    return pd.concat(results).reindex(df.index).fillna(0.0)
