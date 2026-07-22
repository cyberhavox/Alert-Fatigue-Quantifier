"""Degradation Anomaly Audit Log component — Stripi Design Language.

Renders a custom HTML table with per-row severity highlighting
and tabular-figure monospace numerics. Zero emojis.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st

_STATE_STYLES: dict[str, tuple[str, str, str]] = {
    "CRITICAL": ("#ea2261", "rgba(234, 34, 97, 0.12)",  "rgba(234, 34, 97, 0.30)"),
    "HIGH":     ("#f87171", "rgba(248, 113, 113, 0.10)", "rgba(248, 113, 113, 0.25)"),
    "ELEVATED": ("#f59e0b", "rgba(245, 158, 11, 0.10)",  "rgba(245, 158, 11, 0.25)"),
    "NOMINAL":  ("#00c896", "rgba(0, 200, 150, 0.08)",   "rgba(0, 200, 150, 0.20)"),
}

_COLUMNS = ["Timestamp", "Analyst", "Signal", "Deviation", "p-value", "State"]


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit from rendering raw HTML as markdown code blocks."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def _state_badge(state: str) -> str:
    color, bg, border = _STATE_STYLES.get(state, ("#adbdcc", "rgba(173,189,204,0.1)", "rgba(173,189,204,0.2)"))
    return (
        f'<span style="display:inline-block; padding:2px 8px; border-radius:9999px; '
        f'font-size:10px; font-weight:500; letter-spacing:0.5px; text-transform:uppercase; '
        f'font-family:\'Inter\',sans-serif; background:{bg}; color:{color}; border:1px solid {border};">'
        f"{state}</span>"
    )


def render_anomaly_log(anomalies_df: pd.DataFrame) -> None:
    """Renders the degradation anomaly audit log as a styled HTML table."""
    if anomalies_df.empty:
        html = _clean_html("""
            <div class="anomaly-table-wrap">
              <div class="anomaly-empty">
                No operational degradation anomalies in the active monitoring window.
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
            state, ("#adbdcc", "rgba(173,189,204,0.05)", "rgba(173,189,204,0.15)")
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
        <div style="display:grid; grid-template-columns:170px 110px 1fr 120px 100px 110px; padding:10px 16px; gap:8px; border-bottom:1px solid rgba(255,255,255,0.04); align-items:center; background:{bg}; border-left:3px solid {color};">
          <span style="font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--text-muted); font-feature-settings:'tnum' 1;">{row.get("Timestamp", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-primary); font-feature-settings:'tnum' 1; font-weight:500;">{row.get("Analyst", "—")}</span>
          <span style="font-family:'Inter',sans-serif; font-size:12px; color:var(--text-secondary); font-weight:300;">{row.get("Signal", "—")}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:{color}; font-feature-settings:'tnum' 1;">{deviation_str}</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--text-secondary); font-feature-settings:'tnum' 1;">{pvalue_str}</span>
          <div>{_state_badge(state)}</div>
        </div>
        """
        rows_html += _clean_html(row_item)

    col_header = _clean_html("""
    <div style="display:grid; grid-template-columns:170px 110px 1fr 120px 100px 110px; padding:10px 16px; gap:8px; background:rgba(255,255,255,0.04); border-bottom:1px solid var(--border-subtle);">
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">Timestamp</span>
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">Analyst</span>
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">Signal</span>
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">Deviation (z)</span>
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">p-value</span>
      <span style="font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted);">State</span>
    </div>
    """)

    count_label = f"{len(display_df)} anomal{'y' if len(display_df) == 1 else 'ies'} detected"

    full_table = f"""
    <div class="anomaly-table-wrap">
      <div style="padding:12px 16px 10px; border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:13px; font-weight:400; color:var(--text-primary);">Degradation Events</span>
        <span style="font-size:11px; color:var(--text-muted); font-family:'JetBrains Mono',monospace;">{count_label}</span>
      </div>
      {col_header}
      {rows_html}
    </div>
    """
    st.markdown(_clean_html(full_table), unsafe_allow_html=True)
