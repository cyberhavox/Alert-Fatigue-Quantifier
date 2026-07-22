"""Signal Trend Charts component formatted with Stripi Design Language.

Renders line charts using Matplotlib to display rolling window values,
dashed historical baselines, and vertical anomaly indicators. Zero emojis.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st


def render_signal_charts(
    analyst_id: str,
    scored_df: pd.DataFrame,
    baseline: dict[str, float],
    anomalies_df: pd.DataFrame
) -> None:
    """Renders the 5 signal trend charts for a single analyst over the last 8 hours."""
    analyst_data = scored_df[scored_df["analyst_id"] == analyst_id].copy()
    if analyst_data.empty:
        st.warning(f"No signal data available for {analyst_id}.")
        return

    analyst_data["closure_dt"] = pd.to_datetime(analyst_data["closure_timestamp"])
    analyst_data = analyst_data.sort_values(by="closure_dt")

    max_time = analyst_data["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_data = analyst_data[analyst_data["closure_dt"] >= shift_start].copy()

    if shift_data.empty:
        st.warning(f"No active shift data (last 8 hours) for {analyst_id}.")
        return

    anom_filtered = anomalies_df[
        (anomalies_df["Analyst"] == analyst_id)
    ].copy()
    if not anom_filtered.empty:
        anom_filtered["closure_dt"] = pd.to_datetime(anom_filtered["Timestamp"])
        anom_filtered = anom_filtered[anom_filtered["closure_dt"] >= shift_start]

    signals_config = [
        {
            "col": "triage_interval",
            "name": "Triage Interval",
            "unit": "seconds",
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
            "base_key": None,
            "base_val": 0.0,
            "tooltip": "How far this analyst's escalation rate has drifted from their 30-day norm."
        },
        {
            "col": "hourly_closure_rate",
            "name": "Hourly Closure Rate",
            "unit": "ratio",
            "base_key": None,
            "base_val": 1.0,
            "tooltip": "Alerts closed per hour compared to this analyst's baseline rate."
        }
    ]

    signal_names = [cfg["name"] for cfg in signals_config]
    tabs = st.tabs(signal_names)

    # Sleek Dark Palette
    bg_surface = "#141936"
    border_subtle = "#1f264e"
    chart_1 = "#665efd"        # Stripi Indigo
    text_secondary = "#94a3b8"  # Slate Muted Text
    state_high = "#f43f5e"      # Neon Coral Red
    text_primary = "#f8fafc"    # Crisp Off-White

    for i, tab in enumerate(tabs):
        cfg = signals_config[i]
        col_name = cfg["col"]
        sig_name = cfg["name"]
        sig_unit = cfg["unit"]
        
        if cfg["base_key"] is not None:
            baseline_val = baseline.get(cfg["base_key"], 0.0)
        else:
            baseline_val = cfg["base_val"]

        with tab:
            st.caption(f"Parameter: {cfg['tooltip']}")
            
            fig, ax = plt.subplots(figsize=(10, 3.2), facecolor=bg_surface)
            ax.set_facecolor(bg_surface)

            x_vals = shift_data["closure_dt"]
            y_vals = shift_data[col_name]
            
            # Subtle area fill
            ax.fill_between(x_vals, y_vals, color=chart_1, alpha=0.1)

            # Main signal line
            ax.plot(
                x_vals, y_vals,
                color=chart_1,
                linewidth=2.2,
                label=f"Rolling Window ({sig_name})"
            )

            # Baseline horizontal line
            ax.axhline(
                y=baseline_val,
                color=text_secondary,
                linestyle="--",
                linewidth=1.2,
                alpha=0.7,
                label=f"30-day baseline ({baseline_val:.2f} {sig_unit})"
            )

            if not anom_filtered.empty:
                sig_anomalies = anom_filtered[anom_filtered["Signal"].str.lower().str.contains(sig_name.split()[0].lower())]
                for _, anom in sig_anomalies.iterrows():
                    ax.axvline(
                        x=anom["closure_dt"],
                        color=state_high,
                        linestyle=":",
                        linewidth=1.5,
                        alpha=0.8
                    )
                    matching_points = shift_data[shift_data["closure_dt"] == anom["closure_dt"]]
                    if not matching_points.empty:
                        ax.scatter(
                            matching_points["closure_dt"],
                            matching_points[col_name],
                            color=state_high,
                            s=45,
                            zorder=5
                        )

            title_text = f"{sig_name} — {analyst_id} — Active Shift"
            ax.set_title(title_text, color=text_primary, fontsize=10, fontweight="500", pad=10)

            ax.tick_params(colors=text_secondary, labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(border_subtle)
            ax.spines["bottom"].set_color(border_subtle)
            
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: pd.to_datetime(x).strftime("%H:%M")))
            
            ax.set_ylabel(sig_unit, color=text_secondary, fontsize=8)
            ax.grid(color=border_subtle, linestyle="-", linewidth=0.5, alpha=0.5)
            
            legend = ax.legend(
                loc="upper left",
                facecolor=bg_surface,
                edgecolor=border_subtle,
                fontsize=8,
                framealpha=0.9
            )
            for text in legend.get_texts():
                text.set_color(text_primary)

            plt.tight_layout(pad=0.4)
            st.pyplot(fig)
            plt.close(fig)
