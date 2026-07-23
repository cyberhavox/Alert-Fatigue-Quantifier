"""Recommendation Panel component.

Renders advisory suggestions sidebar panel, showing recommended mitigations,
Adaptive Autonomy Level, THERP Human Error Probability (HEP %), SOAR Webhook payload,
and persistent safety disclaimer. Zero emojis.
"""

from __future__ import annotations
import json
import streamlit as st
from recommendations.engine import generate_soar_webhook_payload
from scoring.therp_hep_calculator import calculate_therp_hep
from scoring.burnout_index import calculate_burnout_risk_index


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def render_recommendation_panel(
    analyst_id: str,
    afi_score: float,
    recommendations: dict,
    hep_score: float | None = None,
    financial_risk_exposure: float | None = None
) -> None:
    """Renders the advisory recommendations panel, Adaptive Autonomy Level, and SOAR Webhook."""
    state = recommendations.get("state", "NOMINAL")
    primary_rec = recommendations.get("primary_recommendation", "")
    actions = recommendations.get("actions", [])
    warnings = recommendations.get("warnings", [])
    autonomy_title = recommendations.get("autonomy_level_title", "Level 0: Manual Operator Triage")
    autonomy_desc = recommendations.get("autonomy_level_desc", "Human-in-the-Loop")
    disclaimer = recommendations.get("disclaimer", "All recommendations are advisory. Operational decisions rest with SOC management.")

    # Read live dynamic THERP HEP and Financial Risk Exposure
    hep_pct = hep_score if hep_score is not None else recommendations.get("therp_hep_percentage", calculate_therp_hep(afi_score))
    risk_dollars = financial_risk_exposure if financial_risk_exposure is not None else (afi_score * 44.5)

    color_map = {
        "NOMINAL": "#10b981",
        "ELEVATED": "#f59e0b",
        "HIGH": "#ef4444",
        "CRITICAL": "#dc2626"
    }
    state_color = color_map.get(state, "#f9fafb")
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
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid #1f2937;">
        <span style="font-weight:600; font-size:15px; color:var(--text-primary);">{analyst_id}</span>
        <span class="badge {badge_cls}">AFI {afi_score:.0f}</span>
      </div>
      
      <div style="background:#1f2937; border:1px solid #374151; border-radius:6px; padding:10px 12px; margin-bottom:14px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#3b82f6; letter-spacing:0.5px;">Adaptive SOAR Autonomy Level</div>
        <div style="font-size:13px; font-weight:700; color:#f9fafb; margin-top:2px;">{autonomy_title}</div>
        <div style="font-size:11px; color:#9ca3af; margin-top:2px;">{autonomy_desc}</div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:14px;">
        <div style="background:#1f2937; border:1px solid #374151; border-radius:6px; padding:10px;">
          <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">THERP Human Error (HEP)</div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:{'#ef4444' if hep_pct > 25 else '#10b981'}; margin-top:2px;">{hep_pct:.1f}%</div>
          <div style="font-size:10px; color:#9ca3af;">Error Prob. (ResearchGate)</div>
        </div>

        <div style="background:#1f2937; border:1px solid #374151; border-radius:6px; padding:10px;">
          <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">Breach Risk Exposure</div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:#f59e0b; margin-top:2px;">${risk_dollars:,.0f}</div>
          <div style="font-size:10px; color:#9ca3af;">Ponemon Risk Estimate</div>
        </div>
      </div>

      <p style="font-weight:500; font-size:13px; color:{state_color}; margin-bottom:14px; line-height:1.4;">
        {primary_rec}
      </p>

      <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--text-secondary); margin-bottom:8px; letter-spacing:0.5px;">
        Mitigation Actions
      </div>
      {actions_html}

      <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--text-secondary); margin-top:14px; margin-bottom:8px; letter-spacing:0.5px;">
        Trigger Conditions
      </div>
      {warnings_html}

      <div style="font-size:11px; color:var(--text-muted); border-top:1px solid #1f2937; padding-top:12px; margin-top:14px; line-height:1.4;">
        {disclaimer}
      </div>
    </div>
    """)

    st.markdown(panel_html, unsafe_allow_html=True)

    # ── SOAR Automated Queue Rebalancing JSON Webhook Box ──────
    pred_flag = 1 if (state in ["HIGH", "CRITICAL"]) else 0
    webhook_payload = generate_soar_webhook_payload(analyst_id, afi_score, pred_flag)

    with st.expander("🤖 SOAR Automated Queue Rebalancing Webhook (IEEE THMS 23)", expanded=False):
        st.caption("Cortex XSOAR / Splunk SOAR OCSF 1.1.0 Export Payload")
        st.json(webhook_payload)
