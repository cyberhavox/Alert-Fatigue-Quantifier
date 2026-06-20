"""Hourly Closure Rate signal calculator for the Alert Fatigue Quantifier.

Computes the rolling 60-minute count of alert closures compared to the analyst's
30-day historical mean hourly closures.
"""

import json
import os
import pandas as pd
from config.settings import PATH_BASELINE_LOGS
from signals.rolling_window import prepare_rolling_dataframe


def load_baseline_closure_rate(analyst_id: str, df: pd.DataFrame) -> float:
    """Loads the baseline mean hourly alert closures for an analyst.

    First attempts to read from a pre-calculated baseline JSON file. If not found,
    calculates it on-the-fly from the historical records in the DataFrame.

    Args:
        analyst_id: Unique analyst identifier.
        df: Fallback log DataFrame.

    Returns:
        The mean hourly baseline alert closures as a float.
    """
    baseline_file = os.path.join(PATH_BASELINE_LOGS, f"baseline_{analyst_id}.json")
    if os.path.exists(baseline_file):
        try:
            with open(baseline_file, "r") as f:
                data = json.load(f)
                return float(data.get("baseline_hourly_closures", 15.0))
        except Exception:
            pass

    # Fallback: calculate on-the-fly from data older than 24 hours
    df_sorted = prepare_rolling_dataframe(df)
    analyst_df = df_sorted[df_sorted["analyst_id"] == analyst_id]
    if len(analyst_df) == 0:
        return 15.0  # Default nominal closures rate matching settings.py

    cutoff = df_sorted["closure_timestamp_dt"].max() - pd.Timedelta(days=1)
    hist_df = analyst_df[analyst_df["closure_timestamp_dt"] < cutoff]

    if len(hist_df) > 0:
        total_days = (
            hist_df["closure_timestamp_dt"].max() - hist_df["closure_timestamp_dt"].min()
        ).days
        total_hours = max(1.0, total_days * 24.0)
        return float(len(hist_df) / total_hours)

    return 15.0


def calculate_hourly_closure_rate(df: pd.DataFrame, window_minutes: int = 60) -> pd.Series:
    """Calculates the hourly closure rate ratio in the rolling window.

    Args:
        df: Input log DataFrame.
        window_minutes: Window size in minutes. Defaults to 60.

    Returns:
        A pandas Series of float values representing closure rate ratios,
        aligned with the original DataFrame index.
    """
    df_sorted = prepare_rolling_dataframe(df)

    # Temporary column to perform rolling count
    df_sorted["_counter"] = 1

    # Load baseline mean hourly closures per analyst
    unique_analysts = df_sorted["analyst_id"].unique()
    baselines = {aid: load_baseline_closure_rate(aid, df_sorted) for aid in unique_analysts}
    df_sorted["_baseline"] = df_sorted["analyst_id"].map(baselines)

    results = []
    for _, group in df_sorted.groupby("analyst_id"):
        group_indexed = group.set_index("closure_timestamp_dt")
        rolling_count = group_indexed["_counter"].rolling(f"{window_minutes}min").sum()
        
        # Compute ratio: current count / baseline
        rolling_ratio = (rolling_count / group_indexed["_baseline"]).fillna(1.0)
        rolling_ratio.index = group.index
        results.append(rolling_ratio)

    if not results:
        return pd.Series(1.0, index=df.index)

    return pd.concat(results).reindex(df.index).fillna(1.0)
