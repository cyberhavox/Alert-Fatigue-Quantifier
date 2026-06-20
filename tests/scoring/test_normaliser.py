"""Unit tests for the standard normal score normalisation and sigmoid scaling functions.
"""

import numpy as np
from scoring.normaliser import normalise_zscore, apply_sigmoid


def test_normalise_zscore_math() -> None:
    """Asserts that z-score calculations match standard statistical formulas."""
    # z = (value - mean) / std = (10 - 6) / 2 = 2.0
    assert normalise_zscore(10.0, 6.0, 2.0) == 2.0
    
    # Negative test (z-score reversal for metrics like enrichment depth)
    # z = -((4 - 6) / 2) = -(-1.0) = 1.0
    assert normalise_zscore(4.0, 6.0, 2.0, negate=True) == 1.0


def test_normalise_zscore_zero_std() -> None:
    """Verifies that z-score returns 0.0 when std is zero to avoid division by zero errors."""
    assert normalise_zscore(10.0, 6.0, 0.0) == 0.0
    assert normalise_zscore(10.0, 6.0, -1.0) == 0.0


def test_apply_sigmoid_bounds() -> None:
    """Asserts that sigmoid scaling bounds z-scores strictly between 0.0 and 1.0."""
    assert apply_sigmoid(0.0) == 0.5
    assert 0.0 < apply_sigmoid(-10.0) < 0.1
    assert 0.9 < apply_sigmoid(10.0) < 1.0
