"""Analyst Card component.

Renders a single analyst's real-time fatigue state card:
AFI score gauge, severity badge, signal delta row, and progress bar.
High contrast formatting for Slate dark theme. Zero emojis.
"""

from __future__ import annotations
import streamlit as st


_STATE_COLORS: dict[str, str] = {
    "NOMINAL":  "#10b981",
    "ELEVATED": "#f59e0b",
    "HIGH":     "#ef4444",
    "CRITICAL": "#dc2626",
}


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def render_analyst_card(
    analyst_id: str,
    afi_score: float,
    state: str,
    timestamp: str,
    signals: dict[str, float],
    baseline: dict[str, float],
) -> None:
    """Renders a single analyst status card."""
    state_cls   = f"card-{state.lower()}"
    badge_cls   = f"badge-{state.lower()}"
    state_color = _STATE_COLORS.get(state, "#f8fafc")

    curr_triage = signals.get("triage_interval", 0.0)
    base_triage = baseline.get("mean_triage_interval", 180.0)
    triage_delta = ((curr_triage - base_triage) / base_triage * 100.0) if base_triage > 0 else 0.0

    curr_enrich = signals.get("enrichment_depth", 0.0)
    base_enrich = baseline.get("mean_enrichment_depth", 6.0)
    enrich_delta = ((curr_enrich - base_enrich) / base_enrich * 100.0) if base_enrich > 0 else 0.0

    triage_sign  = "+" if triage_delta >= 0 else ""
    enrich_sign  = "+" if enrich_delta >= 0 else ""
    triage_str   = f"Triage {triage_sign}{triage_delta:.0f}%"
    enrich_str   = f"Enrich {enrich_sign}{enrich_delta:.0f}%"

    triage_color = "#ef4444" if triage_delta > 15.0 else ("#10b981" if triage_delta < -5.0 else "#cbd5e1")
    enrich_color = "#ef4444" if enrich_delta < -15.0 else ("#10b981" if enrich_delta > 5.0 else "#cbd5e1")

    uninvest = float(signals.get("uninvestigated_closures", 0.0))
    uninvest_pct = uninvest * 100.0
    uninvest_color = (
        "#ef4444" if uninvest_pct > 20.0
        else ("#f59e0b" if uninvest_pct > 10.0 else "#cbd5e1")
    )

    card_html = _clean_html(f"""
    <div class="analyst-card {state_cls}">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span class="badge {badge_cls}">{state}</span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--text-secondary);">{timestamp}</span>
      </div>

      <div style="font-size:16px; font-weight:600; color:var(--text-primary); margin-bottom:8px;">
        {analyst_id}
      </div>

      <div style="display:flex; align-items:baseline; margin-bottom:6px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:42px; font-weight:700; color:{state_color}; line-height:1;">
          {afi_score:.0f}
        </span>
        <span style="font-size:13px; color:var(--text-secondary); margin-left:6px; font-weight:500;">
          / 100 AFI
        </span>
      </div>

      <div class="afq-progress-track">
        <div class="afq-progress-fill" style="background:{state_color}; width:{min(afi_score, 100):.0f}%;"></div>
      </div>

      <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:{triage_color}; font-weight:600;">{triage_str}</span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:{enrich_color}; font-weight:600;">{enrich_str}</span>
      </div>

      <div style="border-top:1px solid #334155; padding-top:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <span style="font-size:11px; color:var(--text-secondary); font-weight:500;">Uninvestigated Closures</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:11px; color:{uninvest_color}; font-weight:600;">{uninvest_pct:.1f}%</span>
        </div>
        <div style="background:#334155; border-radius:2px; height:4px; overflow:hidden;">
          <div style="background:{uninvest_color}; height:100%; width:{min(uninvest_pct, 100):.1f}%; border-radius:2px;"></div>
        </div>
      </div>
    </div>
    """)
    st.markdown(card_html, unsafe_allow_html=True)
