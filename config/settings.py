"""Configuration constants for the Alert Fatigue Quantifier.

This module serves as the single source of truth for all constants, thresholds,
and literature-derived weights utilized across the Alert Fatigue Quantifier
pipeline. It contains no functions, classes, or logical computations, and has
zero external dependencies.
"""

# -----------------------------------------------------------------------------
# AFI Scoring Formula Weights (Must sum to 1.0)
# -----------------------------------------------------------------------------

WEIGHT_TRIAGE_INTERVAL: float = 0.25
"""Triage Interval Weight (w1).
Source: SANS Institute (2023) / Al-Mhiqani et al. (2020)
Triage delay is the earliest indicator of cognitive slowing and decision latency.
"""

WEIGHT_UNINVESTIGATED_CLOSURES: float = 0.25
"""Uninvestigated Closures Weight (w2).
Source: Alahmadi et al. (2022) [USENIX Security]
Closing alerts without enrichment or notes is a critical quality degradation shortcut.
"""

WEIGHT_ENRICHMENT_DEPTH: float = 0.20
"""Enrichment Depth Weight (w3).
Source: Best et al. (2021) / Werlinger et al. (2010)
Dropping validation lookups and enrichment depth indicates attention narrowing.
"""

WEIGHT_ESCALATION_DEVIATIONS: float = 0.15
"""Escalation Deviations Weight (w4).
Source: Sundaramurthy et al. (2015)
Stress spikes cause deviations from baseline escalation rates (apathy or hyper-vigilance).
"""

WEIGHT_HOURLY_CLOSURE_RATE: float = 0.15
"""Hourly Closure Rate Weight (w5).
Source: Ponemon Institute (2022) / SANS (2024)
High throughput rate increases fatigue, followed by performance drops.
"""


# -----------------------------------------------------------------------------
# Severity Thresholds for the Analyst Fatigue Index (AFI)
# -----------------------------------------------------------------------------

THRESHOLD_NOMINAL_MAX: float = 49.0
"""Nominal Fatigue Threshold Max.
Source: Shirley et al. (2023)
Under 50% capacity, human operators maintain normal operational performance.
"""

THRESHOLD_ELEVATED_MAX: float = 69.0
"""Elevated Fatigue Threshold Max.
Source: Best et al. (2021)
Slowing reaction times and rising error rates start above 50% capacity saturation.
"""

THRESHOLD_HIGH_MAX: float = 89.0
"""High Fatigue Threshold Max.
Source: Alahmadi et al. (2022) [USENIX Security]
Above 70%, analysts begin skipping verification steps and omitting triage notes.
"""

THRESHOLD_CRITICAL_MIN: float = 90.0
"""Critical Fatigue Threshold Min.
Source: Sundaramurthy et al. (2015) / SANS (2025)
Above 90%, cognitive errors spike significantly, necessitating immediate breaks.
"""


# -----------------------------------------------------------------------------
# System Time Parameters
# -----------------------------------------------------------------------------

ROLLING_WINDOW_MINUTES: int = 60
"""Size of the active rolling window in minutes for evaluating analyst signals."""

BASELINE_DAYS: int = 30
"""Duration of the historical performance log baseline in days."""


# -----------------------------------------------------------------------------
# System File Paths
# -----------------------------------------------------------------------------

PATH_RAW_LOGS: str = "data/raw/"
"""Directory path for raw synthetic CSV/JSON log exports."""

PATH_BASELINE_LOGS: str = "data/baseline/"
"""Directory path for baseline parameters and logs."""

PATH_OUTPUT_LOGS: str = "data/output/"
"""Directory path for intermediate and final pipeline scores."""


# -----------------------------------------------------------------------------
# Synthetic Data Generator Parameters (SANS/Ponemon Distributions)
# -----------------------------------------------------------------------------

LAMBDA_NOMINAL: float = 15.0
"""Mean hourly alert arrival rate in nominal state. Poisson distribution.
Source: SANS Institute (2023)
"""

LAMBDA_FATIGUE: float = 25.0
"""Mean hourly alert arrival rate in fatigued state. Poisson distribution.
Source: SANS Institute (2023)
"""

FP_RATE_NOMINAL: float = 0.80
"""Ratio of alerts resolved as dismissed in nominal state.
Source: Ponemon Institute (2022)
"""

FP_RATE_FATIGUE: float = 0.95
"""Ratio of alerts resolved as dismissed in fatigued state.
Source: SANS Institute (2025)
"""

ENRICHMENT_K_NOMINAL: float = 3.0
"""Shape parameter (k) for Gamma distribution of enrichment count in nominal state.
Source: Alahmadi et al. (2022) [USENIX]
"""

ENRICHMENT_THETA_NOMINAL: float = 2.0
"""Scale parameter (theta) for Gamma distribution of enrichment count in nominal state.
Source: Alahmadi et al. (2022) [USENIX]
"""

ENRICHMENT_K_FATIGUE: float = 1.2
"""Shape parameter (k) for Gamma distribution of enrichment count in fatigued state.
Source: Alahmadi et al. (2022) [USENIX]
"""

ENRICHMENT_THETA_FATIGUE: float = 1.0
"""Scale parameter (theta) for Gamma distribution of enrichment count in fatigued state.
Source: Alahmadi et al. (2022) [USENIX]
"""

NOTES_LEN_MEAN_NOMINAL: float = 120.0
"""Mean characters count of analyst notes in nominal state. Normal distribution.
Source: Best et al. (2021)
"""

NOTES_LEN_STD_NOMINAL: float = 30.0
"""Standard deviation of analyst notes length in nominal state. Normal distribution.
Source: Best et al. (2021)
"""

NOTES_LEN_MEAN_FATIGUE: float = 10.0
"""Mean characters count of analyst notes in fatigued state. Normal distribution.
Source: Best et al. (2021)
"""

TRIAGE_MEAN_NOMINAL: float = 180.0
"""Mean triage interval in seconds in nominal state. Log-normal distribution.
Source: SANS Institute (2023) / Al-Mhiqani et al. (2020)
"""

TRIAGE_STD_NOMINAL: float = 60.0
"""Standard deviation of triage interval in seconds in nominal state.
Source: SANS Institute (2023) / Al-Mhiqani et al. (2020)
"""

TRIAGE_MEAN_FATIGUE: float = 480.0
"""Mean triage interval in seconds in fatigued state. Log-normal distribution.
Source: SANS Institute (2023) / Al-Mhiqani et al. (2020)
"""

TRIAGE_STD_FATIGUE: float = 240.0
"""Standard deviation of triage interval in seconds in fatigued state.
Source: SANS Institute (2023) / Al-Mhiqani et al. (2020)
"""

