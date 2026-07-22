"""Degradation Anomaly Audit Log component.

Renders a high-contrast clean table matching Microsoft Sentinel Dark & LogRhythm design.
Zero emojis, clean SIEM monospace log formatting.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st

_STATE_STYLES: dict[str, tuple[str, str, str]] = {
    "CRITICAL": ("#f87171", "rgba(220, 38, 38, 0.2)", "rgba(220, 38, 38, 0.4)"),
    "HIGH":     ("#ef4444", "rgba(239, 68, 68, 0.15)", "rgba(239, 68, 68, 0.3)"),
    "ELEVATED": ("#f59e0b", "rgba(245, 158, 11, 0.15)", "rgba(245, 158, 11, 0.3)"),
    "NOMINAL":  ("#10b981", "rgba(16, 185, 129, 0.15)", "rgba(16, 185, 129, 0.3)"),
}

_COLUMNS = ["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _state_badge(state: str) -> str:
    color, bg, border = _STATE_STYLES.get(state, ("#9ca3af", "#1f2937", "#374151"))
    return (
        f'<span style="display:inline-block; padding:3px 9px; border-radius:4px; '
        f'font-size:11px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase; '
        f'font-family:\'JetBrains Mono\',monospace; background:{bg}; color:{color}; border:1px solid {border};">'
        f"{state}</span>"
    )


def render_anomaly_log(anomalies_df: pd.DataFrame) -> None:
    """Renders the degradation anomaly audit log as a clean table."""
    if anomalies_df.empty:
        html = _clean_html("""
            <div class="anomaly-table-wrap">
              <div style="padding:24px 20px; text-align:center; color:#9ca3af; font-size:13px;">
                No operational degradation anomalies detected in active telemetry window.
              </div>
            </div>
        """)
        st.markdown(html, unsafe_allow_html=True)
        return

    display_df = anomalies_df.sort_values("Timestamp", ascending=False).copy()
    for col in _COLUMNS:
        if col not in display_df.columns:
            display_df[col] = "—"

    rows_html = ""
    for _, row in display_df.iterrows():
        state = str(row.get("State", "")).upper()
        color, bg, border = _STATE_STYLES.get(
            state, ("#9ca3af", "#1f2937", "#374151")
        )
        deviation = row.get("Deviation", 0)
        pvalue    = row.get("p-value", 0)
        try:
            deviation_str = f"{float(deviation):+.2f} σ"
        except (ValueError, TypeError):
            deviation_str = str(deviation)
        try:
            pvalue_str = f"{float(pvalue):.4f}"
        except (ValueError, TypeError):
            pvalue_str = str(pvalue)

        row_item = f"""
        <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:10px 16px; gap:10px; border-bottom:1px solid #1f2937; align-items:center; background:#111827; border-left:4px solid {color};">
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#9ca3af;">{row.get("Timestamp", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:#f9fafb; font-weight:600;">{row.get("Analyst", "—")}</span>
          <span style="font-family:'Inter',sans-serif; font-size:13px; color:#f9fafb;">{row.get("Signal", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:{color}; font-weight:700;">{deviation_str}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:#9ca3af;">{pvalue_str}</span>
          <div>{_state_badge(state)}</div>
        </div>
        """
        rows_html += _clean_html(row_item)

    col_header = _clean_html("""
    <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:10px 16px; gap:10px; background:#1f2937; border-bottom:1px solid #374151;">
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">Timestamp</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">Analyst Node</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">Degradation Telemetry Signal</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">Deviation (z)</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">p-value</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f9fafb;">Severity</span>
    </div>
    """)

    count_label = f"{len(display_df)} anomal{'y' if len(display_df) == 1 else 'ies'} flagged"

    full_table = f"""
    <div class="anomaly-table-wrap">
      <div style="padding:12px 16px; border-bottom:1px solid #1f2937; display:flex; justify-content:space-between; align-items:center; background:#111827;">
        <span style="font-size:13px; font-weight:600; color:#f9fafb; font-family:'Inter',sans-serif;">Flagged Decision Degradation Events (Mann-Whitney U Test)</span>
        <span style="font-size:12px; color:#9ca3af; font-family:'JetBrains Mono',monospace;">{count_label}</span>
      </div>
      {col_header}
      {rows_html}
    </div>
    """
    st.markdown(_clean_html(full_table), unsafe_allow_html=True)
