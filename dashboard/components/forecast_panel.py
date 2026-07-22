"""Predictive Fatigue Risk Forecast panel.

Renders ML-derived fatigue risk metrics and rolling probability timeline chart.
Uses high-contrast clean HTML metrics and Matplotlib plot matching SIEM Dark theme.
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

_BG_SURFACE   = "#111827"   # Slate 900 Card Surface
_BORDER       = "#1f2937"   # Dark Steel Border
_TEXT_PRIMARY = "#f9fafb"   # Crisp White Text
_TEXT_MUTED   = "#6b7280"   # Medium Gray
_TEXT_SEC     = "#9ca3af"   # Light Slate Text
_COLOR_BLUE   = "#3b82f6"   # Sentinel Blue
_COLOR_RED    = "#ef4444"   # Red 500
_COLOR_AMBER  = "#f59e0b"   # Amber 500
_COLOR_EMERALD= "#10b981"   # Emerald 500


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _risk_color(pred: int, prob: float) -> str:
    if pred == 1:
        return _COLOR_RED
    if prob >= 0.35:
        return _COLOR_AMBER
    return _COLOR_BLUE


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
              <div style="padding:24px; text-align:center; color:#9ca3af; font-size:13px;">
                Predictive model requires calibrated baseline data. Execute <code>python scripts/run_full_pipeline.py</code>.
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
    alert_bg    = "rgba(239, 68, 68, 0.12)" if curr_pred == 1 else "rgba(16, 185, 129, 0.12)"
    alert_border= _COLOR_RED if curr_pred == 1 else _COLOR_EMERALD
    alert_label = "ELEVATED FATIGUE RISK PREDICTED" if curr_pred == 1 else "NOMINAL FATIGUE RISK FORECAST"
    alert_body  = (
        "High probability of fatigue crossing threshold limits. Queue rebalancing recommended."
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
          <div class="forecast-metric-label">Predicted Risk Probability</div>
          <div class="forecast-metric-value" style="color:{risk_color};">{prob_pct:.1f}<span style="font-size:20px; color:#9ca3af;">%</span></div>
        </div>
        <div class="forecast-metric-primary">
          <div class="forecast-metric-label">At-Risk Intervals (Shift)</div>
          <div class="forecast-metric-value" style="color:#f9fafb; font-size:32px;">{n_at_risk}<span style="font-size:14px; color:#9ca3af;"> / {total_recs}</span></div>
        </div>
        <div class="forecast-metric-primary">
          <div class="forecast-metric-label">At-Risk Exposure Ratio</div>
          <div class="forecast-metric-value" style="color:#f9fafb; font-size:32px;">{at_risk_pct:.0f}<span style="font-size:18px; color:#9ca3af;">%</span></div>
        </div>
        <div class="forecast-alert-box" style="background:{alert_bg}; border:1px solid {alert_border}; border-left:4px solid {alert_border};">
          <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:{alert_border}; margin-bottom:6px;">{alert_label}</div>
          <div style="font-size:13px; color:#f9fafb;">{alert_body}</div>
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

    ax.fill_between(x, y, alpha=0.10, color=line_color)
    ax.plot(x, y, color=line_color, linewidth=2.2, label="Predicted Risk Probability (%)")
    ax.axhline(y=50.0, color=_TEXT_SEC, linestyle="--", linewidth=1.2, label="Classification Threshold (50%)", alpha=0.85)

    ax.set_ylim(-2, 105)
    ax.set_title(f"Rolling Fatigue Risk Probability Timeline — Analyst: {analyst_id}", color=_TEXT_PRIMARY, fontsize=11, fontweight="bold", pad=10)
    ax.tick_params(colors=_TEXT_SEC, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(_BORDER)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(_BORDER)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_ylabel("Risk %", color=_TEXT_SEC, fontsize=9)
    ax.grid(axis="y", color=_BORDER, linestyle="-", linewidth=0.7, alpha=0.8)
    ax.grid(axis="x", visible=False)

    legend = ax.legend(loc="upper left", facecolor=_BG_SURFACE, edgecolor=_BORDER, fontsize=8.5, framealpha=1.0)
    for txt in legend.get_texts():
        txt.set_color(_TEXT_PRIMARY)

    plt.tight_layout(pad=0.4)
    st.pyplot(fig)
    plt.close(fig)
