"""Signals calculation engine for the Alert Fatigue Quantifier.

This package computes the five rolling behavioral signals from the validated
log DataFrames.
"""

from signals.triage_interval import calculate_triage_interval
from signals.uninvestigated_closures import calculate_uninvestigated_closures
from signals.escalation_deviations import calculate_escalation_deviations
from signals.enrichment_depth import calculate_enrichment_depth
from signals.hourly_closure_rate import calculate_hourly_closure_rate

__all__ = [
    "calculate_triage_interval",
    "calculate_uninvestigated_closures",
    "calculate_escalation_deviations",
    "calculate_enrichment_depth",
    "calculate_hourly_closure_rate",
]
