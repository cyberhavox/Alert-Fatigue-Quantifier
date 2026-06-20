"""Recommendation Panel component for the Streamlit dashboard.

Renders the advisory suggestions sidebar panel, showing recommended mitigations,
warning triggers, and the mandatory persistent safety disclaimer.
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
        recommendations: Dictionary containing mapping output from the advisory engine:
                         ['state', 'primary_recommendation', 'actions', 'warnings', 'disclaimer']
    """
    # Header
    st.markdown('<div class="section-header">Recommendations</div>', unsafe_allow_html=True)

    # Panel container HTML
    state = recommendations.get("state", "NOMINAL")
    primary_rec = recommendations.get("primary_recommendation", "")
    actions = recommendations.get("actions", [])
    warnings = recommendations.get("warnings", [])
    disclaimer = recommendations.get("disclaimer", "All recommendations are advisory. Decisions rest with the SOC manager.")

    # Color variables matching theme.css
    color_map = {
        "NOMINAL": "#3FB950",
        "ELEVATED": "#D29922",
        "HIGH": "#F78166",
        "CRITICAL": "#FF4444"
    }
    state_color = color_map.get(state, "#E6EDF3")
    badge_cls = f"badge-{state.lower()}"

    # Render recommendations details
    st.markdown(
        f"""
        <div class="recommendation-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-subtle);">
                <span style="font-weight: 600; font-size: 13px; color: var(--text-primary);">{analyst_id}</span>
                <span class="badge {badge_cls}">AFI {afi_score:.0f}</span>
            </div>
            
            <p style="font-weight: 500; font-size: 13px; color: {state_color}; margin-bottom: 12px;">
                {primary_rec}
            </p>
        """,
        unsafe_allow_html=True
    )

    # 1. Action Items List
    st.markdown('<p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 6px; letter-spacing: 0.5px;">Advisory Actions</p>', unsafe_allow_html=True)
    if actions:
        for action in actions:
            st.markdown(
                f'<div style="display: flex; align-items: flex-start; margin-bottom: 8px; font-size: 12px; line-height: 1.4;">'
                f'<span style="color: {state_color}; margin-right: 6px; font-weight: bold;">[!]</span>'
                f'<span style="color: var(--text-primary);">{action}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<p style="font-size: 12px; color: var(--text-secondary); font-style: italic;">No actions suggested.</p>', unsafe_allow_html=True)

    # 2. Warnings/Signals List
    st.markdown('<p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); margin-top: 14px; margin-bottom: 6px; letter-spacing: 0.5px;">Triggers & Warnings</p>', unsafe_allow_html=True)
    if warnings:
        for warning in warnings:
            # Check if this warning contains "Predictive risk" to use primary accent color, otherwise use state color
            icon_color = "var(--accent-primary)" if "Predictive" in warning else state_color
            st.markdown(
                f'<div style="display: flex; align-items: flex-start; margin-bottom: 6px; font-size: 11px; line-height: 1.4; color: var(--text-secondary);">'
                f'<span style="color: {icon_color}; margin-right: 6px; font-weight: bold;">[i]</span>'
                f'<span>{warning}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown('<p style="font-size: 11px; color: var(--text-secondary); font-style: italic;">No statistical or predictive alarms triggered.</p>', unsafe_allow_html=True)

    # 3. Persistent Disclaimer
    st.markdown(
        f"""
            <div class="disclaimer-text">
                {disclaimer}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
