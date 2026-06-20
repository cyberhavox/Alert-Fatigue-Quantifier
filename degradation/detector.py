"""Degradation Detector logic for the Alert Fatigue Quantifier.

Compares current rolling 60-minute behavior metrics against baseline distributions
using non-parametric Mann-Whitney U statistical testing and flags significant
drops in investigation quality (p < 0.05).
"""

import os
import pandas as pd
import numpy as np
from degradation.mann_whitney import perform_mann_whitney_test
from signals.rolling_window import prepare_rolling_dataframe


def detect_degradation_anomalies(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """Detects statistically significant drops in triage quality.

    Compares active shift alert closure patterns (enrichment actions) for each
    analyst in a rolling 60-minute window against their historical baseline.

    Args:
        df: Input log DataFrame containing baseline and active shift.
        baselines: Dictionary of baseline stats per analyst.

    Returns:
        A pandas DataFrame containing flagged anomalies with columns:
        ['Timestamp', 'Analyst', 'Signal', 'Deviation', 'p-value', 'State']
    """
    df_sorted = prepare_rolling_dataframe(df)
    max_time = df_sorted["closure_timestamp_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)

    # Filter active shift records
    active_shift_df = df_sorted[df_sorted["closure_timestamp_dt"] >= shift_start]
    historical_df = df_sorted[df_sorted["closure_timestamp_dt"] < shift_start]

    anomalies = []

    for idx, row in active_shift_df.iterrows():
        analyst = row["analyst_id"]
        current_time = row["closure_timestamp_dt"]

        # 1. Extract active window data (last 60 minutes)
        window_mask = (
            (df_sorted["analyst_id"] == analyst) &
            (df_sorted["closure_timestamp_dt"] > (current_time - pd.Timedelta(minutes=60))) &
            (df_sorted["closure_timestamp_dt"] <= current_time)
        )
        window_records = df_sorted[window_mask]

        # 2. Extract baseline data for the analyst
        base_records = historical_df[historical_df["analyst_id"] == analyst]
        if len(base_records) < 10 or len(window_records) < 5:
            continue

        # Extract enrichment action distributions
        window_enrich = window_records["enrichment_actions"].values
        base_enrich = base_records["enrichment_actions"].values

        # Apply Mann-Whitney U test
        p_val = perform_mann_whitney_test(window_enrich, base_enrich)

        # Flag anomaly if statistically significant (p < 0.05) and current mean is lower than baseline
        window_mean = float(window_enrich.mean())
        baseline_stats = baselines.get(analyst, {})
        base_mean = baseline_stats.get("mean_enrichment_depth", 6.0)
        base_std = baseline_stats.get("std_enrichment_depth", 1.0)

        if p_val < 0.05 and window_mean < base_mean:
            z_score = (window_mean - base_mean) / base_std
            
            # Determine state based on magnitude of drop (z-score)
            if z_score < -3.0:
                state = "CRITICAL"
            elif z_score < -2.0:
                state = "HIGH"
            else:
                state = "ELEVATED"

            anomalies.append({
                "Timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Analyst": analyst,
                "Signal": "Enrichment Depth",
                "Deviation": round(float(z_score), 2),
                "p-value": round(float(p_val), 4),
                "State": state
            })

    if not anomalies:
        # Return empty dataframe with correct schema
        return pd.DataFrame(columns=["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"])

    # Convert to DataFrame, remove duplicates to avoid flood of alerts for the same event
    anomalies_df = pd.DataFrame(anomalies)
    anomalies_df = anomalies_df.drop_duplicates(subset=["Analyst", "Signal", "State"], keep="last")
    return anomalies_df.sort_values(by="Timestamp")
