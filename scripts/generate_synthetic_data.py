"""Synthetic Data Generator for the Alert Fatigue Quantifier.

This script generates synthetic SOC activity logs for multiple analysts spanning
a historical baseline period (30 days) and an active shift (the current day).
It simulates normal behavior during the baseline period and introduces alert
fatigue states (high volume, low enrichment, triage delays, and shortcutting)
during the current shift. All distribution parameters are imported from the
central configuration file config/settings.py.

Author: Raghav Gupta
USN: 241VMTR01929
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import List
import numpy as np
import pandas as pd

# Add the workspace root to Python path to resolve imports from config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import (
    BASELINE_DAYS,
    ENRICHMENT_K_FATIGUE,
    ENRICHMENT_K_NOMINAL,
    ENRICHMENT_THETA_FATIGUE,
    ENRICHMENT_THETA_NOMINAL,
    FP_RATE_FATIGUE,
    FP_RATE_NOMINAL,
    LAMBDA_FATIGUE,
    LAMBDA_NOMINAL,
    NOTES_LEN_MEAN_FATIGUE,
    NOTES_LEN_MEAN_NOMINAL,
    NOTES_LEN_STD_NOMINAL,
    PATH_RAW_LOGS,
    TRIAGE_MEAN_FATIGUE,
    TRIAGE_MEAN_NOMINAL,
    TRIAGE_STD_FATIGUE,
    TRIAGE_STD_NOMINAL,
)


def generate_notes(length: int) -> str:
    """Generates a random string of notes matching a specific length constraint.

    Args:
        length: Desired character length of the generated notes.

    Returns:
        A string containing mock analyst notes of the specified length.
    """
    if length <= 0:
        return ""
    words = [
        "investigated", "traffic", "payload", "normal", "legitimate",
        "advisory", "host", "source", "destination", "malicious",
        "false-positive", "rules", "matched", "session", "closed",
        "verified", "escalated", "threat", "indicators", "resolved"
    ]
    notes_words: List[str] = []
    current_len = 0
    while current_len < length:
        word = random.choice(words)
        notes_words.append(word)
        current_len += len(word) + 1
    return " ".join(notes_words)[:length]


def generate_analyst_logs(
    analyst_id: str,
    start_date: datetime,
    end_date: datetime,
    is_fatigued: bool = False
) -> pd.DataFrame:
    """Generates synthetic log records for a single analyst over a timeframe.

    Args:
        analyst_id: Unique identifier for the SOC analyst.
        start_date: Start datetime of the log generation window.
        end_date: End datetime of the log generation window.
        is_fatigued: If True, forces fatigued distributions on behavioral signals.

    Returns:
        A pandas DataFrame containing generated logs for the analyst.
    """
    records = []
    current_time = start_date

    # Load distribution configurations from settings
    lam = LAMBDA_FATIGUE if is_fatigued else LAMBDA_NOMINAL
    fp_rate = FP_RATE_FATIGUE if is_fatigued else FP_RATE_NOMINAL
    enrich_k = ENRICHMENT_K_FATIGUE if is_fatigued else ENRICHMENT_K_NOMINAL
    enrich_theta = ENRICHMENT_THETA_FATIGUE if is_fatigued else ENRICHMENT_THETA_NOMINAL
    triage_mean = TRIAGE_MEAN_FATIGUE if is_fatigued else TRIAGE_MEAN_NOMINAL
    triage_std = TRIAGE_STD_FATIGUE if is_fatigued else TRIAGE_STD_NOMINAL
    notes_mean = NOTES_LEN_MEAN_FATIGUE if is_fatigued else NOTES_LEN_MEAN_NOMINAL

    alert_counter = 1

    while current_time < end_date:
        # Time to next alert assignment follows an Exponential distribution (Poisson process)
        hours_to_next = random.expovariate(lam)
        current_time += timedelta(hours=hours_to_next)

        if current_time >= end_date:
            break

        # Generate alert details
        alert_id = f"ALERT_{random.randint(100000, 999999)}"
        triage_ts = current_time

        # Triage interval follows a Log-Normal distribution
        # Log-normal parameters calculation from mean and std
        sigma_log = np.sqrt(np.log(1 + (triage_std**2 / triage_mean**2)))
        mu_log = np.log(triage_mean) - (sigma_log**2 / 2)
        triage_seconds = int(random.lognormvariate(mu_log, sigma_log))
        closure_ts = triage_ts + timedelta(seconds=triage_seconds)

        # Assign initial severity
        severity_assigned = random.choice(["low", "medium", "high", "critical"])

        # Determine closure type and escalation
        rand_val = random.random()
        if is_fatigued:
            # Shortcutting: high false positive rate, low escalation rate
            if rand_val < fp_rate:
                closure_type = "dismissed"
                escalation_flag = False
                severity_verified = severity_assigned  # Accept default without validation
            elif rand_val < 0.99:
                closure_type = "investigated"
                escalation_flag = False
                severity_verified = random.choice(["low", "medium", "high"])
            else:
                closure_type = "escalated"
                escalation_flag = True
                severity_verified = "high"
        else:
            # Nominal: typical triage investigation distributions
            if rand_val < fp_rate:
                closure_type = "dismissed"
                escalation_flag = False
                severity_verified = random.choice(["low", "medium", "high"])
            elif rand_val < 0.95:
                closure_type = "investigated"
                escalation_flag = False
                severity_verified = random.choice(["low", "medium", "high", "critical"])
            else:
                closure_type = "escalated"
                escalation_flag = True
                severity_verified = "high"

        # Enrichment actions follow a Gamma distribution
        enrichment_actions = int(np.random.gamma(enrich_k, enrich_theta))
        enrichment_actions = max(0, min(50, enrichment_actions))

        # Notes length follows Normal distribution, bounded below at 0
        if is_fatigued:
            notes_len = int(random.normalvariate(notes_mean, 5.0))
        else:
            notes_len = int(random.normalvariate(notes_mean, NOTES_LEN_STD_NOMINAL))
        notes_len = max(0, min(1000, notes_len))

        # Generate notes text based on length
        notes_text = generate_notes(notes_len)

        records.append({
            "analyst_id": analyst_id,
            "alert_id": alert_id,
            "triage_timestamp": triage_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_timestamp": closure_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_type": closure_type,
            "severity_assigned": severity_assigned,
            "severity_verified": severity_verified,
            "enrichment_actions": enrichment_actions,
            "escalation_flag": escalation_flag,
            "notes": notes_text
        })
        alert_counter += 1

    return pd.DataFrame(records)


def main() -> None:
    """Main execution block to generate the log dataset and save to disk."""
    print("Initializing synthetic dataset generation...")

    # Define analysts to simulate
    analysts = ["ANALYST_01", "ANALYST_02", "ANALYST_03", "ANALYST_04", "ANALYST_05"]

    # Time boundaries
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BASELINE_DAYS)
    current_shift_start = end_date - timedelta(hours=8)

    all_logs = []

    for analyst in analysts:
        print(f"Simulating historical logs for {analyst}...")
        # Historical baseline: nominal state for all analysts
        hist_df = generate_analyst_logs(
            analyst_id=analyst,
            start_date=start_date,
            end_date=current_shift_start,
            is_fatigued=False
        )
        all_logs.append(hist_df)

        # Current shift logs: simulate fatigue for ANALYST_02 and ANALYST_05
        is_fatigued_today = analyst in ["ANALYST_02", "ANALYST_05"]
        state_label = "FATIGUED" if is_fatigued_today else "NOMINAL"
        print(f"Simulating current active shift for {analyst} ({state_label})...")
        
        shift_df = generate_analyst_logs(
            analyst_id=analyst,
            start_date=current_shift_start,
            end_date=end_date,
            is_fatigued=is_fatigued_today
        )
        all_logs.append(shift_df)

    # Combine all records
    full_dataset = pd.concat(all_logs, ignore_index=True)

    # Sort chronologically by triage timestamp
    full_dataset["triage_dt"] = pd.to_datetime(full_dataset["triage_timestamp"])
    full_dataset = full_dataset.sort_values(by="triage_dt").drop(columns=["triage_dt"])

    # Ensure output raw folder exists
    os.makedirs(PATH_RAW_LOGS, exist_ok=True)

    # Define file name using YYYYMMDD suffix
    date_suffix = end_date.strftime("%Y%m%d")
    output_filename = f"analyst_logs_{date_suffix}.csv"
    output_path = os.path.join(PATH_RAW_LOGS, output_filename)

    print(f"Writing {len(full_dataset)} records to {output_path}...")
    full_dataset.to_csv(output_path, index=False)
    print("Dataset generation completed successfully.")


if __name__ == "__main__":
    main()
