"""Baseline calibrator for the Alert Fatigue Quantifier.

Calculates the mean and standard deviation of rolling signal values for each
analyst over a 30-day historical log subset and saves them as JSON profiles.
"""

import json
import os
import pandas as pd
from config.settings import PATH_BASELINE_LOGS
from signals.enrichment_depth import calculate_enrichment_depth
from signals.hourly_closure_rate import calculate_hourly_closure_rate
from signals.triage_interval import calculate_triage_interval
from signals.uninvestigated_closures import calculate_uninvestigated_closures


def build_and_save_baselines(df: pd.DataFrame) -> None:
    """Computes baseline statistics for all analysts and saves them to disk.

    Computes means and standard deviations of the 5 rolling signals using
    records older than the active 8-hour shift.

    Args:
        df: Input log DataFrame spanning baseline and active shift.
    """
    df_sorted = df.copy()
    df_sorted["closure_timestamp_dt"] = pd.to_datetime(df_sorted["closure_timestamp"])

    # Baseline data cutoff: records older than the active shift (last 8 hours)
    max_time = df_sorted["closure_timestamp_dt"].max()
    cutoff_time = max_time - pd.Timedelta(hours=8)
    baseline_data = df_sorted[df_sorted["closure_timestamp_dt"] < cutoff_time]

    if len(baseline_data) == 0:
        # Fallback to entire DataFrame if no historical data is older than 8 hours
        baseline_data = df_sorted

    # Create directory if missing
    os.makedirs(PATH_BASELINE_LOGS, exist_ok=True)

    # Pre-compute rolling signal values over the baseline period
    print("Pre-computing rolling signals for historical baseline calibration...")
    triage_series = calculate_triage_interval(baseline_data)
    uninvest_series = calculate_uninvestigated_closures(baseline_data)
    enrich_series = calculate_enrichment_depth(baseline_data)

    # Temporary dataframe to compute grouped statistics
    temp_df = pd.DataFrame({
        "analyst_id": baseline_data["analyst_id"],
        "triage_interval": triage_series,
        "uninvestigated_closures": uninvest_series,
        "enrichment_depth": enrich_series,
        "escalation_flag": baseline_data["escalation_flag"].astype(int),
        "closure_timestamp_dt": baseline_data["closure_timestamp_dt"]
    })

    unique_analysts = df_sorted["analyst_id"].unique()

    for analyst in unique_analysts:
        analyst_df = temp_df[temp_df["analyst_id"] == analyst]
        if len(analyst_df) == 0:
            continue

        # Compute static baseline parameters
        total_escalations = int(analyst_df["escalation_flag"].sum())
        baseline_esc_rate = float(total_escalations / len(analyst_df))

        total_days = (
            analyst_df["closure_timestamp_dt"].max() - analyst_df["closure_timestamp_dt"].min()
        ).days
        total_hours = max(1.0, total_days * 24.0)
        baseline_hourly_closures = float(len(analyst_df) / total_hours)

        # Compute signal means and stds
        triage_mean = float(analyst_df["triage_interval"].mean())
        triage_std = float(analyst_df["triage_interval"].std())
        triage_std = max(1e-4, triage_std)  # Avoid division by zero

        uninvest_mean = float(analyst_df["uninvestigated_closures"].mean())
        uninvest_std = float(analyst_df["uninvestigated_closures"].std())
        uninvest_std = max(1e-4, uninvest_std)

        enrich_mean = float(analyst_df["enrichment_depth"].mean())
        enrich_std = float(analyst_df["enrichment_depth"].std())
        enrich_std = max(1e-4, enrich_std)

        profile = {
            "analyst_id": analyst,
            "mean_triage_interval": triage_mean,
            "std_triage_interval": triage_std,
            "mean_uninvestigated_closures": uninvest_mean,
            "std_uninvestigated_closures": uninvest_std,
            "mean_enrichment_depth": enrich_mean,
            "std_enrichment_depth": enrich_std,
            "baseline_escalation_rate": baseline_esc_rate,
            "baseline_hourly_closures": baseline_hourly_closures
        }

        output_path = os.path.join(PATH_BASELINE_LOGS, f"baseline_{analyst}.json")
        with open(output_path, "w") as f:
            json.dump(profile, f, indent=4)


def load_baseline(analyst_id: str) -> dict:
    """Loads stored baseline profile for an analyst.

    Args:
        analyst_id: Unique analyst identifier.

    Returns:
        Dictionary containing baseline statistics.

    Raises:
        FileNotFoundError: If no baseline profile exists for the analyst.
    """
    baseline_path = os.path.join(PATH_BASELINE_LOGS, f"baseline_{analyst_id}.json")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"No baseline profile found for analyst: {analyst_id}")

    with open(baseline_path, "r") as f:
        return json.load(f)
