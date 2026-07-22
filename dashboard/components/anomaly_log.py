"""Degradation Anomaly Audit Log component.

Renders a high-contrast clean table matching Microsoft Sentinel & Log360 Cloud design.
Zero emojis, clean typography.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st

_STATE_STYLES: dict[str, tuple[str, str, str]] = {
    "CRITICAL": ("#991b1b", "#fef2f2", "#fca5a5"),
    "HIGH":     ("#b91c1c", "#fef2f2", "#fecaca"),
    "ELEVATED": ("#b45309", "#fffbeb", "#fde68a"),
    "NOMINAL":  ("#047857", "#ecfdf5", "#a7f3d0"),
}

_COLUMNS = ["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _state_badge(state: str) -> str:
    color, bg, border = _STATE_STYLES.get(state, ("#334155", "#f1f5f9", "#cbd5e1"))
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
              <div style="padding:24px 20px; text-align:center; color:#64748b; font-size:13px;">
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
            state, ("#334155", "#f1f5f9", "#cbd5e1")
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
        <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:10px 16px; gap:10px; border-bottom:1px solid #e2e8f0; align-items:center; background:#ffffff; border-left:4px solid {color};">
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#475569;">{row.get("Timestamp", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:#0f172a; font-weight:600;">{row.get("Analyst", "—")}</span>
          <span style="font-family:'Inter',sans-serif; font-size:13px; color:#0f172a;">{row.get("Signal", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:{color}; font-weight:700;">{deviation_str}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:13px; color:#475569;">{pvalue_str}</span>
          <div>{_state_badge(state)}</div>
        </div>
        """
        rows_html += _clean_html(row_item)

    col_header = _clean_html("""
    <div style="display:grid; grid-template-columns:180px 120px 1fr 130px 110px 110px; padding:10px 16px; gap:10px; background:#f1f5f9; border-bottom:1px solid #cbd5e1;">
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">Timestamp</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">Analyst</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">Degradation Signal</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">Deviation (z)</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">p-value</span>
      <span style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:#0f172a;">Severity</span>
    </div>
    """)

    count_label = f"{len(display_df)} anomal{'y' if len(display_df) == 1 else 'ies'} flagged"

    full_table = f"""
    <div class="anomaly-table-wrap">
      <div style="padding:12px 16px; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; background:#ffffff;">
        <span style="font-size:14px; font-weight:600; color:#0f172a;">Flagged Decision Degradation Events</span>
        <span style="font-size:12px; color:#64748b; font-family:'JetBrains Mono',monospace;">{count_label}</span>
      </div>
      {col_header}
      {rows_html}
    </div>
    """
    st.markdown(_clean_html(full_table), unsafe_allow_html=True)
