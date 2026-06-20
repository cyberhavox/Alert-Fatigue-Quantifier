"""Advisory recommendations engine package for the Alert Fatigue Quantifier.

This package maps composite fatigue scores, statistical anomalies, and machine learning
forecasts to advisory mitigation actions.
"""

from recommendations.engine import get_advisory_recommendations

__all__ = ["get_advisory_recommendations"]
