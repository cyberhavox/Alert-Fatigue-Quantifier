# Decision Quality Anomaly Detection

This document specifies the mathematical model and statistical processing rules for the **Degradation Detector** component of the Alert Fatigue Quantifier.

---

## 1. Functional Objective

Alert fatigue causes analysts to cut corners during alert triage. The primary operational indicators of this shortcutting behavior are:
1. **Spikes in False Positive Rates:** Overloaded analysts dismiss alerts as false positives (`dismissed` status) without verifying logs.
2. **Drops in Investigation Depth:** Analysts perform fewer enrichment queries (`enrichment_actions`) per alert.

The degradation detector compares the distributions of these behaviors in the **current rolling 60-minute window** against the analyst's **30-day historical baseline** to detect statistically significant drops in investigation quality.

---

## 2. Statistical Methodology: Mann–Whitney U Test

Human behavioral data in security operations (such as the number of lookup actions or log response times) is discrete, bounded, and heavily skewed. It **does not follow a normal Gaussian distribution**. Therefore, parametric tests like the Student's t-test are inappropriate.

To maintain academic rigor, the degradation detector utilizes the **Mann–Whitney U test** (also known as the Wilcoxon rank-sum test), a non-parametric statistical hypothesis test.

### 2.1 Hypotheses
* **Null Hypothesis ($H_0$):** The distribution of analyst behaviors in the current rolling 60-minute window is identical to the distribution of their 30-day historical baseline.
* **Alternative Hypothesis ($H_1$):** The distribution of behaviors in the current window is shifted significantly (indicating a drop in enrichment depth or a spike in dismissal rate).

### 2.2 Test Statistic Calculation
Let the current window sample size be $n_1$ and the baseline sample size be $n_2$. The combined observations are ranked from smallest to largest ($1$ to $n_1 + n_2$). In the case of tied values, average ranks are assigned.

The test statistic $U$ is the smaller of $U_1$ and $U_2$:

$$U_1 = R_1 - \frac{n_1(n_1 + 1)}{2}$$

$$U_2 = R_2 - \frac{n_2(n_2 + 1)}{2}$$

$$U = \min(U_1, U_2)$$

Where:
* $R_1$ is the sum of ranks of observations in the current rolling window.
* $R_2$ is the sum of ranks of observations in the baseline dataset.

### 2.3 Significance Threshold
The pipeline evaluates the probability (p-value) of obtaining a test statistic at least as extreme as the observed $U$ under the null hypothesis:

$$\text{Anomaly Flagged} = (p < 0.05)$$

A significance threshold of **$p < 0.05$** is enforced. If the calculated p-value drops below $0.05$, the system rejects the null hypothesis and logs a **degradation anomaly** flag.

---

## 3. Pipeline Implementation

The degradation detector is implemented in `degradation/detector.py` and `degradation/mann_whitney.py` using SciPy:

```python
import numpy as np
from scipy import stats

def perform_mann_whitney_test(
    window_data: np.ndarray,
    baseline_data: np.ndarray
) -> float:
    """
    Executes the Mann-Whitney U test between two behavioral samples.

    Args:
        window_data: Array of current window metrics (e.g. enrichment actions).
        baseline_data: Array of baseline metrics.

    Returns:
        p_value: The calculated two-sided p-value.
    """
    # Execute double-sided non-parametric rank-sum test
    stat, p_val = stats.mannwhitneyu(
        window_data, 
        baseline_data, 
        alternative='two-sided'
    )
    return float(p_val)
```

### Logging Anomaly Output
When $p < 0.05$ is met, the module logs a record to `data/output/degradation_anomalies.json` containing:
* `timestamp`: ISO 8601 UTC timestamp.
* `analyst_id`: The ID of the affected analyst.
* `signal`: The signal that triggered the degradation (e.g., `enrichment_depth`).
* `p_value`: The calculated p-value.
* `deviation_zscore`: The z-score of the current mean relative to the baseline.
