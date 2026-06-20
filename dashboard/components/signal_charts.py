"""Signal Trend Charts component for the Streamlit dashboard.

Renders line charts using Matplotlib and Seaborn to display rolling window values,
dashed historical baselines, and vertical anomaly indicators, matching the design guide.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import streamlit as st


def render_signal_charts(
    analyst_id: str,
    scored_df: pd.DataFrame,
    baseline: dict[str, float],
    anomalies_df: pd.DataFrame
) -> None:
    """Renders the 5 signal trend charts for a single analyst over the last 8 hours.

    Args:
        analyst_id: Selected analyst to filter data for.
        scored_df: Scored DataFrame containing rolling signal outputs and closure timestamps.
        baseline: Baseline parameters dictionary for the analyst.
        anomalies_df: Flagged anomalies DataFrame to draw vertical indicators.
    """
    # 1. Filter data for the selected analyst
    analyst_data = scored_df[scored_df["analyst_id"] == analyst_id].copy()
    if analyst_data.empty:
        st.warning(f"No signal data available for {analyst_id}.")
        return

    # Convert timestamps to datetime to ensure correct sorting and indexing
    analyst_data["closure_dt"] = pd.to_datetime(analyst_data["closure_timestamp"])
    analyst_data = analyst_data.sort_values(by="closure_dt")

    # Filter for the last 8 hours (active shift)
    max_time = analyst_data["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_data = analyst_data[analyst_data["closure_dt"] >= shift_start].copy()

    if shift_data.empty:
        st.warning(f"No active shift data (last 8 hours) for {analyst_id}.")
        return

    # Filter anomalies for the selected analyst and active shift window
    anom_filtered = anomalies_df[
        (anomalies_df["Analyst"] == analyst_id)
    ].copy()
    if not anom_filtered.empty:
        anom_filtered["closure_dt"] = pd.to_datetime(anom_filtered["Timestamp"])
        anom_filtered = anom_filtered[anom_filtered["closure_dt"] >= shift_start]

    # 2. Define the 5 signals, their titles, baseline key mappings, and help tooltips
    signals_config = [
        {
            "col": "triage_interval",
            "name": "Triage Interval",
            "unit": "s",
            "base_key": "mean_triage_interval",
            "tooltip": "Average time between alert assignment and first analyst action in this window."
        },
        {
            "col": "uninvestigated_closures",
            "name": "Uninvestigated Closures",
            "unit": "ratio",
            "base_key": "mean_uninvestigated_closures",
            "tooltip": "Alerts closed without enrichment steps or notes recorded."
        },
        {
            "col": "enrichment_depth",
            "name": "Enrichment Depth",
            "unit": "actions",
            "base_key": "mean_enrichment_depth",
            "tooltip": "Average number of enrichment actions taken per alert in this window."
        },
        {
            "col": "escalation_deviations",
            "name": "Escalation Deviations",
            "unit": "ratio",
            "base_key": None,  # Center is 0 by definition
            "base_val": 0.0,
            "tooltip": "How far this analyst's escalation rate has drifted from their 30-day norm."
        },
        {
            "col": "hourly_closure_rate",
            "name": "Hourly Closure Rate",
            "unit": "ratio",
            "base_key": None,  # Nominal ratio centered at 1.0
            "base_val": 1.0,
            "tooltip": "Alerts closed per hour compared to this analyst's baseline rate."
        }
    ]

    # Create tabs for each signal chart to save screen space and match high-fidelity layout
    signal_names = [cfg["name"] for cfg in signals_config]
    tabs = st.tabs(signal_names)

    # 3. Render charts inside tabs
    # Theme colors mapped to matplotlib hex
    bg_surface = "#161B22"
    border_subtle = "#30363D"
    chart_1 = "#58A6FF"       # Active rolling value
    text_secondary = "#8B949E" # Baseline line
    state_high = "#F78166"     # Anomalies indicator
    text_primary = "#E6EDF3"

    for i, tab in enumerate(tabs):
        cfg = signals_config[i]
        col_name = cfg["col"]
        sig_name = cfg["name"]
        sig_unit = cfg["unit"]
        
        # Get baseline value
        if cfg["base_key"] is not None:
            baseline_val = baseline.get(cfg["base_key"], 0.0)
        else:
            baseline_val = cfg["base_val"]

        with tab:
            st.caption(f"**Description:** {cfg['tooltip']}")
            
            # Setup matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 3.5), facecolor=bg_surface)
            ax.set_facecolor(bg_surface)

            # Plot rolling window data
            x_vals = shift_data["closure_dt"]
            y_vals = shift_data[col_name]
            
            ax.plot(
                x_vals, y_vals,
                color=chart_1,
                linewidth=2,
                label=f"Rolling Window ({sig_name})"
            )

            # Plot baseline line
            ax.axhline(
                y=baseline_val,
                color=text_secondary,
                linestyle="--",
                linewidth=1.5,
                label=f"30-day baseline ({baseline_val:.2f} {sig_unit})"
            )

            # Highlight anomalies with vertical dotted lines
            if not anom_filtered.empty:
                # Filter anomalies specific to this signal
                # Note: Currently degradation anomalies are specifically calculated on Enrichment Depth,
                # but we can filter or show them.
                sig_anomalies = anom_filtered[anom_filtered["Signal"].str.lower().str.contains(sig_name.split()[0].lower())]
                for _, anom in sig_anomalies.iterrows():
                    ax.axvline(
                        x=anom["closure_dt"],
                        color=state_high,
                        linestyle=":",
                        linewidth=1.5,
                        alpha=0.8
                    )
                    # Put a small dot at the anomaly location on the line
                    matching_points = shift_data[shift_data["closure_dt"] == anom["closure_dt"]]
                    if not matching_points.empty:
                        ax.scatter(
                            matching_points["closure_dt"],
                            matching_points[col_name],
                            color=state_high,
                            s=40,
                            zorder=5
                        )

            # Chart Title
            title_text = f"{sig_name} · {analyst_id} · Last 8h"
            ax.set_title(title_text, color=text_primary, fontsize=12, fontweight="bold", pad=15)

            # Styling axes
            ax.tick_params(colors=text_secondary, labelsize=9)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(border_subtle)
            ax.spines["bottom"].set_color(border_subtle)
            
            # Format X-axis timestamps to monospace HH:MM
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: pd.to_datetime(x).strftime("%H:%M")))
            
            # Label axes
            ax.set_ylabel(sig_unit, color=text_secondary, fontsize=9)
            ax.grid(color=border_subtle, linestyle="-", linewidth=0.5, alpha=0.4)
            
            # Legend
            legend = ax.legend(
                loc="upper left",
                facecolor=bg_surface,
                edgecolor=border_subtle,
                fontsize=8
            )
            for text in legend.get_texts():
                text.set_color(text_primary)

            # Render to Streamlit and clean up
            st.pyplot(fig)
            plt.close(fig)
