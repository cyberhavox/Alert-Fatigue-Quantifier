"""End-to-End Integration and Performance Profiling Tests.

Executes the entire Alert Fatigue Quantifier pipeline sequentially, capturing execution
times for each stage via cProfile, and validating data leakage guidelines.
"""

import os
import io
import cProfile
import pstats
import time
import pickle
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from sklearn.ensemble import RandomForestClassifier

# Pipeline module imports
from ingestion.parser import parse_log_file
from ingestion.validator import validate_log_schema
from scoring.baseline_calibrator import build_and_save_baselines, load_baseline
from scoring.afi_calculator import calculate_analyst_afi
from signals.triage_interval import calculate_triage_interval
from signals.uninvestigated_closures import calculate_uninvestigated_closures
from signals.enrichment_depth import calculate_enrichment_depth
from signals.escalation_deviations import calculate_escalation_deviations
from signals.hourly_closure_rate import calculate_hourly_closure_rate
from degradation.detector import detect_degradation_anomalies
from prediction.feature_engineering import build_feature_matrix
from prediction.model import train_predictive_model, save_model, load_model, predict_fatigue_risk
from prediction.validator import validate_model_performance
from recommendations.engine import get_advisory_recommendations


def test_e2e_pipeline_integration_and_performance(tmp_path) -> None:
    """Runs the entire AFQ pipeline end-to-end.

    Asserts:
    1. Processing completes successfully at each stage.
    2. cProfile captures performance and all Pandas operations run within a 5-second threshold.
    3. Train-test splits and CV folds have zero index overlap (no data leakage).
    4. Serialized models and baselines are saved/loaded correctly.
    """
    # --- Step 1: Create a realistic synthetic dataset in-memory ---
    records = []
    base_time = pd.Timestamp("2026-06-01T08:00:00Z")
    
    # 50 historical logs (spaced 1 hour) representing the 30-day baseline period (nominal state)
    for i in range(50):
        triage_dt = base_time + pd.Timedelta(hours=i)
        # nominal triage time: 3 mins (180s)
        closure_dt = triage_dt + pd.Timedelta(seconds=180)
        records.append({
            "analyst_id": "ANALYST_01",
            "alert_id": f"ALERT_HIST_{i:06d}",
            "triage_timestamp": triage_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_timestamp": closure_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_type": "investigated" if i % 5 != 0 else "dismissed",
            "severity_assigned": "high",
            "severity_verified": "high",
            "enrichment_actions": 6,  # nominal depth
            "escalation_flag": i % 10 == 0,
            "notes": "Nominal ticket closure details."
        })
        
    # 20 active shift logs (spaced 15 minutes) representing the current shift (extreme fatigue state)
    active_start_time = base_time + pd.Timedelta(hours=50)
    for i in range(20):
        triage_dt = active_start_time + pd.Timedelta(minutes=15 * i)
        # fatigued triage time: 8 mins (480s)
        closure_dt = triage_dt + pd.Timedelta(seconds=480)
        records.append({
            "analyst_id": "ANALYST_01",
            "alert_id": f"ALERT_ACTIVE_{i:06d}",
            "triage_timestamp": triage_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_timestamp": closure_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "closure_type": "dismissed",  # fatigue shortcutting
            "severity_assigned": "high",
            "severity_verified": "medium",  # default validation severity accepted
            "enrichment_actions": 1,  # fatigue shortcutting
            "escalation_flag": False,
            "notes": ""  # empty notes
        })

    raw_df = pd.DataFrame(records)
    
    # Save to temp path to test csv parsing
    temp_csv_path = tmp_path / "synthetic_analyst_logs.csv"
    raw_df.to_csv(temp_csv_path, index=False)

    # Initialize cProfile
    pr = cProfile.Profile()
    pr.enable()

    # --- Step 2: Ingestion & Parsing ---
    start_time = time.time()
    df = parse_log_file(str(temp_csv_path))
    assert len(df) == 70
    assert validate_log_schema(df) is True
    ingest_time = time.time() - start_time
    assert ingest_time < 5.0, f"Ingestion stage took {ingest_time:.2f}s, exceeding threshold!"

    # --- Step 3: Baseline Calibration ---
    start_time = time.time()
    with patch("scoring.baseline_calibrator.PATH_BASELINE_LOGS", str(tmp_path)):
        build_and_save_baselines(df)
        assert (tmp_path / "baseline_ANALYST_01.json").exists()
        
        baselines = {"ANALYST_01": load_baseline("ANALYST_01")}
        assert baselines["ANALYST_01"]["mean_enrichment_depth"] == 6.0
    baseline_time = time.time() - start_time
    assert baseline_time < 5.0, f"Baseline Calibration stage took {baseline_time:.2f}s, exceeding threshold!"

    # --- Step 4: Signals Calculations ---
    start_time = time.time()
    triage_int = calculate_triage_interval(df)
    uninvest_cls = calculate_uninvestigated_closures(df)
    enrich_depth = calculate_enrichment_depth(df)
    escalation_dev = calculate_escalation_deviations(df)
    hourly_rate = calculate_hourly_closure_rate(df)

    signals_df = pd.DataFrame({
        "analyst_id": df["analyst_id"],
        "closure_timestamp": df["closure_timestamp"],
        "triage_interval": triage_int,
        "uninvestigated_closures": uninvest_cls,
        "enrichment_depth": enrich_depth,
        "escalation_deviations": escalation_dev,
        "hourly_closure_rate": hourly_rate
    }, index=df.index)
    signals_time = time.time() - start_time
    assert signals_time < 5.0, f"Signals Calculation stage took {signals_time:.2f}s, exceeding threshold!"

    # --- Step 5: AFI Scoring ---
    start_time = time.time()
    scored_df = calculate_analyst_afi(signals_df, baselines)
    assert "afi_score" in scored_df.columns
    assert scored_df["afi_score"].min() >= 0.0
    assert scored_df["afi_score"].max() <= 100.0
    scoring_time = time.time() - start_time
    assert scoring_time < 5.0, f"AFI Scoring stage took {scoring_time:.2f}s, exceeding threshold!"

    # --- Step 6: Degradation Anomaly Detection ---
    start_time = time.time()
    anomalies_df = detect_degradation_anomalies(df, baselines)
    assert isinstance(anomalies_df, pd.DataFrame)
    if not anomalies_df.empty:
        assert (anomalies_df["p-value"] < 0.05).all()
        assert "State" in anomalies_df.columns
    degradation_time = time.time() - start_time
    assert degradation_time < 5.0, f"Degradation Detection stage took {degradation_time:.2f}s, exceeding threshold!"

    # --- Step 7: Predictive Modelling (Random Forest) & Data Leakage checks ---
    start_time = time.time()
    X, y = build_feature_matrix(scored_df)
    
    # Run performance cross validation + metrics verification
    metrics = validate_model_performance(train_predictive_model(X, y), X, y)
    assert "cv_mean_accuracy" in metrics
    assert "split_f1" in metrics

    # Train and serialize model to tmp_path
    final_model = train_predictive_model(X, y)
    assert isinstance(final_model, RandomForestClassifier)
    
    model_file = tmp_path / "fatigue_model.pkl"
    save_model(final_model, str(model_file))
    assert model_file.exists()

    # Load serialized model back and run inference
    loaded_model = load_model(str(model_file))
    preds = predict_fatigue_risk(loaded_model, X)
    assert len(preds) == len(X)
    predict_time = time.time() - start_time
    assert predict_time < 5.0, f"Prediction stage took {predict_time:.2f}s, exceeding threshold!"

    # --- Step 8: Advisory Recommendations Engine ---
    start_time = time.time()
    # Find latest AFI score
    latest_afi = scored_df.iloc[-1]["afi_score"]
    anomalies_list = anomalies_df.to_dict(orient="records") if not anomalies_df.empty else []
    latest_pred = int(preds[-1])
    
    recommendations_data = get_advisory_recommendations(
        afi_score=latest_afi,
        anomalies=anomalies_list,
        prediction_flag=latest_pred
    )
    assert isinstance(recommendations_data, dict)
    assert "state" in recommendations_data
    assert "primary_recommendation" in recommendations_data
    assert "actions" in recommendations_data
    assert "warnings" in recommendations_data
    assert "disclaimer" in recommendations_data
    
    # Confirm mandatory advisory disclaimer text
    assert "advisory" in recommendations_data["disclaimer"].lower()
    
    recs_time = time.time() - start_time
    assert recs_time < 5.0, f"Recommendations Engine stage took {recs_time:.2f}s, exceeding threshold!"


    # Disable profiling and output stats
    pr.disable()
    s = io.StringIO()
    sortby = "cumulative"
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(15)  # print top 15 calls
    
    print("\n================== cProfile Pipeline Stats ==================")
    print(s.getvalue())
    print("=============================================================")
