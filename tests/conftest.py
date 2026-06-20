"""Shared PyTest fixtures for the Alert Fatigue Quantifier test suite.

Provides mock data frames, baseline profiles, and configured samples to be used
across ingestion, signals, scoring, degradation, and prediction unit tests.
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def mock_raw_data() -> pd.DataFrame:
    """Generates a mock DataFrame mimicking raw ingested logs.

    Contains 20 records for multiple analysts with standard fields.
    """
    records = []
    base_time = pd.Timestamp("2026-06-20T10:00:00Z")
    
    # Generate 20 records spaced by 10 minutes
    for i in range(20):
        triage_dt = base_time + pd.Timedelta(minutes=10 * i)
        # Triage interval is 3 minutes (180s)
        closure_dt = triage_dt + pd.Timedelta(seconds=180)
        
        analyst_id = "ANALYST_01" if i % 2 == 0 else "ANALYST_02"
        
        records.append({
            "analyst_id": analyst_id,
            "alert_id": f"ALERT_{i:06d}",
            "triage_timestamp": triage_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_timestamp": closure_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_type": "dismissed" if i % 3 != 0 else "investigated",
            "severity_assigned": "medium",
            "severity_verified": "medium",
            "enrichment_actions": 5 if analyst_id == "ANALYST_01" else 1,
            "escalation_flag": False,
            "notes": "Triage notes written here" if i % 4 != 0 else ""
        })
        
    return pd.DataFrame(records)


@pytest.fixture
def mock_baseline_data() -> dict[str, dict[str, float]]:
    """Generates mock baseline profiles for simulated analysts.

    Contains mean and standard deviations of rolling window signals.
    """
    return {
        "ANALYST_01": {
            "mean_triage_interval": 180.0,
            "std_triage_interval": 60.0,
            "mean_uninvestigated_closures": 0.05,
            "std_uninvestigated_closures": 0.02,
            "mean_enrichment_depth": 6.0,
            "std_enrichment_depth": 1.0,
            "mean_escalation_deviations": 0.0,
            "std_escalation_deviations": 0.15,
            "mean_hourly_closure_rate": 1.0,
            "std_hourly_closure_rate": 0.5
        },
        "ANALYST_02": {
            "mean_triage_interval": 200.0,
            "std_triage_interval": 80.0,
            "mean_uninvestigated_closures": 0.08,
            "std_uninvestigated_closures": 0.03,
            "mean_enrichment_depth": 5.0,
            "std_enrichment_depth": 1.2,
            "mean_escalation_deviations": 0.0,
            "std_escalation_deviations": 0.15,
            "mean_hourly_closure_rate": 1.0,
            "std_hourly_closure_rate": 0.5
        }
    }


@pytest.fixture
def mock_signals_df() -> pd.DataFrame:
    """Generates a scored signals DataFrame containing rolling indicators.

    Suitable for normalisation, scoring, and prediction test modules.
    """
    records = []
    base_time = pd.Timestamp("2026-06-20T10:00:00Z")
    
    # Create 30 records for ANALYST_01 and ANALYST_02
    for i in range(30):
        t_stamp = base_time + pd.Timedelta(minutes=15 * i)
        analyst_id = "ANALYST_01" if i < 15 else "ANALYST_02"
        
        # Fatigued signatures for ANALYST_02
        if analyst_id == "ANALYST_02":
            triage_interval = 400.0  # Elongated triage
            uninvestigated_closures = 0.8  # High uninvestigated
            enrichment_depth = 1.0  # Low enrichment depth
            escalation_deviations = 0.4
            hourly_closure_rate = 2.0
            afi_score = 80.0  # Fatigue AFI
        else:
            triage_interval = 180.0  # Nominal triage
            uninvestigated_closures = 0.05
            enrichment_depth = 5.5  # High enrichment depth
            escalation_deviations = 0.0
            hourly_closure_rate = 1.0
            afi_score = 45.0  # Nominal AFI
            
        records.append({
            "analyst_id": analyst_id,
            "closure_timestamp": t_stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "triage_interval": triage_interval,
            "uninvestigated_closures": uninvestigated_closures,
            "enrichment_depth": enrichment_depth,
            "escalation_deviations": escalation_deviations,
            "hourly_closure_rate": hourly_closure_rate
        })
        
    df = pd.DataFrame(records)
    # Inject baseline scores directly for testing
    df["afi_score"] = [45.0] * 15 + [80.0] * 15
    return df
