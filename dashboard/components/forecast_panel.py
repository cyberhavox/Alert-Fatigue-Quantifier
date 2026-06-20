"""Forecast Panel component for the Streamlit dashboard.

Renders upcoming machine learning fatigue risk forecasts, displaying risk probabilities,
classification outcomes, and a rolling timeline chart of forecasted risk levels.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st


def render_forecast_panel(
    analyst_id: str,
    scored_df: pd.DataFrame,
    risk_probabilities: np.ndarray,
    risk_predictions: np.ndarray
) -> None:
    """Renders the machine learning fatigue risk forecast panel for the selected analyst.

    Args:
        analyst_id: The selected analyst ID.
        scored_df: The scored DataFrame (same length as the predictions arrays).
        risk_probabilities: Array of predicted probability of fatigue (AFI > 70).
        risk_predictions: Array of binary predictions (0 or 1).
    """
    st.markdown('<div class="section-header">Predictive Fatigue Forecast (ML)</div>', unsafe_allow_html=True)

    # 1. Filter and prepare data
    analyst_mask = scored_df["analyst_id"] == analyst_id
    analyst_data = scored_df[analyst_mask].copy()
    
    if analyst_data.empty or len(risk_probabilities) != len(scored_df):
        st.markdown(
            '<p style="color: var(--text-secondary); font-size: 13px; font-style: italic;">'
            'Predictive model requires baseline data. Run baseline calibration first.</p>',
            unsafe_allow_html=True
        )
        return

    # Add predictions to the local copy
    analyst_data["risk_prob"] = risk_probabilities[analyst_mask]
    analyst_data["risk_pred"] = risk_predictions[analyst_mask]
    analyst_data["closure_dt"] = pd.to_datetime(analyst_data["closure_timestamp"])
    analyst_data = analyst_data.sort_values(by="closure_dt")

    # Filter for active shift (last 8 hours)
    max_time = analyst_data["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_data = analyst_data[analyst_data["closure_dt"] >= shift_start].copy()

    if shift_data.empty:
        st.warning("No recent shift data to generate ML forecast.")
        return

    # 2. Display current risk metrics
    latest_record = shift_data.iloc[-1]
    curr_prob = float(latest_record["risk_prob"]) * 100.0
    curr_pred = int(latest_record["risk_pred"])

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(
            label="Fatigue Probability",
            value=f"{curr_prob:.1f}%",
            delta="High Risk" if curr_pred == 1 else "Nominal Risk",
            delta_color="inverse" if curr_pred == 1 else "normal"
        )
        
    with col2:
        if curr_pred == 1:
            st.markdown(
                '<div style="background-color: rgba(255, 68, 68, 0.1); border-left: 4px solid var(--state-critical); padding: 10px; border-radius: 4px; font-size: 12px; margin-top: 5px;">'
                '<strong style="color: var(--state-critical);">[!] Proactive Alert:</strong> High likelihood of '
                'fatigue crossing standard thresholds. Queue mitigation suggested.'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background-color: rgba(63, 185, 80, 0.1); border-left: 4px solid var(--state-nominal); padding: 10px; border-radius: 4px; font-size: 12px; margin-top: 5px;">'
                '<strong style="color: var(--state-nominal);">[i] Stable Trend:</strong> Model predicts low '
                'fatigue risk for the upcoming alerts in the current cycle.'
                '</div>',
                unsafe_allow_html=True
            )

    # 3. Plot the rolling risk probability chart
    bg_surface = "#161B22"
    border_subtle = "#30363D"
    chart_color = "#F78166" if curr_pred == 1 else "#58A6FF"
    text_secondary = "#8B949E"
    text_primary = "#E6EDF3"

    fig, ax = plt.subplots(figsize=(10, 3), facecolor=bg_surface)
    ax.set_facecolor(bg_surface)

    # Plot rolling risk probability
    ax.plot(
        shift_data["closure_dt"],
        shift_data["risk_prob"] * 100.0,
        color=chart_color,
        linewidth=2,
        label="ML Forecasted Risk %"
    )

    # Threshold line at 50%
    ax.axhline(
        y=50.0,
        color=text_secondary,
        linestyle=":",
        linewidth=1.2,
        label="Risk Classification Threshold (50%)"
    )

    # Title & Labels
    ax.set_title("Rolling Fatigue Risk Probability Timeline", color=text_primary, fontsize=10, fontweight="bold", pad=10)
    ax.tick_params(colors=text_secondary, labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(border_subtle)
    ax.spines["bottom"].set_color(border_subtle)
    
    # Format X-axis
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: pd.to_datetime(x).strftime("%H:%M")))
    ax.set_ylabel("Risk %", color=text_secondary, fontsize=8)
    ax.grid(color=border_subtle, linestyle="-", linewidth=0.5, alpha=0.3)
    ax.set_ylim(-5, 105)

    # Legend
    legend = ax.legend(
        loc="lower left",
        facecolor=bg_surface,
        edgecolor=border_subtle,
        fontsize=8
    )
    for text in legend.get_texts():
        text.set_color(text_primary)

    st.pyplot(fig)
    plt.close(fig)
