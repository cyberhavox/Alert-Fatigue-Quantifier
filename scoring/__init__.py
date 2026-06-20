"""Scoring module for the Alert Fatigue Quantifier.

This package provides baseline calculation, normalisation, and AFI scoring
operations.
"""

from scoring.baseline_calibrator import build_and_save_baselines, load_baseline
from scoring.normaliser import normalise_zscore, apply_sigmoid
from scoring.afi_calculator import calculate_analyst_afi

__all__ = [
    "build_and_save_baselines",
    "load_baseline",
    "normalise_zscore",
    "apply_sigmoid",
    "calculate_analyst_afi",
]
