"""Alert Fatigue Quantifier (AFQ) — Professional SOC Operations Dashboard.

Monitors real-time analyst cognitive load, detects decision-quality degradation,
forecasts upcoming fatigue risk, and presents academic methodology & literature base.
"""

from __future__ import annotations
import os
import sys
import time
import subprocess
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

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
from dashboard.components.methodology_panel import render_methodology_panel

# ── Page Configuration ───────────────────────────────────────
st.set_page_config(
    page_title="Alert Fatigue Quantifier | SOC Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject Theme CSS ──────────────────────────────────────────
_theme_path = os.path.join(WORKSPACE_ROOT, "dashboard", "styles", "theme.css")
if os.path.exists(_theme_path):
    with open(_theme_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


@st.cache_resource
def _bootstrap_pipeline() -> bool:
    """Runs data generator and pipeline once if missing."""
    scored_path = os.path.join(WORKSPACE_ROOT, "data", "output", "scored_alerts.csv")
    if os.path.exists(scored_path):
        return True

    scripts = [
        [sys.executable, os.path.join(WORKSPACE_ROOT, "scripts", "generate_synthetic_data.py")],
        [sys.executable, os.path.join(WORKSPACE_ROOT, "scripts", "run_full_pipeline.py")],
    ]
    for cmd in scripts:
        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        if res.returncode != 0:
            st.error(f"Pipeline error: {res.stderr[:300]}")
            return False
    return True


@st.cache_data(ttl=10)
def load_pipeline_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Loads scored alerts, degradation anomalies, and baselines."""
    scored_path    = os.path.join(WORKSPACE_ROOT, "data", "output", "scored_alerts.csv")
    anomalies_path = os.path.join(WORKSPACE_ROOT, "data", "output", "degradation_anomalies.csv")

    if not os.path.exists(scored_path):
        return pd.DataFrame(), pd.DataFrame(), {}

    scored_df = pd.read_csv(scored_path)

    if os.path.exists(anomalies_path):
        anomalies_df = pd.read_csv(anomalies_path)
    else:
        anomalies_df = pd.DataFrame(
            columns=["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]
        )

    baselines: dict = {}
    for aid in scored_df["analyst_id"].unique():
        try:
            baselines[aid] = load_baseline(aid)
        except Exception:
            baselines[aid] = {
                "mean_triage_interval":        180.0,
                "std_triage_interval":          60.0,
                "mean_enrichment_depth":         6.0,
                "std_enrichment_depth":          1.0,
                "mean_uninvestigated_closures":  0.05,
                "std_uninvestigated_closures":   0.02,
            }

    return scored_df, anomalies_df, baselines


def _afi_state(score: float) -> str:
    if score < 50.0:  return "NOMINAL"
    if score < 70.0:  return "ELEVATED"
    if score < 90.0:  return "HIGH"
    return "CRITICAL"


def main() -> None:
    # ── Auto-Bootstrap Pipeline ───────────────────────────────
    with st.spinner("Initializing Telemetry Engine..."):
        _bootstrap_pipeline()

    # ── Header Bar ────────────────────────────────────────────
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    header_html = _clean_html(f"""
    <div class="afq-header">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div class="afq-header-title">Alert Fatigue Quantifier (AFQ)</div>
          <div class="afq-header-subtitle">
            SOC Analyst Cognitive Capacity &amp; Behavioral Degradation Monitoring System
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <span class="afq-header-live">&bull; TELEMETRY STREAM ACTIVE</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-secondary); background:#e2e8f0; padding:4px 10px; border-radius:4px;">{now_str}</span>
        </div>
      </div>
    </div>
    """)
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Primary Navigation Tabs ───────────────────────────────
    main_tab1, main_tab2 = st.tabs([
        "Live SOC Operations Dashboard",
        "Research Methodology & Literature Base (18 Sources)"
    ])

    with main_tab2:
        render_methodology_panel()

    with main_tab1:
        # ── Data Loading ──────────────────────────────────────
        scored_df, anomalies_df, baselines = load_pipeline_data()

        if scored_df.empty:
            st.error("No telemetry logs detected. Execute `python scripts/run_full_pipeline.py` to ingest telemetry.")
            return

        # Filter active shift (last 8 hours)
        scored_df["closure_dt"] = pd.to_datetime(scored_df["closure_timestamp"])
        max_time = scored_df["closure_dt"].max()
        shift_start = max_time - pd.Timedelta(hours=8)
        shift_df = scored_df[scored_df["closure_dt"] >= shift_start].copy()

        # ── High Contrast KPI Cards ───────────────────────────
        total_logs = len(shift_df)
        unique_analysts = sorted(scored_df["analyst_id"].unique())

        latest_per_analyst = shift_df.sort_values("closure_dt").groupby("analyst_id").last()
        mean_afi = latest_per_analyst["afi_score"].mean() if not latest_per_analyst.empty else 0.0
        global_state = _afi_state(mean_afi)

        mean_triage = shift_df["triage_interval"].mean() if not shift_df.empty else 0.0
        anom_count = len(anomalies_df)

        afi_color = "#059669" if mean_afi < 50 else ("#d97706" if mean_afi < 70 else "#dc2626")

        kpi_html = _clean_html(f"""
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:20px;">
          <div class="kpi-card">
            <div class="kpi-label">Shift Log Volume</div>
            <div class="kpi-value" style="color:var(--text-primary);">{total_logs:,}</div>
            <div class="kpi-sub">Alert logs in active 8h shift</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Global Mean AFI Score</div>
            <div class="kpi-value" style="color:{afi_color};">{mean_afi:.1f} <span style="font-size:14px; color:var(--text-secondary);">/ 100</span></div>
            <div class="kpi-sub">Status: <strong style="color:{afi_color};">{global_state}</strong></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Degradation Anomalies</div>
            <div class="kpi-value" style="color:#dc2626;">{anom_count}</div>
            <div class="kpi-sub">MWU statistical flags (p &lt; 0.05)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Mean Triage Latency</div>
            <div class="kpi-value" style="color:var(--text-primary);">{mean_triage:.0f}s</div>
            <div class="kpi-sub">Log-Normal response time</div>
          </div>
        </div>
        """)
        st.markdown(kpi_html, unsafe_allow_html=True)

        # ── Controls Bar ──────────────────────────────────────
        ctrl_left, ctrl_right = st.columns([4, 1])
        with ctrl_left:
            filtered_analysts = st.multiselect(
                "Select SOC Analyst Roster",
                options=unique_analysts,
                default=unique_analysts,
                help="Filter the active shift cards and telemetry timeline.",
            )
        with ctrl_right:
            auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)

        if not filtered_analysts:
            st.warning("Select at least one analyst to view telemetry.")
            return

        focus_analyst = st.selectbox(
            "Focus Analyst (Detailed Telemetry, Advisory & Forecast)",
            options=filtered_analysts,
            index=0,
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 1 — Active Analysts Shift Status
        # ══════════════════════════════════════════════════════════
        st.markdown('<span class="section-label">Active SOC Roster &ensp;|&ensp; Cognitive Load Gauge</span>', unsafe_allow_html=True)

        col_grid, col_rec = st.columns([3, 1])

        with col_grid:
            card_cols = st.columns(3)
            for i, aid in enumerate(filtered_analysts):
                analyst_logs = scored_df[scored_df["analyst_id"] == aid]
                if analyst_logs.empty:
                    continue
                latest = analyst_logs.sort_values("closure_timestamp").iloc[-1]
                base   = baselines.get(aid, {})
                score  = float(latest["afi_score"])
                state  = _afi_state(score)
                ts_str = pd.to_datetime(latest["closure_timestamp"]).strftime("%H:%M")

                signals = {
                    "triage_interval":        latest["triage_interval"],
                    "enrichment_depth":       latest["enrichment_depth"],
                    "uninvestigated_closures":latest["uninvestigated_closures"],
                    "escalation_deviations":  latest["escalation_deviations"],
                    "hourly_closure_rate":    latest["hourly_closure_rate"],
                }
                with card_cols[i % 3]:
                    render_analyst_card(
                        analyst_id=aid,
                        afi_score=score,
                        state=state,
                        timestamp=ts_str,
                        signals=signals,
                        baseline=base,
                    )

        with col_rec:
            focus_logs = scored_df[scored_df["analyst_id"] == focus_analyst]
            if not focus_logs.empty:
                focus_latest = focus_logs.sort_values("closure_timestamp").iloc[-1]
                focus_score  = float(focus_latest["afi_score"])
                focus_pred   = int(focus_latest.get("risk_pred", 0))

                focus_anom_records: list = []
                if not anomalies_df.empty:
                    fa = anomalies_df[anomalies_df["Analyst"] == focus_analyst].copy()
                    if not fa.empty:
                        fa["closure_dt"] = pd.to_datetime(fa["Timestamp"])
                        fa = fa[fa["closure_dt"] >= shift_start]
                        focus_anom_records = fa.to_dict("records")

                recs = get_advisory_recommendations(
                    afi_score=focus_score,
                    anomalies=focus_anom_records,
                    prediction_flag=focus_pred,
                )
                render_recommendation_panel(
                    analyst_id=focus_analyst,
                    afi_score=focus_score,
                    recommendations=recs,
                )

        # ══════════════════════════════════════════════════════════
        # SECTION 2 — Signal Telemetry Time-Series
        # ══════════════════════════════════════════════════════════
        st.markdown('<span class="section-label">Behavioral Signal Trends &ensp;|&ensp; Rolling 60-Min Window</span>', unsafe_allow_html=True)
        render_signal_charts(
            analyst_id=focus_analyst,
            scored_df=scored_df,
            baseline=baselines.get(focus_analyst, {}),
            anomalies_df=anomalies_df,
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 3 — Degradation Anomaly Audit Log
        # ══════════════════════════════════════════════════════════
        st.markdown('<span class="section-label">Decision Degradation Audit Log &ensp;|&ensp; Mann–Whitney U Test</span>', unsafe_allow_html=True)
        render_anomaly_log(anomalies_df)

        # ══════════════════════════════════════════════════════════
        # SECTION 4 — Predictive Fatigue Risk Forecast
        # ══════════════════════════════════════════════════════════
        st.markdown('<span class="section-label">Predictive Cognitive Risk Forecast &ensp;|&ensp; Machine Learning Model</span>', unsafe_allow_html=True)
        risk_probabilities = (
            scored_df["risk_prob"].values if "risk_prob" in scored_df.columns
            else np.zeros(len(scored_df))
        )
        risk_predictions = (
            scored_df["risk_pred"].values if "risk_pred" in scored_df.columns
            else np.zeros(len(scored_df))
        )
        render_forecast_panel(
            analyst_id=focus_analyst,
            scored_df=scored_df,
            risk_probabilities=risk_probabilities,
            risk_predictions=risk_predictions,
        )

        if auto_refresh:
            time.sleep(60)
            st.rerun()


if __name__ == "__main__":
    main()
