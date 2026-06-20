"""Advisory recommendations engine for the Alert Fatigue Quantifier.

Maps computed Analyst Fatigue Index (AFI) scores, statistical anomalies, and predictive
ML risks into non-imperative, advisory actions for SOC managers.
"""

from config.settings import (
    THRESHOLD_NOMINAL_MAX,
    THRESHOLD_ELEVATED_MAX,
    THRESHOLD_HIGH_MAX,
)


def get_advisory_recommendations(
    afi_score: float,
    anomalies: list[dict],
    prediction_flag: int
) -> dict:
    """Generates advisory recommendations based on AFI, anomalies, and ML risk flags.

    Follows design guidelines: non-imperative language, advisory-only context, and
    prominent display of the system disclaimer.

    Args:
        afi_score: The composite Analyst Fatigue Index (0.0 to 100.0).
        anomalies: A list of anomaly dictionaries triggered for the analyst.
        prediction_flag: Binary prediction from the ML classifier (1 = fatigue risk, 0 = normal).

    Returns:
        A dictionary containing:
        - 'state': One of ['NOMINAL', 'ELEVATED', 'HIGH', 'CRITICAL']
        - 'primary_recommendation': Main advisory text.
        - 'actions': List of conditional suggestion strings.
        - 'warnings': List of triggered warning logs.
        - 'disclaimer': Persistent safety warning.
    """
    # 1. Determine severity state based on literature thresholds
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

    # 2. Extract warnings from statistical anomalies
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

    # 3. Incorporate ML predictions
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
        "disclaimer": "All recommendations are advisory. Decisions rest with the SOC manager."
    }
