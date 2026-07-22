"""Recommendation Panel component.

Renders advisory suggestions sidebar panel, showing recommended mitigations,
warning triggers, and persistent safety disclaimer. Zero emojis.
"""

from __future__ import annotations
import streamlit as st


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def render_recommendation_panel(
    analyst_id: str,
    afi_score: float,
    recommendations: dict
) -> None:
    """Renders the advisory recommendations panel."""
    state = recommendations.get("state", "NOMINAL")
    primary_rec = recommendations.get("primary_recommendation", "")
    actions = recommendations.get("actions", [])
    warnings = recommendations.get("warnings", [])
    disclaimer = recommendations.get("disclaimer", "All recommendations are advisory. Operational decisions rest with SOC management.")

    color_map = {
        "NOMINAL": "#10b981",
        "ELEVATED": "#f59e0b",
        "HIGH": "#ef4444",
        "CRITICAL": "#dc2626"
    }
    state_color = color_map.get(state, "#f8fafc")
    badge_cls = f"badge-{state.lower()}"

    actions_html = ""
    if actions:
        for action in actions:
            actions_html += f"""
            <div style="display:flex; align-items:flex-start; margin-bottom:8px; font-size:13px; line-height:1.4;">
              <span style="color:{state_color}; margin-right:8px; font-weight:700;">—</span>
              <span style="color:var(--text-primary);">{action}</span>
            </div>
            """
    else:
        actions_html = '<p style="font-size:12px; color:var(--text-muted); font-style:italic;">No mitigation actions required.</p>'

    warnings_html = ""
    if warnings:
        for warning in warnings:
            icon_color = "#6366f1" if "Predictive" in warning else state_color
            warnings_html += f"""
            <div style="display:flex; align-items:flex-start; margin-bottom:6px; font-size:12px; line-height:1.4; color:var(--text-secondary);">
              <span style="color:{icon_color}; margin-right:8px; font-weight:700;">•</span>
              <span>{warning}</span>
            </div>
            """
    else:
        warnings_html = '<p style="font-size:12px; color:var(--text-muted); font-style:italic;">No operational degradation alarms triggered.</p>'

    panel_html = _clean_html(f"""
    <div class="recommendation-container">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid #334155;">
        <span style="font-weight:600; font-size:15px; color:var(--text-primary);">{analyst_id}</span>
        <span class="badge {badge_cls}">AFI {afi_score:.0f}</span>
      </div>
      
      <p style="font-weight:500; font-size:14px; color:{state_color}; margin-bottom:16px; line-height:1.4;">
        {primary_rec}
      </p>

      <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--text-secondary); margin-bottom:8px; letter-spacing:0.5px;">
        Mitigation Actions
      </div>
      {actions_html}

      <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--text-secondary); margin-top:16px; margin-bottom:8px; letter-spacing:0.5px;">
        Trigger Conditions
      </div>
      {warnings_html}

      <div style="font-size:11px; color:var(--text-muted); border-top:1px solid #334155; padding-top:12px; margin-top:16px; line-height:1.4;">
        {disclaimer}
      </div>
    </div>
    """)

    st.markdown(panel_html, unsafe_allow_html=True)
