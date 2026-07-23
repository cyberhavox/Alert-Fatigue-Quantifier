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

    # Analyst-specific profile adjustments for realistic heterogeneous telemetry
    profile_bias = {
        "ANALYST_01": {"triage_mult": 0.8, "enrich_mult": 1.4, "fp_mult": 0.7, "switch_min": 1, "switch_max": 3, "ai_rate": 0.10},
        "ANALYST_02": {"triage_mult": 2.4, "enrich_mult": 0.3, "fp_mult": 1.6, "switch_min": 7, "switch_max": 12, "ai_rate": 0.85},
        "ANALYST_03": {"triage_mult": 1.1, "enrich_mult": 1.1, "fp_mult": 0.9, "switch_min": 2, "switch_max": 5, "ai_rate": 0.30},
        "ANALYST_04": {"triage_mult": 0.6, "enrich_mult": 0.7, "fp_mult": 1.2, "switch_min": 3, "switch_max": 6, "ai_rate": 0.45},
        "ANALYST_05": {"triage_mult": 2.1, "enrich_mult": 0.4, "fp_mult": 1.5, "switch_min": 6, "switch_max": 10, "ai_rate": 0.75},
    }
    prof = profile_bias.get(analyst_id, {"triage_mult": 1.0, "enrich_mult": 1.0, "fp_mult": 1.0, "switch_min": 2, "switch_max": 5, "ai_rate": 0.3})

    # Load distribution configurations from settings
    lam = LAMBDA_FATIGUE if is_fatigued else LAMBDA_NOMINAL
    fp_rate = min(0.95, (FP_RATE_FATIGUE if is_fatigued else FP_RATE_NOMINAL) * prof["fp_mult"])
    enrich_k = max(1.0, (ENRICHMENT_K_FATIGUE if is_fatigued else ENRICHMENT_K_NOMINAL) * prof["enrich_mult"])
    enrich_theta = ENRICHMENT_THETA_FATIGUE if is_fatigued else ENRICHMENT_THETA_NOMINAL
    triage_mean = max(60.0, (TRIAGE_MEAN_FATIGUE if is_fatigued else TRIAGE_MEAN_NOMINAL) * prof["triage_mult"])
    triage_std = TRIAGE_STD_FATIGUE if is_fatigued else TRIAGE_STD_NOMINAL
    notes_mean = NOTES_LEN_MEAN_FATIGUE if is_fatigued else NOTES_LEN_MEAN_NOMINAL

    alert_counter = 1

    while current_time < end_date:
        hours_to_next = random.expovariate(lam)
        current_time += timedelta(hours=hours_to_next)

        if current_time >= end_date:
            break

        alert_id = f"ALERT_{random.randint(100000, 999999)}"
        triage_ts = current_time

        sigma_log = np.sqrt(np.log(1 + (triage_std**2 / triage_mean**2)))
        mu_log = np.log(triage_mean) - (sigma_log**2 / 2)
        triage_seconds = int(random.lognormvariate(mu_log, sigma_log))
        closure_ts = triage_ts + timedelta(seconds=triage_seconds)

        severity_assigned = random.choice(["low", "medium", "high", "critical"])

        rand_val = random.random()
        if is_fatigued:
            if rand_val < fp_rate:
                closure_type = "dismissed"
                escalation_flag = False
                severity_verified = severity_assigned
            elif rand_val < 0.99:
                closure_type = "investigated"
                escalation_flag = False
                severity_verified = random.choice(["low", "medium", "high"])
            else:
                closure_type = "escalated"
                escalation_flag = True
                severity_verified = "high"
        else:
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

        enrichment_actions = int(np.random.gamma(enrich_k, enrich_theta))
        enrichment_actions = max(0, min(50, enrichment_actions))

        if is_fatigued:
            notes_len = int(random.normalvariate(notes_mean, 5.0))
        else:
            notes_len = int(random.normalvariate(notes_mean, NOTES_LEN_STD_NOMINAL))
        notes_len = max(0, min(1000, notes_len))

        # AI Recommendation acceptance and Tool Context Switch Count driven by analyst profile
        ai_accepted = 1 if random.random() < prof["ai_rate"] else 0
        context_switch_count = random.randint(prof["switch_min"], prof["switch_max"])

        # Generate notes text based on length
        notes_text = generate_notes(notes_len)

        mitre_tactics = ["Initial Access", "Execution", "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement", "Exfiltration"]
        mitre_tactic = random.choice(mitre_tactics)

        records.append({
            "analyst_id": analyst_id,
            "alert_id": alert_id,
            "siem_provider": random.choice(["Cortex XSOAR Connector", "Splunk ES Data Lake", "Microsoft Sentinel Collector", "CrowdStrike Falcon Stream"]),
            "triage_timestamp": triage_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_timestamp": closure_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_type": closure_type,
            "severity_assigned": severity_assigned,
            "severity_verified": severity_verified,
            "enrichment_actions": enrichment_actions,
            "escalation_flag": escalation_flag,
            "ai_accepted": ai_accepted,
            "context_switch_count": context_switch_count,
            "mitre_tactic": mitre_tactic,
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
