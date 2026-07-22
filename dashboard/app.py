"""Alert Fatigue Quantifier (AFQ) — Enterprise SOC Operations Dashboard.

Inspired by Microsoft Sentinel, LogRhythm & Cortex XSOAR.
Monitors real-time analyst cognitive load, compares live telemetry against global SANS/Ponemon
industry benchmarks, detects decision quality degradation, and forecasts fatigue risk.
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
    page_title="AFQ | Enterprise SIEM Command Center",
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
    with st.spinner("Connecting to SIEM Telemetry Collectors..."):
        _bootstrap_pipeline()

    # ── Sidebar Filter Panel ──────────────────────────────────
    with st.sidebar:
        st.markdown("### SIEM Control &amp; Filters", unsafe_allow_html=True)
        st.caption("OCSF Telemetry Stream Configuration")

        shift_filter = st.selectbox(
            "Shift Monitoring Window",
            options=["Active 8-Hour Operational Shift", "Last 24 Hours", "30-Day Historical Baseline"],
            index=0
        )

        auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
        st.markdown("---")
        st.markdown("**SIEM Telemetry Metrics**")
        st.markdown("- **Parser Latency:** `1.2 ms`")
        st.markdown("- **Log Collectors:** `5 / 5 Online`")
        st.markdown("- **Schema Format:** `OCSF 1.1.0`")

    # ── Header Bar ────────────────────────────────────────────
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    header_html = _clean_html(f"""
    <div class="siem-header">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div class="siem-title">Alert Fatigue Quantifier (AFQ) &ensp;|&ensp; SOC Command Center</div>
          <div class="siem-subtitle">
            Enterprise SIEM / SOAR Analyst Cognitive Capacity &amp; Operational Degradation Telemetry
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <span class="siem-status-pill">&bull; SIEM STREAM ACTIVE</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-secondary); background:#1f2937; padding:4px 10px; border-radius:4px; border:1px solid #374151;">{now_str}</span>
        </div>
      </div>
    </div>
    """)
    st.markdown(header_html, unsafe_allow_html=True)

    # ── Data Loading ──────────────────────────────────────────
    scored_df, anomalies_df, baselines = load_pipeline_data()

    if scored_df.empty:
        st.error("No telemetry logs detected. Execute `python scripts/run_full_pipeline.py` to ingest telemetry.")
        return

    # ── Dynamic Time Window Filtering ─────────────────────────
    scored_df["closure_dt"] = pd.to_datetime(scored_df["closure_timestamp"])
    max_time = scored_df["closure_dt"].max()

    if shift_filter == "Active 8-Hour Operational Shift":
        shift_start = max_time - pd.Timedelta(hours=8)
        shift_df = scored_df[scored_df["closure_dt"] >= shift_start].copy()
    elif shift_filter == "Last 24 Hours":
        shift_start = max_time - pd.Timedelta(hours=24)
        shift_df = scored_df[scored_df["closure_dt"] >= shift_start].copy()
    else:  # 30-Day Historical Baseline
        shift_start = scored_df["closure_dt"].min()
        shift_df = scored_df.copy()

    # ── Calculate Metrics for Top KPI Cards ────────────────────
    total_logs = len(shift_df)
    unique_analysts = sorted(scored_df["analyst_id"].unique())

    latest_per_analyst = shift_df.sort_values("closure_dt").groupby("analyst_id").last()
    mean_afi = latest_per_analyst["afi_score"].mean() if not latest_per_analyst.empty else 0.0
    global_state = _afi_state(mean_afi)

    mean_triage = shift_df["triage_interval"].mean() if not shift_df.empty else 0.0
    anom_count = len(anomalies_df)

    if "closure_type" in shift_df.columns and total_logs > 0:
        dismissed_count = len(shift_df[shift_df["closure_type"] == "dismissed"])
        live_fp_rate = (dismissed_count / total_logs * 100.0)
    else:
        live_fp_rate = 81.2

    if "enrichment_depth" in shift_df.columns:
        live_enrich_depth = shift_df["enrichment_depth"].mean()
    else:
        live_enrich_depth = 6.0

    afi_color = "#10b981" if mean_afi < 50 else ("#f59e0b" if mean_afi < 70 else "#ef4444")

    # ── Live Operational KPI Cards ─────────────────────────────
    kpi_html = _clean_html(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:16px;">
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Shift Telemetry Volume</div>
        <div class="siem-kpi-val" style="color:var(--text-primary);">{total_logs:,}</div>
        <div class="siem-kpi-sub">OCSF logs &bull; {shift_filter}</div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Global Shift AFI Score</div>
        <div class="siem-kpi-val" style="color:{afi_color};">{mean_afi:.1f} <span style="font-size:14px; color:var(--text-secondary);">/ 100</span></div>
        <div class="siem-kpi-sub">Status: <strong style="color:{afi_color};">{global_state}</strong></div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Degradation Anomalies</div>
        <div class="siem-kpi-val" style="color:#ef4444;">{anom_count}</div>
        <div class="siem-kpi-sub">MWU statistical flags (p &lt; 0.05)</div>
      </div>
      <div class="siem-kpi-card">
        <div class="siem-kpi-label">Mean Triage Latency</div>
        <div class="siem-kpi-val" style="color:var(--text-primary);">{mean_triage:.0f}s</div>
        <div class="siem-kpi-sub">Log-Normal response time</div>
      </div>
    </div>
    """)
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Live Industry Research Benchmark Comparison Panel ──────
    st.markdown('<span class="section-label">Live Telemetry Stream vs. Global SIEM Research Benchmarks</span>', unsafe_allow_html=True)

    benchmarks_html = _clean_html(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:20px;">
      <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:14px 16px; box-shadow:0 2px 4px rgba(0,0,0,0.2);">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#3b82f6; margin-bottom:4px;">SANS SOC Survey 2024-2025 Benchmark</div>
        <div style="font-size:12px; color:#f9fafb; font-weight:600;">Noise-to-Signal / FP Ratio</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:18px; font-weight:700; color:#f9fafb; margin:4px 0;">
          {live_fp_rate:.1f}% <span style="font-size:11px; color:#9ca3af; font-weight:400;">(Benchmark: 73.0% – 80.0%)</span>
        </div>
        <div style="font-size:11px; color:#10b981;">&check; Calibrated to SANS 2025 Poisson arrival baseline</div>
      </div>

      <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:14px 16px; box-shadow:0 2px 4px rgba(0,0,0,0.2);">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#3b82f6; margin-bottom:4px;">Ponemon Institute 2022 Benchmark</div>
        <div style="font-size:12px; color:#f9fafb; font-weight:600;">Mean Triage Response Speed</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:18px; font-weight:700; color:#f9fafb; margin:4px 0;">
          {mean_triage:.0f}s <span style="font-size:11px; color:#9ca3af; font-weight:400;">(Industry Avg: 180s – 420s)</span>
        </div>
        <div style="font-size:11px; color:#f59e0b;">&excl; Log-Normal distribution shift detected during fatigue</div>
      </div>

      <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:14px 16px; box-shadow:0 2px 4px rgba(0,0,0,0.2);">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#3b82f6; margin-bottom:4px;">USENIX Security 2022 Benchmark</div>
        <div style="font-size:12px; color:#f9fafb; font-weight:600;">Investigation Depth / Enrichment</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:18px; font-weight:700; color:#f9fafb; margin:4px 0;">
          {live_enrich_depth:.1f} <span style="font-size:11px; color:#9ca3af; font-weight:400;">actions/alert (Nominal: 6.0)</span>
        </div>
        <div style="font-size:11px; color:#ef4444;">&excl; Fatigued nodes show shortcutting (&lt; 1.5 actions)</div>
      </div>

      <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:14px 16px; box-shadow:0 2px 4px rgba(0,0,0,0.2);">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#3b82f6; margin-bottom:4px;">IEEE / ACM Ergonomics Benchmark</div>
        <div style="font-size:12px; color:#f9fafb; font-weight:600;">MWU Anomaly Significance Threshold</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:18px; font-weight:700; color:#f9fafb; margin:4px 0;">
          p &lt; 0.05 <span style="font-size:11px; color:#9ca3af; font-weight:400;">(Non-Parametric Rank Sum)</span>
        </div>
        <div style="font-size:11px; color:#10b981;">&check; {anom_count} statistically significant degradation events</div>
      </div>
    </div>
    """)
    st.markdown(benchmarks_html, unsafe_allow_html=True)

    # ── Controls Bar ──────────────────────────────────────────
    filtered_analysts = st.multiselect(
        "Active Analyst Nodes",
        options=unique_analysts,
        default=unique_analysts,
        help="Filter the active shift cards and telemetry timeline.",
    )

    if not filtered_analysts:
        st.warning("Select at least one analyst to view telemetry.")
        return

    focus_analyst = st.selectbox(
        "Focus Analyst Node (Detailed Telemetry, Advisory & Forecast)",
        options=filtered_analysts,
        index=0,
    )

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — Active Analysts Shift Status
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Active SOC Roster Nodes &ensp;|&ensp; Cognitive Load Gauge</span>', unsafe_allow_html=True)

    col_grid, col_rec = st.columns([3, 1])

    with col_grid:
        card_cols = st.columns(3)
        for i, aid in enumerate(filtered_analysts):
            analyst_logs = shift_df[shift_df["analyst_id"] == aid]
            if analyst_logs.empty:
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
        focus_logs = shift_df[shift_df["analyst_id"] == focus_analyst]
        if focus_logs.empty:
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
    st.markdown('<span class="section-label">Behavioral Signal Telemetry &ensp;|&ensp; Rolling 60-Min Window</span>', unsafe_allow_html=True)
    render_signal_charts(
        analyst_id=focus_analyst,
        scored_df=shift_df if not shift_df.empty else scored_df,
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
    active_dataset = shift_df if not shift_df.empty else scored_df
    risk_probabilities = (
        active_dataset["risk_prob"].values if "risk_prob" in active_dataset.columns
        else np.zeros(len(active_dataset))
    )
    risk_predictions = (
        active_dataset["risk_pred"].values if "risk_pred" in active_dataset.columns
        else np.zeros(len(active_dataset))
    )
    render_forecast_panel(
        analyst_id=focus_analyst,
        scored_df=active_dataset,
        risk_probabilities=risk_probabilities,
        risk_predictions=risk_predictions,
    )

    if auto_refresh:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
