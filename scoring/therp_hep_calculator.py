"""THERP-based Human Error Probability (HEP) Estimator for SOC Operations.

Source: Al-Mhiqani et al. (ResearchGate 2021 / IEEE Cyber Ops)
Calculates the Human Error Probability P(Error) in range [0.0%, 100.0%] using
Technique for Human Error Rate Prediction (THERP) adapted for cybersecurity triage.
"""

from __future__ import annotations
import math
import pandas as pd
import numpy as np


def calculate_therp_hep(
    afi_score: float,
    circadian_multiplier: float = 1.0,
    automation_bias: float = 0.0,
    context_switch_count: float = 3.0
) -> float:
    """Calculates THERP Human Error Probability (HEP %).

    HEP = Baseline_HEP * Circadian_Factor * Workload_Factor * (1 + Automation_Bias)

    Args:
        afi_score: Analyst Fatigue Index (0-100).
        circadian_multiplier: 1.20 during night hours (02:00-06:00 UTC), else 1.0.
        automation_bias: Automation Bias Index ratio (0.0-1.0).
        context_switch_count: Mean tool switches per alert.

    Returns:
        Estimated Human Error Probability percentage (0.0% to 100.0%).
    """
    # Nominal baseline human error rate in routine monitoring is ~ 2% (0.02)
    base_hep = 0.02

    # Workload saturation multiplier derived from exponential AFI scaling
    workload_factor = math.exp((afi_score - 50.0) / 25.0) if afi_score > 50.0 else 1.0

    # Tool friction penalty factor
    friction_factor = 1.0 + (max(0.0, context_switch_count - 3.0) * 0.08)

    # Combined THERP HEP Formula
    hep_raw = base_hep * circadian_multiplier * workload_factor * friction_factor * (1.0 + automation_bias * 0.8)

    hep_percentage = min(99.9, hep_raw * 100.0)
    return round(hep_percentage, 2)
