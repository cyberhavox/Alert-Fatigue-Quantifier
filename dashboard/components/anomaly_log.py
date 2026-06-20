"""Anomaly Log component for the Streamlit dashboard.

Displays statistical degradation outcomes in a high-fidelity tabular view,
using Pandas Styler to highlight rows with elevated/critical severity.
"""

import pandas as pd
import streamlit as st


def render_anomaly_log(anomalies_df: pd.DataFrame) -> None:
    """Renders the degradation anomaly log panel.

    Args:
        anomalies_df: DataFrame of flagged degradation anomalies containing columns:
                      ['Timestamp', 'Analyst', 'Signal', 'Deviation', 'p-value', 'State']
    """
    st.markdown('<div class="section-header">Degradation Anomaly Log</div>', unsafe_allow_html=True)

    # 1. Handle Empty State
    if anomalies_df.empty:
        st.markdown(
            '<p style="color: var(--text-secondary); font-size: 13px; font-style: italic;">'
            'No degradation anomalies in the current window.</p>',
            unsafe_allow_html=True
        )
        return

    # Sort to show most recent first
    display_df = anomalies_df.sort_values(by="Timestamp", ascending=False).copy()

    # Rename columns for presentation
    display_df.columns = ["Timestamp", "Analyst ID", "Signal Type", "Deviation (z-score)", "p-value", "State"]

    # 2. Styling function for rows
    def highlight_by_state(row: pd.Series) -> list[str]:
        state = row["State"]
        if state == "CRITICAL":
            # 15% opacity critical red
            return ["background-color: rgba(255, 68, 68, 0.15); border-left: 3px solid var(--state-critical);"] * len(row)
        elif state == "HIGH":
            # 8% opacity coral-red
            return ["background-color: rgba(247, 129, 102, 0.08); border-left: 3px solid var(--state-high);"] * len(row)
        elif state == "ELEVATED":
            # 8% opacity amber
            return ["background-color: rgba(210, 153, 34, 0.08); border-left: 3px solid var(--state-elevated);"] * len(row)
        return [""] * len(row)

    # 3. Render dataframe with styling
    styled_df = display_df.style.apply(highlight_by_state, axis=1)
    
    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Timestamp": st.column_config.TextColumn(
                "Timestamp",
                help="Time of the anomaly event in ISO 8601 format."
            ),
            "Analyst ID": st.column_config.TextColumn(
                "Analyst ID",
                help="Unique identifier of the SOC analyst."
            ),
            "Signal Type": st.column_config.TextColumn(
                "Signal Type",
                help="The metric showing significant performance degradation."
            ),
            "Deviation (z-score)": st.column_config.NumberColumn(
                "Deviation (z-score)",
                format="%.2f",
                help="Standard deviations from the analyst's historical 30-day baseline mean."
            ),
            "p-value": st.column_config.NumberColumn(
                "p-value",
                format="%.4f",
                help="Asymptotic p-value from two-sided Mann-Whitney U test (significant if < 0.05)."
            ),
            "State": st.column_config.TextColumn(
                "State",
                help="Severity of the detected degradation anomaly."
            ),
        }
    )
