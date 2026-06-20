"""Main app entry point for the Streamlit dashboard.

Orchestrates data loading, header controls, filtering, and mounts individual
monitoring panels (cards grid, recommendation sidebar, charts, anomalies log, and forecast).
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

# Add the workspace root to Python path to import modules
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from scoring.baseline_calibrator import load_baseline
from recommendations.engine import get_advisory_recommendations
from dashboard.components.analyst_card import render_analyst_card
from dashboard.components.signal_charts import render_signal_charts
from dashboard.components.anomaly_log import render_anomaly_log
from dashboard.components.forecast_panel import render_forecast_panel
from dashboard.components.recommendation_panel import render_recommendation_panel

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="Alert Fatigue Quantifier",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Theme
theme_css_path = os.path.join(WORKSPACE_ROOT, "dashboard", "styles", "theme.css")
if os.path.exists(theme_css_path):
    with open(theme_css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# 3. Load Data Helper Functions
@st.cache_data(ttl=10)  # Short TTL to allow updates
def load_pipeline_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Loads scored alerts, anomalies, and baselines from output directories.

    Returns:
        A tuple of (scored_df, anomalies_df, baselines_dict).
    """
    scored_path = os.path.join(WORKSPACE_ROOT, "data", "output", "scored_alerts.csv")
    anomalies_path = os.path.join(WORKSPACE_ROOT, "data", "output", "degradation_anomalies.csv")

    if not os.path.exists(scored_path):
        return pd.DataFrame(), pd.DataFrame(), {}

    scored_df = pd.read_csv(scored_path)
    
    if os.path.exists(anomalies_path):
        anomalies_df = pd.read_csv(anomalies_path)
    else:
        anomalies_df = pd.DataFrame(columns=["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"])

    # Load baselines for all unique analysts
    unique_analysts = scored_df["analyst_id"].unique()
    baselines = {}
    for aid in unique_analysts:
        try:
            baselines[aid] = load_baseline(aid)
        except Exception:
            # Fallback if baseline doesn't exist
            baselines[aid] = {
                "mean_triage_interval": 180.0,
                "std_triage_interval": 60.0,
                "mean_enrichment_depth": 6.0,
                "std_enrichment_depth": 1.0,
                "mean_uninvestigated_closures": 0.05,
                "std_uninvestigated_closures": 0.02
            }

    return scored_df, anomalies_df, baselines


