"""End-to-End processing pipeline runner script for the Alert Fatigue Quantifier.

Executes ingestion, validation, signal engineering, scoring, degradation detection,
machine learning feature engineering, training, cross-validation, and saves output data
for dashboard rendering.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np

# Set the workspace root relative to this file
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

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
from prediction.model import train_predictive_model, save_model
from prediction.validator import validate_model_performance


def main() -> None:
    print("==================================================")
    print("   ALERT FATIGUE QUANTIFIER - E2E PIPELINE RUN    ")
    print("==================================================")

    # 1. Locate the raw log file
    raw_dir = os.path.join(WORKSPACE_ROOT, "data", "raw")
    csv_files = glob.glob(os.path.join(raw_dir, "analyst_logs_*.csv"))
    if not csv_files:
        print("Error: No raw CSV logs found in data/raw/.")
        sys.exit(1)
        
    raw_path = csv_files[0]
    print(f"[1/7] Loading raw logs from: {raw_path}")
    
    # 2. Ingest and Validate
    df = parse_log_file(raw_path)
    print(f"Loaded {len(df)} logs.")
    is_valid = validate_log_schema(df)
    print(f"Schema validation success: {is_valid}")
    if not is_valid:
        print("Error: Schema validation failed. Exiting.")
        sys.exit(1)

    # 3. Calibrate historical baseline profiles (30 days)
    print("[2/7] Calibrating analyst historical baselines...")
    build_and_save_baselines(df)
    
    unique_analysts = df["analyst_id"].unique()
    baselines = {aid: load_baseline(aid) for aid in unique_analysts}
    print(f"Baseline profiles calibrated for: {list(baselines.keys())}")

    # 4. Calculate Rolling window signals (60-minute window)
    print("[3/7] Computing active rolling window signals...")
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

    # 5. Compute Analyst Fatigue Index (AFI)
    print("[4/7] Scoring Analyst Fatigue Index (AFI)...")
    scored_df = calculate_analyst_afi(signals_df, baselines)

    # 6. Detect Statistical Degradation (Mann-Whitney U Test)
    print("[5/7] Detecting operational degradation anomalies...")
    anomalies_df = detect_degradation_anomalies(df, baselines)
    print(f"Detected {len(anomalies_df)} degradation anomalies.")

    # 7. Machine Learning Predictive Modeling
    print("[6/7] Building feature matrix and training predictive model...")
    X, y = build_feature_matrix(scored_df)
    
    # Stratified split and CV validation
    print("Validating model performance...")
    model_template = train_predictive_model(X, y)
    validation_metrics = validate_model_performance(model_template, X, y)
    
    # Train final production model on full dataset
    print("Training final Random Forest model...")
    final_model = train_predictive_model(X, y)
    
    # Save trained model to models/
    model_path = os.path.join(WORKSPACE_ROOT, "data", "models", "fatigue_model.pkl")
    save_model(final_model, model_path)
    print(f"Model saved to: {model_path}")

    # Run predictions across the feature matrix
    risk_prob = final_model.predict_proba(X)[:, 1]
    risk_pred = final_model.predict(X)

    # Re-align predictions to sorted scored alerts dataframe
    # build_feature_matrix returns sorted scored_df rows. Let's recreate it:
    scored_df_sorted = scored_df.copy()
    scored_df_sorted["closure_dt"] = pd.to_datetime(scored_df_sorted["closure_timestamp"])
    scored_df_sorted = scored_df_sorted.sort_values(by=["analyst_id", "closure_dt"])
    
    scored_df_sorted["risk_prob"] = risk_prob
    scored_df_sorted["risk_pred"] = risk_pred
    
    # Drop datetime sorting column before saving
    scored_df_sorted = scored_df_sorted.drop(columns=["closure_dt"])

    # 8. Save output files for dashboard consumption
    output_dir = os.path.join(WORKSPACE_ROOT, "data", "output")
    os.makedirs(output_dir, exist_ok=True)

    scored_out_path = os.path.join(output_dir, "scored_alerts.csv")
    anom_out_path = os.path.join(output_dir, "degradation_anomalies.csv")

    scored_df_sorted.to_csv(scored_out_path, index=False)
    anomalies_df.to_csv(anom_out_path, index=False)

    print("[7/7] Outputs successfully saved for dashboard:")
    print(f"  - Scored alerts with ML predictions: {scored_out_path}")
    print(f"  - Degradation anomalies log:        {anom_out_path}")
    print("==================================================")
    print("Pipeline run completed successfully.")


if __name__ == "__main__":
    main()
