"""Advisory recommendations & Adaptive Autonomy Engine for the Alert Fatigue Quantifier.

Maps computed Analyst Fatigue Index (AFI) scores, THERP Human Error Probability (HEP),
and predictive ML risks into Adaptive Autonomy Levels (Level 0-3) and OCSF 1.1.0 JSON Webhooks.
"""

from config.settings import (
    THRESHOLD_NOMINAL_MAX,
    THRESHOLD_ELEVATED_MAX,
    THRESHOLD_HIGH_MAX,
)
from scoring.therp_hep_calculator import calculate_therp_hep


def get_adaptive_autonomy_level(afi_score: float) -> tuple[int, str, str]:
    """Determines Adaptive Autonomy Level (IEEE Access / THMS).

    - Level 0: Manual Triage (Nominal AFI < 50)
    - Level 1: AI-Assisted Enrichment (Elevated AFI 50-70)
    - Level 2: Semi-Automated Pre-Filtering (High AFI 70-90)
    - Level 3: Full Autonomous Quarantine & Failover (Critical AFI >= 90)
    """
    if afi_score <= THRESHOLD_NOMINAL_MAX:
        return 0, "Level 0: Manual Operator Triage", "Human-in-the-Loop: Standard manual inspection."
    elif afi_score <= THRESHOLD_ELEVATED_MAX:
        return 1, "Level 1: AI-Assisted Enrichment", "Human-in-the-Loop: Automated threat intel lookups enabled."
    elif afi_score <= THRESHOLD_HIGH_MAX:
        return 2, "Level 2: Semi-Automated Pre-Filtering", "Human-on-the-Loop: SOAR pre-dismisses low-risk FP alerts."
    else:
        return 3, "Level 3: Full Autonomous Failover", "Human-out-of-the-Loop: Auto-quarantine & queue rerouting active."


def get_advisory_recommendations(
    afi_score: float,
    anomalies: list[dict],
    prediction_flag: int
) -> dict:
    """Generates advisory recommendations based on AFI, anomalies, and ML risk flags."""
    level_num, level_title, level_desc = get_adaptive_autonomy_level(afi_score)
    hep_pct = calculate_therp_hep(afi_score)

    if afi_score <= THRESHOLD_NOMINAL_MAX:
        state = "NOMINAL"
        primary_rec = "Analyst is operating within nominal baseline parameters."
        actions = [
            "Maintain current queue assignments and standard rotation schedule.",
            "No adjustments required at this time."
        ]
    elif afi_score <= THRESHOLD_ELEVATED_MAX:
        state = "ELEVATED"
        primary_rec = "Elevated cognitive load detected. Performance indicators are shifting."
        actions = [
            "Consider scheduling a short 10-15 minute rest break within the next 2 hours.",
            "Consider task rotation (e.g. shift to documentation or threat hunting) to reduce repetitive alert load."
        ]
    elif afi_score <= THRESHOLD_HIGH_MAX:
        state = "HIGH"
        primary_rec = "High alert fatigue. Quality metrics indicate attention narrowing."
        actions = [
            "Consider rotating the analyst out of primary high-volume queues for the remainder of the shift.",
            "Consider pairing with a second analyst for peer review on high-severity escalations.",
            "Recommend a mandatory 20-minute rest break."
        ]
    else:
        state = "CRITICAL"
        primary_rec = "Critical fatigue levels. Spikes in cognitive errors are highly probable."
        actions = [
            "Recommend an immediate operational pause and shift handoff.",
            "Consider temporary alert suppression or queue redirection for incoming medium/high alerts for this analyst.",
            "Mandate a rest break before resuming any triage duties."
        ]

    warnings = []
    for anomaly in anomalies:
        signal = anomaly.get("Signal", "")
        deviation = anomaly.get("Deviation", 0.0)
        p_val = anomaly.get("p-value", 1.0)
        
        if "Enrichment" in signal:
            warnings.append(
                f"Drop in enrichment depth detected (z={deviation:.2f}, p={p_val:.4f}). "
                "Analyst may be skipping verification steps."
            )
        elif "Triage" in signal:
            warnings.append(
                f"Triage interval elongation detected (z={deviation:.2f}, p={p_val:.4f}). "
                "Analyst response latency is significantly higher than baseline."
            )
        else:
            warnings.append(
                f"Statistical deviation in {signal} detected (z={deviation:.2f}, p={p_val:.4f})."
            )

    if prediction_flag == 1:
        warnings.append(
            "Predictive risk warning: ML model forecasts elevated fatigue risk in the upcoming hours. "
            "Proactive queue monitoring recommended."
        )

    return {
        "state": state,
        "primary_recommendation": primary_rec,
        "actions": actions,
        "warnings": warnings,
        "autonomy_level_num": level_num,
        "autonomy_level_title": level_title,
        "autonomy_level_desc": level_desc,
        "therp_hep_percentage": hep_pct,
        "disclaimer": "All recommendations are advisory. Decisions rest with the SOC manager."
    }


def generate_soar_webhook_payload(
    analyst_id: str,
    afi_score: float,
    prediction_flag: int,
    timestamp: str = ""
) -> dict:
    """Generates standardized OCSF 1.1.0 / Cortex XSOAR compatible JSON Webhook payload."""
    trigger_flag = afi_score > 70.0 or prediction_flag == 1
    level_num, level_title, _ = get_adaptive_autonomy_level(afi_score)
    hep_pct = calculate_therp_hep(afi_score)

    return {
        "event_type": "AFQ_SOAR_QUEUE_REBALANCE_TRIGGER" if trigger_flag else "AFQ_STATUS_NOMINAL",
        "schema_version": "OCSF_1.1.0",
        "timestamp": timestamp or "2026-07-23T06:20:00Z",
        "analyst_node": analyst_id,
        "metrics": {
            "analyst_fatigue_index": round(afi_score, 2),
            "therp_human_error_probability_pct": hep_pct,
            "adaptive_autonomy_level": level_num,
            "predictive_risk_flag": int(prediction_flag),
            "rebalance_action_required": trigger_flag
        },
        "soar_action_recommendation": {
            "target_soar_platform": "Cortex XSOAR / Splunk SOAR",
            "autonomy_policy": level_title,
            "action": "PAUSE_HIGH_SEVERITY_TICKET_ASSIGNMENT" if trigger_flag else "MAINTAIN_STANDARD_QUEUE",
            "reroute_queue": "SOC_REBALANCED_QUEUE_POOL" if trigger_flag else "PRIMARY_DESK",
            "mandatory_rest_break_minutes": 20 if afi_score > 70.0 else 0
        }
    }