def main() -> None:
    # Title Bar Container
    st.markdown(
        """
        <div class="header-container">
            <h2 class="header-title">🛡️ Alert Fatigue Quantifier</h2>
            <p style="margin: 6px 0 0 0; font-size: 13px; color: var(--text-secondary); font-weight: 500;">
                Cognitive Load & Operational Degradation Monitoring for SOC Analysts
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Data Loading & Empty State Check
    scored_df, anomalies_df, baselines = load_pipeline_data()

    if scored_df.empty:
        st.info("No log file detected. Load a CSV or JSON export to begin.")
        st.markdown(
            """
            <div style="background-color: var(--bg-surface); padding: 20px; border-radius: 6px; border: 1px solid var(--border-subtle);">
                <h4>Pipeline Setup Guide</h4>
                <ol>
                    <li>Generate synthetic raw data or ingest alert logs into <code>data/raw/</code></li>
                    <li>Run the end-to-end processing pipeline script: <code>scratch/run_full_pipeline.py</code></li>
                    <li>The dashboard will automatically display pre-computed scores once they are saved to <code>data/output/</code></li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # 5. Header Controls (Filter and Refresh Info)
    unique_analysts = sorted(scored_df["analyst_id"].unique())
    
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        filtered_analysts = st.multiselect(
            "Filter analysts",
            options=unique_analysts,
            default=unique_analysts,
            help="Narrow down the active analyst group displayed in the cards and charts."
        )
    with col_refresh:
        # Time and auto-refresh control
        now_str = datetime.now().strftime("%H:%M:%S")
        st.markdown(
            f"""
            <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-secondary); margin-top: 5px;">
                Last updated: {now_str}
            </div>
            """,
            unsafe_allow_html=True
        )
        auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)

    if not filtered_analysts:
        st.warning("Please select at least one analyst to display.")
        return

    # Focus selection for recommendation details
    focus_analyst = st.selectbox(
        "Focus Analyst (for Recommendations & Forecasting)",
        options=filtered_analysts,
        index=0
    )

    # 6. Upper Page Layout (Analyst Cards + Recommendation Panel)
    col_grid, col_rec = st.columns([3, 1])

    with col_grid:
        st.markdown('<div class="section-header">Active Analysts Shift Status</div>', unsafe_allow_html=True)
        # Cards grid (up to 3 columns)
        card_cols = st.columns(3)
        for i, aid in enumerate(filtered_analysts):
            col_idx = i % 3
            with card_cols[col_idx]:
                # Extract latest record details
                analyst_logs = scored_df[scored_df["analyst_id"] == aid]
                if analyst_logs.empty:
                    continue
                latest_log = analyst_logs.sort_values(by="closure_timestamp").iloc[-1]
                
                # Fetch baseline
                base = baselines.get(aid, {})
                
                # Compute state based on AFI score
                score = float(latest_log["afi_score"])
                if score < 50.0:
                    state = "NOMINAL"
                elif score < 70.0:
                    state = "ELEVATED"
                elif score < 90.0:
                    state = "HIGH"
                else:
                    state = "CRITICAL"

                # Parse timestamp for display
                ts_dt = pd.to_datetime(latest_log["closure_timestamp"])
                ts_str = ts_dt.strftime("%H:%M")

                # Compile signals dict
                signals_dict = {
                    "triage_interval": latest_log["triage_interval"],
                    "enrichment_depth": latest_log["enrichment_depth"],
                    "uninvestigated_closures": latest_log["uninvestigated_closures"],
                    "escalation_deviations": latest_log["escalation_deviations"],
                    "hourly_closure_rate": latest_log["hourly_closure_rate"]
                }

                render_analyst_card(
                    analyst_id=aid,
                    afi_score=score,
                    state=state,
                    timestamp=ts_str,
                    signals=signals_dict,
                    baseline=base
                )

    with col_rec:
        # Get focus analyst details
        focus_logs = scored_df[scored_df["analyst_id"] == focus_analyst]
        if not focus_logs.empty:
            focus_latest = focus_logs.sort_values(by="closure_timestamp").iloc[-1]
            focus_score = float(focus_latest["afi_score"])
            focus_pred = int(focus_latest.get("risk_pred", 0))

            # Fetch active anomalies for the focus analyst in the last 8 hours
            max_time = pd.to_datetime(scored_df["closure_timestamp"]).max()
            shift_start = max_time - pd.Timedelta(hours=8)
            
            focus_anom_records = []
            if not anomalies_df.empty:
                focus_anom_df = anomalies_df[anomalies_df["Analyst"] == focus_analyst].copy()
                if not focus_anom_df.empty:
                    focus_anom_df["closure_dt"] = pd.to_datetime(focus_anom_df["Timestamp"])
                    focus_anom_df = focus_anom_df[focus_anom_df["closure_dt"] >= shift_start]
                    focus_anom_records = focus_anom_df.to_dict("records")

            # Generate recommendations map
            recs = get_advisory_recommendations(
                afi_score=focus_score,
                anomalies=focus_anom_records,
                prediction_flag=focus_pred
            )

            render_recommendation_panel(
                analyst_id=focus_analyst,
                afi_score=focus_score,
                recommendations=recs
            )

    # 7. Signal Trend Charts Section
    st.markdown('<div class="section-header">Signal Trend Analysis (Active Shift)</div>', unsafe_allow_html=True)
    render_signal_charts(
        analyst_id=focus_analyst,
        scored_df=scored_df,
        baseline=baselines.get(focus_analyst, {}),
        anomalies_df=anomalies_df
    )

    # 8. Anomaly Log Section
    render_anomaly_log(anomalies_df)

    # 9. Predictive Forecast Section
    # Extract prediction arrays for the forecast panel
    risk_probabilities = scored_df["risk_prob"].values if "risk_prob" in scored_df.columns else np.zeros(len(scored_df))
    risk_predictions = scored_df["risk_pred"].values if "risk_pred" in scored_df.columns else np.zeros(len(scored_df))
    
    render_forecast_panel(
        analyst_id=focus_analyst,
        scored_df=scored_df,
        risk_probabilities=risk_probabilities,
        risk_predictions=risk_predictions
    )

    # 10. Auto refresh logic
    if auto_refresh:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
