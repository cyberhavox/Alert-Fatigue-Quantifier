"""Analyst Card component — Stripi Design Language.

Renders a single analyst's real-time fatigue state card:
AFI score gauge, severity badge, signal delta row, and progress bar.
Uses new theme.css tokens. Zero emojis, engineering voice.
"""

from __future__ import annotations
import streamlit as st


_STATE_COLORS: dict[str, str] = {
    "NOMINAL":  "#00c896",
    "ELEVATED": "#f59e0b",
    "HIGH":     "#f87171",
    "CRITICAL": "#ea2261",
}


def render_analyst_card(
    analyst_id: str,
    afi_score: float,
    state: str,
    timestamp: str,
    signals: dict[str, float],
    baseline: dict[str, float],
) -> None:
    """Renders a single analyst status card.

    Args:
        analyst_id: Unique analyst identifier (e.g. "ANL-003").
        afi_score: Composite Alert Fatigue Index (0–100).
        state: Severity string — NOMINAL | ELEVATED | HIGH | CRITICAL.
        timestamp: Last computation timestamp formatted as HH:MM.
        signals: Rolling 60-minute window signal values.
        baseline: Historical 30-day baseline stats for the analyst.
    """
    state_cls   = f"card-{state.lower()}"
    badge_cls   = f"badge-{state.lower()}"
    state_color = _STATE_COLORS.get(state, "#f6f9fc")

    # Signal deltas (vs 30-day baseline)
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

    # Delta colors: triage up is bad; enrich up is good
    triage_color = "#f87171" if triage_delta > 15.0 else ("#00c896" if triage_delta < -5.0 else "#a8c3de")
    enrich_color = "#f87171" if enrich_delta < -15.0 else ("#00c896" if enrich_delta > 5.0 else "#a8c3de")

    # Uninvestigated closures indicator
    uninvest = float(signals.get("uninvestigated_closures", 0.0))
    uninvest_pct = uninvest * 100.0
    uninvest_color = (
        "#ea2261" if uninvest_pct > 20.0
        else ("#f59e0b" if uninvest_pct > 10.0 else "#a8c3de")
    )

    card_html = f"""
    <div class="analyst-card {state_cls}">
      <!-- Row 1: Badge + Timestamp -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span class="badge {badge_cls}">{state}</span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:10px;
                     color:var(--text-muted); font-feature-settings:'tnum' 1; letter-spacing:0.4px;">
          {timestamp}
        </span>
      </div>

      <!-- Row 2: Analyst ID -->
      <div style="font-size:15px; font-weight:400; color:var(--text-primary);
                  margin-bottom:8px; letter-spacing:-0.2px;">
        {analyst_id}
      </div>

      <!-- Row 3: AFI Score large display -->
      <div style="display:flex; align-items:baseline; margin-bottom:4px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:44px; font-weight:400;
                     color:{state_color}; line-height:1; letter-spacing:-2px;
                     font-feature-settings:'tnum' 1;">
          {afi_score:.0f}
        </span>
        <span style="font-size:13px; color:var(--text-muted); margin-left:5px; font-weight:300;">
          / 100 AFI
        </span>
      </div>

      <!-- Row 4: Progress bar -->
      <div class="afq-progress-track">
        <div class="afq-progress-fill" style="background:{state_color}; width:{min(afi_score, 100):.0f}%;"></div>
      </div>

      <!-- Row 5: Signal deltas -->
      <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px;
                     color:{triage_color}; font-feature-settings:'tnum' 1;">
          {triage_str}
        </span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px;
                     color:{enrich_color}; font-feature-settings:'tnum' 1;">
          {enrich_str}
        </span>
      </div>

      <!-- Row 6: Uninvestigated closures micro-bar -->
      <div style="border-top:1px solid rgba(255,255,255,0.06); padding-top:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
          <span style="font-size:10px; color:var(--text-muted); font-weight:400;
                       text-transform:uppercase; letter-spacing:0.6px;">
            Uninvestigated Closures
          </span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:10px;
                       color:{uninvest_color}; font-feature-settings:'tnum' 1;">
            {uninvest_pct:.1f}%
          </span>
        </div>
        <div style="background:rgba(255,255,255,0.06); border-radius:2px; height:3px; overflow:hidden;">
          <div style="background:{uninvest_color}; height:100%;
                      width:{min(uninvest_pct, 100):.1f}%; border-radius:2px;"></div>
        </div>
      </div>
    </div>
    """
    # Collapse newlines to avoid Streamlit rendering issues
    clean_html = " ".join(card_html.split())
    st.markdown(clean_html, unsafe_allow_html=True)
