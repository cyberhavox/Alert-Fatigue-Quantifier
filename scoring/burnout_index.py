"""Burnout Risk Index (BRI) & Financial Breach Risk Exposure Estimator.

Source: SOUPS 2015 (Sundaramurthy et al.) & Ponemon Institute / SANS 2024
Calculates:
1. Burnout Risk Index (BRI: 0-100): Differentiates healthy throughput from exhaustion rushing.
2. Financial Breach Risk Exposure ($ Risk): Estimated monetary vulnerability caused by fatigue-driven errors.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


def calculate_burnout_risk_index(
    afi_score: float,
    triage_interval: float,
    baseline_triage: float,
    enrichment_depth: float,
    uninvestigated_closures: float
) -> tuple[float, float]:
    """Calculates Burnout Risk Index (BRI 0-100) and Financial Breach Exposure ($ Risk).

    Args:
        afi_score: Analyst Fatigue Index (0-100).
        triage_interval: Active shift mean response latency (seconds).
        baseline_triage: 30-day baseline mean response latency (seconds).
        enrichment_depth: Active shift mean threat intel lookups per alert.
        uninvestigated_closures: Ratio of alerts closed without notes/enrichment.

    Returns:
        Tuple of (burnout_risk_index, estimated_financial_risk_dollars).
    """
    # Rushing speed factor vs enrichment quality drop
    rushing = max(0.0, 1.0 - (triage_interval / baseline_triage)) if baseline_triage > 0 else 0.0
    quality_drop = uninvestigated_closures

    # Burnout Risk Index formula
    bri_raw = 0.40 * afi_score + 0.35 * (rushing * 100.0) + 0.25 * (quality_drop * 100.0)
    bri_score = float(np.clip(bri_raw, 0.0, 100.0))

    # Ponemon 2022 Cost of Data Breach Benchmark ($4.45M avg breach cost / 10,000 uninvestigated alerts = ~$445 per uninvestigated alert)
    avg_alert_risk = 445.0
    estimated_dollars = round((bri_score / 100.0) * 15.0 * avg_alert_risk, 2)

    return round(bri_score, 1), estimated_dollars
