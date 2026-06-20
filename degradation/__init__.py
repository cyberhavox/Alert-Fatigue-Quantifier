"""Decision quality degradation detection module for the Alert Fatigue Quantifier.

This package provides statistics wrappers and detection algorithms to identify
declines in analyst investigation depth.
"""

from degradation.mann_whitney import perform_mann_whitney_test
from degradation.detector import detect_degradation_anomalies

__all__ = ["perform_mann_whitney_test", "detect_degradation_anomalies"]
