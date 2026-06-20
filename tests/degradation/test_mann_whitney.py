"""Unit tests for the Mann-Whitney U statistical test wrapper.
"""

import numpy as np
from degradation.mann_whitney import perform_mann_whitney_test


def test_perform_mann_whitney_test_shifted() -> None:
    """Verifies that a significant shift in distributions returns a low p-value."""
    # window_data is significantly lower than baseline_data
    window = np.array([1, 1, 2, 1, 2, 1, 1, 2])
    baseline = np.array([5, 6, 5, 6, 7, 5, 6, 5, 6, 5])
    
    p_val = perform_mann_whitney_test(window, baseline)
    assert p_val < 0.05  # Significant difference


def test_perform_mann_whitney_test_identical() -> None:
    """Verifies that identical distributions return a high p-value (no change)."""
    window = np.array([5, 5, 5, 5, 5])
    baseline = np.array([5, 5, 5, 5, 5])
    
    p_val = perform_mann_whitney_test(window, baseline)
    assert p_val == 1.0


def test_perform_mann_whitney_test_empty_inputs() -> None:
    """Verifies that empty input arrays return a neutral p-value of 1.0."""
    empty = np.array([])
    valid = np.array([1, 2, 3])
    
    assert perform_mann_whitney_test(empty, valid) == 1.0
    assert perform_mann_whitney_test(valid, empty) == 1.0
