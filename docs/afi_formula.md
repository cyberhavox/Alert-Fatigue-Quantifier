# Analyst Fatigue Index (AFI) Mathematical Framework

This document outlines the mathematical framework, normalization techniques, and aggregation formula used to calculate the **Analyst Fatigue Index (AFI)**.

---

## 1. Mathematical Normalization

To ensure that behavioral metrics can be compared across different analysts with varying work speeds and patterns, all raw rolling window signals are normalized using **z-score normalization** against the individual analyst's 30-day historical baseline.

For each analyst, the system maintains a running baseline consisting of:
* Mean ($\mu$) of each signal.
* Standard Deviation ($\sigma$) of each signal.

### 1.1 z-Score Formula (SciPy Implementation)
For a raw signal value $x$:
$$z = \frac{x - \mu}{\sigma}$$

* **Directional Adjustments:** For signals where an *increase* indicates fatigue (e.g., Triage Interval, Uninvestigated Closures, Escalation Deviations), the standard z-score is used.
* **Inverse Signals:** For signals where a *decrease* indicates fatigue (e.g., Enrichment Depth), the z-score is negated to ensure that positive normalized scores consistently reflect increased cognitive load:
  $$z_{\text{enrichment}} = \frac{\mu - x}{\sigma}$$

---

## 2. Sigmoid Feature Scaling

To prevent extreme outliers (e.g., a single alert with an abnormally long triage time) from dominating the composite index, all z-scores are mapped to a bounded interval $[0, 1]$ using a standard **logistic sigmoid function**:

$$S(z_i) = \frac{1}{1 + e^{-k \cdot z_i}}$$

* **Parameters:** $k$ is a scaling factor (default $k = 1.0$) controlling the steepness of the curve.
* **Properties:**
  * When $z_i = 0$ (normal behavior), $S(z_i) = 0.5$.
  * When $z_i \to \infty$ (high fatigue), $S(z_i) \to 1.0$.
  * When $z_i \to -\infty$ (unusually high performance), $S(z_i) \to 0.0$.

---

## 3. Weighted Index Aggregation

The composite Analyst Fatigue Index (AFI) is calculated as a weighted average of the five sigmoid-scaled signals:

$$\text{Raw AFI} = \sum_{i=1}^{5} w_i \cdot S(z_i)$$

Where the weights satisfy the constraint:
$$\sum_{i=1}^{5} w_i = 1.0 \quad (w_i \ge 0)$$

### 3.1 Pinned Literature-Derived Weights

The following weights are assigned based on significance values and findings in the 18 reviewed sources:

* **$w_1$ (Triage Interval Weight):** $0.25$  
  *Justification:* SANS Institute (2023) / Al-Mhiqani et al. (2020). Triage delay is identified as the earliest measurable indicator of cognitive overload and decision latency as processing speed slows down under load.
* **$w_2$ (Uninvestigated Closures Weight):** $0.25$  
  *Justification:* Alahmadi et al. (2022) [USENIX Security]. Operational shortcuts—specifically closing alerts without triage notes or log analysis—represent the strongest behavioral marker of compromised decision quality.
* **$w_3$ (Escalation Deviations Weight):** $0.15$  
  *Justification:* Sundaramurthy et al. (2015). Under high fatigue, analysts deviate from their historical baseline escalation rates due to either hyper-vigilance (escalating everything) or exhaustion (escalating nothing).
* **$w_4$ (Enrichment Depth Weight):** $0.20$  
  *Justification:* Best et al. (2021) / Werlinger et al. (2010). Cognitive depletion leads to a drop in enrichment depth, where analysts skip checking secondary logs and threat intelligence databases as a coping mechanism.
* **$w_5$ (Hourly Closure Rate Weight):** $0.15$  
  *Justification:* Ponemon Institute (2022) / SANS (2024). High pressure to clear queues causes a spike in closure rates during the early stages of fatigue, followed by a performance drop as exhaustion sets in.

$$\text{Sum} = 0.25 + 0.25 + 0.15 + 0.20 + 0.15 = 1.0$$

---

## 4. Final AFI Scale

The final index is scaled to an operational range of $[0, 100]$:

$$\text{AFI} = \text{Raw AFI} \times 100$$

### 4.1 Severity Threshold Mapping

The AFI is divided into four operational bands:

| AFI Score Range | Severity Level | UI Indicator (design.md §2) | Literature & Operational Basis |
| :--- | :--- | :--- | :--- |
| `[0, 49]` | **Nominal** | Green (`--state-nominal`) | Shirley et al. (2023): Baseline task performance remains stable below 50% cognitive load capacity. |
| `[50, 69]` | **Elevated** | Amber (`--state-elevated`) | Best et al. (2021): Slowing reaction times and rising error rates start above 50% capacity saturation. |
| `[70, 89]` | **High** | Coral-red (`--state-high`) | Alahmadi et al. (2022) [USENIX]: Analysts begin skipping enrichment and notes to clear queues rapidly. |
| `[90, 100]` | **Critical** | Saturated Red (`--state-critical`) | Sundaramurthy et al. (2015) / SANS 2025: Burnout threshold; immediate shift rotation is required to prevent severe security omissions. |

