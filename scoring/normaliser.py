"""Normalization and scaling utilities for the Scoring module.

Provides SciPy-like z-score normalization and logistic sigmoid functions to
standardize rolling signal metrics.
"""

import numpy as np


def normalise_zscore(value: float, mean: float, std: float, negate: bool = False) -> float:
    """Calculates the standard normal score (z-score) for a value.

    Args:
        value: The raw signal value.
        mean: The baseline mean for the signal.
        std: The baseline standard deviation.
        negate: If True, reverses the sign of the z-score (used when lower raw
            values indicate higher fatigue, e.g. enrichment depth).

    Returns:
        The computed float z-score.
    """
    if std <= 0.0:
        return 0.0
    z = (value - mean) / std
    return -z if negate else z


def apply_sigmoid(z_score: float) -> float:
    """Applies a logistic sigmoid function to bound a z-score to range [0.0, 1.0].

    Args:
        z_score: The standard normal z-score value.

    Returns:
        The scaled output between 0.0 and 1.0.
    """
    return float(1.0 / (1.0 + np.exp(-z_score)))
