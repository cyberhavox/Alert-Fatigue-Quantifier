"""Analyst Card component for the Streamlit dashboard.

Renders an information-dense, visually styled card representing the fatigue state
of a single SOC analyst, complete with custom CSS styling and signal deltas.
"""

import streamlit as st
import textwrap


def render_analyst_card(
    analyst_id: str,
    afi_score: float,
    state: str,
    timestamp: str,
    signals: dict[str, float],
    baseline: dict[str, float]
) -> None:
    """Renders a single analyst's status card.

    Args:
        analyst_id: Unique identifier for the analyst.
        afi_score: Composite Analyst Fatigue Index score (0 to 100).
        state: Severity state (NOMINAL, ELEVATED, HIGH, CRITICAL).
        timestamp: Time when the scores were last computed.
        signals: Current rolling 60-minute window signals.
        baseline: Historical baseline values for the analyst.
    """
    # 1. Map state to CSS classes and colors
    state_cls = f"card-{state.lower()}"
    badge_cls = f"badge-{state.lower()}"
    
    # Color variables matching theme.css
    color_map = {
        "NOMINAL": "#3FB950",
        "ELEVATED": "#D29922",
        "HIGH": "#F78166",
        "CRITICAL": "#FF4444"
    }
    state_color = color_map.get(state, "#E6EDF3")

    # 2. Compute signal deltas
    # Triage Interval
    curr_triage = signals.get("triage_interval", 0.0)
    base_triage = baseline.get("mean_triage_interval", 180.0)
    triage_delta = ((curr_triage - base_triage) / base_triage * 100.0) if base_triage > 0 else 0.0

    # Enrichment Depth
    curr_enrich = signals.get("enrichment_depth", 0.0)
    base_enrich = baseline.get("mean_enrichment_depth", 6.0)
    enrich_delta = ((curr_enrich - base_enrich) / base_enrich * 100.0) if base_enrich > 0 else 0.0

    # 3. Format delta strings
    triage_symbol = "↑" if triage_delta >= 0 else "↓"
    triage_sign = "+" if triage_delta >= 0 else ""
    triage_delta_str = f"{triage_symbol} Triage {triage_sign}{triage_delta:.0f}%"

    enrich_symbol = "↑" if enrich_delta >= 0 else "↓"
    enrich_sign = "+" if enrich_delta >= 0 else ""
    enrich_delta_str = f"{enrich_symbol} Enrich {enrich_sign}{enrich_delta:.0f}%"

    # Colorize deltas (Triage increase is bad/amber/red, Enrich decrease is bad/amber/red)
    triage_color = "#F78166" if triage_delta > 15.0 else ("#3FB950" if triage_delta < -5.0 else "#8B949E")
    enrich_color = "#F78166" if enrich_delta < -15.0 else ("#3FB950" if enrich_delta > 5.0 else "#8B949E")

    # 4. Render Card HTML
    card_html = f"""
    <div class="analyst-card {state_cls}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span class="badge {badge_cls}">● {state}</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-secondary);">{timestamp}</span>
        </div>
        <div style="font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">
            {analyst_id}
        </div>
        <div style="display: flex; align-items: baseline; margin-bottom: 4px;">
            <span class="monospace-val" style="font-size: 48px; font-weight: 700; color: {state_color}; line-height: 1;">
                {afi_score:.0f}
            </span>
            <span style="font-size: 13px; color: var(--text-secondary); margin-left: 6px;">out of 100</span>
        </div>
        
        <!-- Custom Progress Bar -->
        <div style="background-color: var(--bg-input); border-radius: 4px; height: 6px; width: 100%; margin-bottom: 16px; overflow: hidden;">
            <div style="background-color: {state_color}; width: {afi_score}%; height: 100%;"></div>
        </div>
        
        <!-- Signal Deltas -->
        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 500;">
            <span style="color: {triage_color};">{triage_delta_str}</span>
            <span style="color: {enrich_color};">{enrich_delta_str}</span>
        </div>
    </div>
    """
    st.markdown(textwrap.dedent(card_html), unsafe_allow_html=True)
