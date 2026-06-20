"""Mann-Whitney U statistical test wrapper for the Degradation module.

This module provides a robust wrapper around SciPy's rank-sum test to compare
current rolling performance samples with historical baseline samples.
"""

import numpy as np
from scipy import stats


def perform_mann_whitney_test(
    window_data: np.ndarray,
    baseline_data: np.ndarray
) -> float:
    """Executes a two-sided Mann-Whitney U test between two data samples.

    Args:
        window_data: 1D array representing current rolling window observations.
        baseline_data: 1D array representing historical baseline observations.

    Returns:
        The two-sided asymptotic p-value of the test.
    """
    if len(window_data) == 0 or len(baseline_data) == 0:
        return 1.0  # Cannot perform test, accept null hypothesis (no change)

    # In case of constant arrays (e.g. all zeros), mannwhitneyu can raise ValueError
    # or return nan. Let's handle it gracefully:
    if np.all(window_data == window_data[0]) and np.all(baseline_data == baseline_data[0]):
        if window_data[0] == baseline_data[0]:
            return 1.0  # Identical flat distributions, no change
        return 0.0  # Completely shifted, maximum change

    try:
        _, p_val = stats.mannwhitneyu(
            window_data,
            baseline_data,
            alternative="two-sided"
        )
        return float(p_val)
    except ValueError:
        return 1.0
