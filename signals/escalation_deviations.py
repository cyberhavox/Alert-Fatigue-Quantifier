"""Escalation Deviations signal calculator for the Alert Fatigue Quantifier.

Computes the rolling absolute deviation of the analyst's current escalation rate
from their 30-day historical baseline rate.
"""

import json
import os
import pandas as pd
from config.settings import PATH_BASELINE_LOGS
from signals.rolling_window import prepare_rolling_dataframe


def load_baseline_escalation_rate(analyst_id: str, df: pd.DataFrame) -> float:
    """Loads the baseline escalation rate for an analyst.

    First attempts to read from a pre-calculated baseline JSON file. If not found,
    calculates it on-the-fly from the historical records in the DataFrame.

    Args:
        analyst_id: Unique analyst identifier.
        df: Fallback log DataFrame.

    Returns:
        The baseline escalation rate as a float ratio.
    """
    baseline_file = os.path.join(PATH_BASELINE_LOGS, f"baseline_{analyst_id}.json")
    if os.path.exists(baseline_file):
        try:
            with open(baseline_file, "r") as f:
                data = json.load(f)
                return float(data.get("baseline_escalation_rate", 0.05))
        except Exception:
            pass

    # Fallback: calculate on-the-fly from data older than 24 hours
    df_sorted = prepare_rolling_dataframe(df)
    analyst_df = df_sorted[df_sorted["analyst_id"] == analyst_id]
    if len(analyst_df) == 0:
        return 0.05  # Default low escalation rate matching SANS distributions

    cutoff = df_sorted["closure_timestamp_dt"].max() - pd.Timedelta(days=1)
    hist_df = analyst_df[analyst_df["closure_timestamp_dt"] < cutoff]

    if len(hist_df) > 0:
        escalations = hist_df["escalation_flag"].sum()
        return float(escalations / len(hist_df))

    # General fallback
    return float(analyst_df["escalation_flag"].sum() / len(analyst_df))


def calculate_escalation_deviations(df: pd.DataFrame, window_minutes: int = 60) -> pd.Series:
    """Calculates the absolute escalation rate deviation in the rolling window.

    Args:
        df: Input log DataFrame.
        window_minutes: Window size in minutes. Defaults to 60.

    Returns:
        A pandas Series of float values representing absolute rate deviations,
        aligned with the original DataFrame index.
    """
    df_sorted = prepare_rolling_dataframe(df)

    # Convert escalation flag to integer representation
    df_sorted["_is_escalated"] = df_sorted["escalation_flag"].astype(int)

    # Cache unique baselines to prevent repeated lookups
    unique_analysts = df_sorted["analyst_id"].unique()
    baselines = {aid: load_baseline_escalation_rate(aid, df_sorted) for aid in unique_analysts}
    df_sorted["_baseline"] = df_sorted["analyst_id"].map(baselines)

    results = []
    for _, group in df_sorted.groupby("analyst_id"):
        group_indexed = group.set_index("closure_timestamp_dt")
        
        # Calculate rolling sum of escalations and rolling count of total alerts
        r_sum = group_indexed["_is_escalated"].rolling(f"{window_minutes}min").sum()
        r_count = group_indexed["_is_escalated"].rolling(f"{window_minutes}min").count()
        rolling_rate = (r_sum / r_count).fillna(0.0)

        # Deviation calculation
        rolling_dev = (rolling_rate - group_indexed["_baseline"]).abs()
        rolling_dev.index = group.index
        results.append(rolling_dev)

    if not results:
        return pd.Series(0.0, index=df.index)

    return pd.concat(results).reindex(df.index).fillna(0.0)
