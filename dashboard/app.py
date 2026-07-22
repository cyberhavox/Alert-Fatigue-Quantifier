"""Alert Fatigue Quantifier — SIEM/SOAR Command Center Dashboard.

Orchestrates data loading, KPI ribbon rendering, shift-status grid,
advisory panel, signal telemetry charts, anomaly audit log, and predictive forecast.
Zero emojis, professional SOC engineering voice.
"""

from __future__ import annotations
import os
import sys
import time
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

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Alert Fatigue Quantifier | SIEM SOC Command Center",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS Theme Injection ───────────────────────────────────────
_theme_path = os.path.join(WORKSPACE_ROOT, "dashboard", "styles", "theme.css")
if os.path.exists(_theme_path):
    with open(_theme_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering."""
    return "".join([line.strip() for line in raw_html.split("\n")])


# ── Streamlit Cloud Bootstrap ─────────────────────────────────
@st.cache_resource
def _bootstrap_pipeline() -> bool:
    """Generates synthetic data and runs pipeline if scored_alerts.csv is missing."""
    scored_path = os.path.join(WORKSPACE_ROOT, "data", "output", "scored_alerts.csv")
    if os.path.exists(scored_path):
        return True

    import subprocess
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
    """Loads scored alerts, anomalies, and per-analyst baselines."""
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
    # ── Cloud Auto-Bootstrap ──────────────────────────────────
    with st.spinner("Initializing SIEM Telemetry Engine..."):
        _bootstrap_pipeline()

    # ── SIEM SOC Command Header ───────────────────────────────
    now_str = datetime.now().strftime("%H:%M:%S UTC")
    header_html = _clean_html(f"""
    <div class="siem-header">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div class="siem-eyebrow">CYBERHAVOX // SOC COMMAND CENTER — SIEM/SOAR INTEGRATION</div>
          <h1 class="siem-title">Alert Fatigue Quantifier</h1>
          <div class="siem-subtitle">Real-Time Cognitive Load &amp; Operational Degradation Monitoring for Security Analysts</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
          <span class="siem-status-pill">SIEM INGESTION: ONLINE</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--text-muted);">{now_str}</span>
        </div>
      </div>
    </div>
    """)
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Load Data ─────────────────────────────────────────────
    scored_df, anomalies_df, baselines = load_pipeline_data()

    if scored_df.empty:
        st.info("No SIEM alert logs detected. Running telemetry pipeline...")
        return

    # ── SIEM KPI Ribbon Summary ───────────────────────────────
    total_alerts = len(scored_df)
    n_analysts   = len(scored_df["analyst_id"].unique())
    avg_afi      = float(scored_df["afi_score"].mean()) if "afi_score" in scored_df.columns else 0.0
    n_anomalies  = len(anomalies_df)

    kpi_html = _clean_html(f"""
    <div class="siem-kpi-ribbon">
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Ingested Shift Alerts</div>
        <div class="siem-kpi-val">{total_alerts:,}</div>
        <div class="siem-kpi-sub">SIEM log stream (30-day window)</div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Active Analyst Roster</div>
        <div class="siem-kpi-val">{n_analysts}</div>
        <div class="siem-kpi-sub">Monitoring 5 SOC Tiers</div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">SOC Average AFI</div>
        <div class="siem-kpi-val" style="color: {'#fbbf24' if avg_afi >= 60 else '#34d399'};">{avg_afi:.1f}</div>
        <div class="siem-kpi-sub">Composite Cognitive Score</div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Degradation Anomalies</div>
        <div class="siem-kpi-val" style="color: {'#f87171' if n_anomalies > 0 else '#34d399'};">{n_anomalies}</div>
        <div class="siem-kpi-sub">Mann-Whitney U (p &lt; 0.05)</div>
      </div>
    </div>
    """)
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Command Controls ──────────────────────────────────────
    unique_analysts = sorted(scored_df["analyst_id"].unique())

    ctrl_left, ctrl_right = st.columns([4, 1])
    with ctrl_left:
        filtered_analysts = st.multiselect(
            "SOC Analyst Roster Filter",
            options=unique_analysts,
            default=unique_analysts,
            help="Filter live telemetry grid across SOC team members.",
        )
    with ctrl_right:
        auto_refresh = st.checkbox("Auto-refresh (60 s)", value=False)

    if not filtered_analysts:
        st.warning("Select at least one analyst to display SIEM telemetry.")
        return

    focus_analyst = st.selectbox(
        "Focus Analyst Console — Deep Telemetry, SOAR Advisory & Predictive Risk",
        options=filtered_analysts,
        index=0,
    )

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — Analyst Console Grid & SOAR Advisory
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">SOC Analyst Shift Status Grid</span>', unsafe_allow_html=True)

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

            max_time    = pd.to_datetime(scored_df["closure_timestamp"]).max()
            shift_start = max_time - pd.Timedelta(hours=8)

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
    # SECTION 2 — Telemetry Signal Time-Series
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Signal Telemetry Trends — Active Shift</span>', unsafe_allow_html=True)
    render_signal_charts(
        analyst_id=focus_analyst,
        scored_df=scored_df,
        baseline=baselines.get(focus_analyst, {}),
        anomalies_df=anomalies_df,
    )

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — SIEM Degradation Anomaly Audit Trail
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Degradation Anomaly Audit Log</span>', unsafe_allow_html=True)
    render_anomaly_log(anomalies_df)

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — Predictive Fatigue Risk Forecast
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Predictive Fatigue Risk Forecast</span>', unsafe_allow_html=True)
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

    # ── Auto-Refresh ──────────────────────────────────────────
    if auto_refresh:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
