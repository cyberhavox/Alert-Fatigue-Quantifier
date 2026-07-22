"""Predictive Fatigue Risk Forecast panel — Stripi Design Language.

Renders ML-derived fatigue risk metrics and rolling probability timeline chart.
Uses custom HTML for metric display and Matplotlib with Stripi palette for the chart.
Zero emojis, plain engineering voice.
"""

from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import streamlit as st

_BG_SURFACE   = "#1c1e54"
_BG_ELEVATED  = "#242b5e"
_BORDER       = "#2a3060"
_TEXT_PRIMARY = "#f6f9fc"
_TEXT_MUTED   = "#64748d"
_TEXT_SEC     = "#a8c3de"
_COLOR_INDIGO = "#533afd"   # primary CTA — used for nominal risk line
_COLOR_RUBY   = "#ea2261"   # ruby — elevated/high risk line
_COLOR_AMBER  = "#f59e0b"   # elevated
_COLOR_TEAL   = "#00c896"   # nominal state


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit from rendering raw HTML as markdown code blocks."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _risk_color(pred: int, prob: float) -> str:
    """Returns the appropriate line color based on risk prediction and probability."""
    if pred == 1:
        return _COLOR_RUBY
    if prob >= 0.35:
        return _COLOR_AMBER
    return _COLOR_INDIGO


def render_forecast_panel(
    analyst_id: str,
    scored_df: pd.DataFrame,
    risk_probabilities: np.ndarray,
    risk_predictions: np.ndarray,
) -> None:
    """Renders the ML fatigue risk forecast for the focus analyst."""
    analyst_mask = scored_df["analyst_id"] == analyst_id
    analyst_data = scored_df[analyst_mask].copy()

    if analyst_data.empty or len(risk_probabilities) != len(scored_df):
        html = _clean_html("""
            <div class="forecast-wrap">
              <div style="padding:24px; text-align:center; color:var(--text-muted); font-size:13px; font-weight:300;">
                Predictive model requires calibrated baseline data.
                Run <code>python scripts/run_full_pipeline.py</code> to generate forecasts.
              </div>
            </div>
        """)
        st.markdown(html, unsafe_allow_html=True)
        return

    analyst_data["risk_prob"] = risk_probabilities[analyst_mask]
    analyst_data["risk_pred"] = risk_predictions[analyst_mask]
    analyst_data["closure_dt"] = pd.to_datetime(analyst_data["closure_timestamp"])
    analyst_data = analyst_data.sort_values("closure_dt")

    max_time    = analyst_data["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_data  = analyst_data[analyst_data["closure_dt"] >= shift_start].copy()

    if shift_data.empty:
        st.warning("Insufficient shift data for ML forecast.")
        return

    latest    = shift_data.iloc[-1]
    curr_prob = float(latest["risk_prob"])
    curr_pred = int(latest["risk_pred"])
    prob_pct  = curr_prob * 100.0

    risk_color  = _risk_color(curr_pred, curr_prob)
    alert_bg    = "rgba(234, 34, 97, 0.10)"   if curr_pred == 1 else "rgba(0, 200, 150, 0.08)"
    alert_border= _COLOR_RUBY                 if curr_pred == 1 else _COLOR_TEAL
    alert_label = "Elevated Risk"             if curr_pred == 1 else "Nominal Risk"
    alert_body  = (
        "High probability of fatigue crossing threshold limits. "
        "Queue rebalancing and workload redistribution recommended."
        if curr_pred == 1
        else
        "Model projects low fatigue risk for upcoming alerts in the current shift cycle."
    )

    n_at_risk  = int((shift_data["risk_pred"] == 1).sum())
    total_recs = len(shift_data)
    at_risk_pct = (n_at_risk / total_recs * 100.0) if total_recs > 0 else 0.0

    forecast_html = _clean_html(f"""
    <div class="forecast-wrap">
      <div class="forecast-metric-row">
        <div class="forecast-metric-primary">
          <div class="forecast-metric-label">Fatigue Probability</div>
          <div class="forecast-metric-value" style="color:{risk_color};">{prob_pct:.1f}<span style="font-size:20px; color:var(--text-muted);">%</span></div>
        </div>
        <div class="forecast-metric-primary">
          <div class="forecast-metric-label">At-Risk Intervals (shift)</div>
          <div class="forecast-metric-value" style="color:var(--text-primary); font-size:28px;">{n_at_risk}<span style="font-size:13px; color:var(--text-muted);">/ {total_recs}</span></div>
        </div>
        <div class="forecast-metric-primary">
          <div class="forecast-metric-label">At-Risk Exposure</div>
          <div class="forecast-metric-value" style="color:var(--text-primary); font-size:28px;">{at_risk_pct:.0f}<span style="font-size:16px; color:var(--text-muted);">%</span></div>
        </div>
        <div class="forecast-alert-box" style="background:{alert_bg}; border-left:3px solid {alert_border};">
          <div style="font-size:11px; font-weight:500; text-transform:uppercase; letter-spacing:0.6px; color:{alert_border}; margin-bottom:5px;">{alert_label}</div>
          <div style="font-size:13px; font-weight:300; color:var(--text-secondary);">{alert_body}</div>
        </div>
      </div>
    </div>
    """)
    st.markdown(forecast_html, unsafe_allow_html=True)

    line_color = _risk_color(curr_pred, curr_prob)

    fig, ax = plt.subplots(figsize=(11, 3.2), facecolor=_BG_SURFACE)
    ax.set_facecolor(_BG_SURFACE)

    x = shift_data["closure_dt"]
    y = shift_data["risk_prob"] * 100.0

    ax.fill_between(x, y, alpha=0.08, color=line_color)
    ax.plot(x, y, color=line_color, linewidth=2.0, label="Predicted Risk Probability (%)")
    ax.axhline(y=50.0, color=_TEXT_MUTED, linestyle="--", linewidth=1.0, label="Classification threshold — 50%", alpha=0.6)

    ax.set_ylim(-2, 105)
    ax.set_title(f"Rolling Fatigue Risk Probability Timeline — {analyst_id}", color=_TEXT_PRIMARY, fontsize=10, fontweight="normal", fontfamily="monospace", pad=10)
    ax.tick_params(colors=_TEXT_SEC, labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(_BORDER)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_ylabel("Risk %", color=_TEXT_MUTED, fontsize=8)
    ax.grid(axis="y", color=_BORDER, linestyle="-", linewidth=0.5, alpha=0.4)
    ax.grid(axis="x", visible=False)

    legend = ax.legend(loc="upper left", facecolor=_BG_ELEVATED, edgecolor=_BORDER, fontsize=8, framealpha=1)
    for txt in legend.get_texts():
        txt.set_color(_TEXT_SEC)

    plt.tight_layout(pad=0.5)
    st.pyplot(fig)
    plt.close(fig)
