"""Alert Fatigue Quantifier — Enterprise SOC Command Center Dashboard.

Orchestrates SIEM alert telemetry, cognitive load monitoring, statistical degradation,
and predictive machine learning risk forecasting for SOC management.
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

# ── Page Configuration ───────────────────────────────────────
st.set_page_config(
    page_title="SOC Command Center | Alert Fatigue Quantifier",
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
    """Strips multiline indentation to prevent Streamlit from rendering raw HTML as codeblocks."""
    return "".join([line.strip() for line in raw_html.split("\n")])


@st.cache_resource
def _bootstrap_pipeline() -> bool:
    """Runs pipeline once on startup if output files do not exist."""
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
    """Loads scored alerts, degradation anomalies, and per-analyst baselines."""
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
    with st.spinner("Initializing SOC Telemetry Pipeline..."):
        _bootstrap_pipeline()

    # ── SIEM Command Center Header ────────────────────────────
    now_str = datetime.now().strftime("%H:%M:%S UTC")
    header_html = _clean_html(f"""
    <div class="afq-header">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
            <div class="afq-header-title">SOC Command Center &ensp;|&ensp; Alert Fatigue Quantifier</div>
          </div>
          <div class="afq-header-subtitle">
            Enterprise Cognitive Capacity &amp; Behavioral Degradation Engine &ensp;&bull;&ensp; Real-Time Advisory Mode
          </div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="afq-header-live">SIEM INGEST ACTIVE</span>
            <span style="font-size:10px; padding:3px 8px; border-radius:4px; background:rgba(255,255,255,0.06); color:var(--text-secondary); font-family:'JetBrains Mono',monospace;">SHIFT ALPHA</span>
          </div>
          <span style="font-size:11px; color:var(--text-muted); font-family:'JetBrains Mono',monospace;">{now_str}</span>
        </div>
      </div>
    </div>
    """)
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Data Loading ──────────────────────────────────────────
    scored_df, anomalies_df, baselines = load_pipeline_data()

    if scored_df.empty:
        st.info("No telemetry logs ingested. Run `python scripts/run_full_pipeline.py` to start telemetry engine.")
        return

    # Filter data for current 8-hour shift
    scored_df["closure_dt"] = pd.to_datetime(scored_df["closure_timestamp"])
    max_time = scored_df["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_df = scored_df[scored_df["closure_dt"] >= shift_start].copy()

    # ── Enterprise KPI Overview Strip ─────────────────────────
    total_logs = len(shift_df)
    unique_analysts = sorted(scored_df["analyst_id"].unique())
    
    # Calculate global shift metrics
    latest_per_analyst = shift_df.sort_values("closure_dt").groupby("analyst_id").last()
    mean_afi = latest_per_analyst["afi_score"].mean() if not latest_per_analyst.empty else 0.0
    global_state = _afi_state(mean_afi)
    
    mean_triage = shift_df["triage_interval"].mean() if not shift_df.empty else 0.0
    anom_count = len(anomalies_df)

    kpi_color = "#10b981" if mean_afi < 50 else ("#f59e0b" if mean_afi < 70 else "#f43f5e")

    kpi_html = _clean_html(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:24px;">
      <div style="background:rgba(20,25,54,0.85); backdrop-filter:blur(12px); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:16px 20px; box-shadow:var(--shadow-card);">
        <div style="font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:6px;">Active Shift Ingestion</div>
        <div style="font-size:28px; font-weight:300; font-family:'JetBrains Mono',monospace; color:var(--text-primary);">{total_logs:,}<span style="font-size:13px; color:var(--text-muted); margin-left:6px;">logs</span></div>
        <div style="font-size:11px; color:var(--text-secondary); margin-top:4px;">Poisson λ = 15-28 alerts/hr</div>
      </div>
      <div style="background:rgba(20,25,54,0.85); backdrop-filter:blur(12px); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:16px 20px; box-shadow:var(--shadow-card);">
        <div style="font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:6px;">Global Shift Fatigue Index</div>
        <div style="font-size:28px; font-weight:300; font-family:'JetBrains Mono',monospace; color:{kpi_color};">{mean_afi:.1f}<span style="font-size:13px; color:var(--text-muted); margin-left:6px;">/ 100 AFI</span></div>
        <div style="font-size:11px; color:var(--text-secondary); margin-top:4px;">Shift Status: <strong style="color:{kpi_color};">{global_state}</strong></div>
      </div>
      <div style="background:rgba(20,25,54,0.85); backdrop-filter:blur(12px); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:16px 20px; box-shadow:var(--shadow-card);">
        <div style="font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:6px;">Degradation Events (MWU)</div>
        <div style="font-size:28px; font-weight:300; font-family:'JetBrains Mono',monospace; color:#f43f5e;">{anom_count}<span style="font-size:13px; color:var(--text-muted); margin-left:6px;">anomalies</span></div>
        <div style="font-size:11px; color:var(--text-secondary); margin-top:4px;">p-value &lt; 0.05 vs baseline</div>
      </div>
      <div style="background:rgba(20,25,54,0.85); backdrop-filter:blur(12px); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:16px 20px; box-shadow:var(--shadow-card);">
        <div style="font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:6px;">Mean Triage Latency</div>
        <div style="font-size:28px; font-weight:300; font-family:'JetBrains Mono',monospace; color:var(--text-primary);">{mean_triage:.0f}<span style="font-size:13px; color:var(--text-muted); margin-left:6px;">sec</span></div>
        <div style="font-size:11px; color:var(--text-secondary); margin-top:4px;">Log-Normal Distribution</div>
      </div>
    </div>
    """)
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Controls Bar ──────────────────────────────────────────
    ctrl_left, ctrl_right = st.columns([4, 1])
    with ctrl_left:
        filtered_analysts = st.multiselect(
            "Filter SOC Analyst Roster",
            options=unique_analysts,
            default=unique_analysts,
            help="Filter the active shift status grid and signal charts.",
        )
    with ctrl_right:
        auto_refresh = st.checkbox("SIEM Live Sync (60s)", value=False)

    if not filtered_analysts:
        st.warning("Select at least one analyst to display telemetry.")
        return

    focus_analyst = st.selectbox(
        "Focus Analyst (Detailed Telemetry, Advisory & Forecast)",
        options=filtered_analysts,
        index=0,
    )

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — Active SOC Analysts Shift Status + Advisory
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Active SOC Roster &ensp;|&ensp; Shift Cognitive Load</span>', unsafe_allow_html=True)

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
    # SECTION 2 — Signal Telemetry Trends
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">SIEM Behavioral Signal Trends &ensp;|&ensp; Rolling 60-Min Window</span>', unsafe_allow_html=True)
    render_signal_charts(
        analyst_id=focus_analyst,
        scored_df=scored_df,
        baseline=baselines.get(focus_analyst, {}),
        anomalies_df=anomalies_df,
    )

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — Degradation Anomaly Audit Log
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Decision Degradation Audit Log &ensp;|&ensp; Mann–Whitney U Non-Parametric Test</span>', unsafe_allow_html=True)
    render_anomaly_log(anomalies_df)

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — Predictive Fatigue Risk Forecast
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Predictive Cognitive Risk Forecast &ensp;|&ensp; Random Forest Classifier</span>', unsafe_allow_html=True)
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

    # ── Auto-refresh ──────────────────────────────────────────
    if auto_refresh:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
