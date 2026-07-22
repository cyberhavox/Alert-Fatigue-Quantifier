"""Recommendation Panel component formatted with Stripe Design Language.

Renders advisory suggestions sidebar panel, showing recommended mitigations,
warning triggers, and persistent safety disclaimer. Zero emojis.
"""

import streamlit as st


def render_recommendation_panel(
    analyst_id: str,
    afi_score: float,
    recommendations: dict
) -> None:
    """Renders the advisory recommendations panel in the sidebar/right column.

    Args:
        analyst_id: Selected analyst identifier.
        afi_score: Analyst Fatigue Index score.
        recommendations: Dictionary containing mapping output from the advisory engine.
    """
    st.markdown('<div class="section-header">Advisory Guidance</div>', unsafe_allow_html=True)

    state = recommendations.get("state", "NOMINAL")
    primary_rec = recommendations.get("primary_recommendation", "")
    actions = recommendations.get("actions", [])
    warnings = recommendations.get("warnings", [])
    disclaimer = recommendations.get("disclaimer", "All recommendations are advisory. Operational decisions rest with SOC management.")

    color_map = {
        "NOMINAL": "#00d4b2",
        "ELEVATED": "#ffc043",
        "HIGH": "#ff5b60",
        "CRITICAL": "#ea2261"
    }
    state_color = color_map.get(state, "#ffffff")
    badge_cls = f"badge-{state.lower()}"

    rec_html = f"""
    <div class="recommendation-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-subtle);">
            <span style="font-weight: 600; font-size: 13px; color: var(--text-primary);">{analyst_id}</span>
            <span class="badge {badge_cls}">AFI {afi_score:.0f}</span>
        </div>
        <p style="font-weight: 500; font-size: 13px; color: {state_color}; margin-bottom: 12px; line-height: 1.4;">
            {primary_rec}
        </p>
    """
    clean_rec_html = "".join([line.strip() for line in rec_html.split("\n")])
    st.markdown(clean_rec_html, unsafe_allow_html=True)

    # 1. Action Items List
    st.markdown('<p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 6px; letter-spacing: 0.5px;">Mitigation Actions</p>', unsafe_allow_html=True)
    if actions:
        for action in actions:
            st.markdown(
                f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px; font-size: 12px; line-height: 1.4;">'
                f'<span style="color: {state_color}; margin-right: 6px; font-weight: 600;">—</span>'
                f'<span style="color: var(--text-primary);">{action}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<p style="font-size: 12px; color: var(--text-secondary); font-style: italic;">No mitigation actions required.</p>', unsafe_allow_html=True)

    # 2. Warnings/Signals List
    st.markdown('<p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); margin-top: 14px; margin-bottom: 6px; letter-spacing: 0.5px;">Trigger Conditions</p>', unsafe_allow_html=True)
    if warnings:
        for warning in warnings:
            icon_color = "#635bff" if "Predictive" in warning else state_color
            st.markdown(
                f'<div style="display: flex; align-items: flex-start; margin-bottom: 6px; font-size: 11px; line-height: 1.4; color: var(--text-secondary);">'
                f'<span style="color: {icon_color}; margin-right: 6px; font-weight: 600;">•</span>'
                f'<span>{warning}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<p style="font-size: 11px; color: var(--text-secondary); font-style: italic;">No operational degradation alarms triggered.</p>', unsafe_allow_html=True)

    # 3. Persistent Disclaimer
    disc_html = f"""
    <div class="disclaimer-text">
        {disclaimer}
    </div>
    </div>
    """
    clean_disc_html = "".join([line.strip() for line in disc_html.split("\n")])
    st.markdown(clean_disc_html, unsafe_allow_html=True)
