"""Degradation Anomaly Audit Log component.

Renders a high-contrast HTML table with per-row severity highlighting
and tabular-figure monospace numerics. Zero emojis.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st

_STATE_STYLES: dict[str, tuple[str, str, str]] = {
    "CRITICAL": ("#ef4444", "rgba(239, 68, 68, 0.15)",  "#ef4444"),
    "HIGH":     ("#ef4444", "rgba(239, 68, 68, 0.10)",  "#ef4444"),
    "ELEVATED": ("#f59e0b", "rgba(245, 158, 11, 0.10)",  "#f59e0b"),
    "NOMINAL":  ("#10b981", "rgba(16, 185, 129, 0.10)",  "#10b981"),
}

_COLUMNS = ["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _state_badge(state: str) -> str:
    color, bg, border = _STATE_STYLES.get(state, ("#cbd5e1", "rgba(203,213,225,0.1)", "#cbd5e1"))
    return (
        f'<span style="display:inline-block; padding:3px 10px; border-radius:4px; '
        f'font-size:11px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase; '
        f'font-family:\'JetBrains Mono\',monospace; background:{bg}; color:{color}; border:1px solid {border};">'
        f"{state}</span>"
    )


def render_anomaly_log(anomalies_df: pd.DataFrame) -> None:
    """Renders the degradation anomaly audit log as a high-contrast table."""
    if anomalies_df.empty:
        html = _clean_html("""
            <div class="anomaly-table-wrap">
              <div style="padding:28px 20px; text-align:center; color:var(--text-muted); font-size:13px;">
                No operational degradation anomalies detected in active monitoring window.
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
            state, ("#cbd5e1", "rgba(203,213,225,0.05)", "#cbd5e1")
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
        <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:12px 18px; gap:10px; border-bottom:1px solid #334155; align-items:center; background:var(--bg-surface); border-left:4px solid {color};">
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-secondary);">{row.get("Timestamp", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--text-primary); font-weight:600;">{row.get("Analyst", "—")}</span>
          <span style="font-family:'Inter',sans-serif; font-size:13px; color:var(--text-primary);">{row.get("Signal", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:{color}; font-weight:600;">{deviation_str}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--text-secondary);">{pvalue_str}</span>
          <div>{_state_badge(state)}</div>
        </div>
        """
        rows_html += _clean_html(row_item)

    col_header = _clean_html("""
    <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:12px 18px; gap:10px; background:#334155; border-bottom:1px solid #475569;">
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">Timestamp</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">Analyst</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">Degradation Signal</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">Deviation (z)</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">p-value</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#f8fafc;">Severity</span>
    </div>
    """)

    count_label = f"{len(display_df)} anomal{'y' if len(display_df) == 1 else 'ies'} flagged"

    full_table = f"""
    <div class="anomaly-table-wrap">
      <div style="padding:14px 18px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:14px; font-weight:600; color:var(--text-primary);">Flagged Decision Degradation Events</span>
        <span style="font-size:12px; color:var(--text-muted); font-family:'JetBrains Mono',monospace;">{count_label}</span>
      </div>
      {col_header}
      {rows_html}
    </div>
    """
    st.markdown(_clean_html(full_table), unsafe_allow_html=True)
