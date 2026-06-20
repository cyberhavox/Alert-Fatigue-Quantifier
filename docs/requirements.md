# Requirement Analysis & System Specification

This document details the functional specifications, signal behaviors, mathematical structures, and interface contracts for the Alert Fatigue Quantifier (AFQ) system.

---

## 1. The Five Analyst Fatigue Index (AFI) Signals

All behavioral signals are computed per analyst over a rolling **60-minute window** (configurable via config) and compared to their individual 30-day historical baseline.

| Signal Name | Definition | Measurement Unit | Rolling Window Calculation Logic |
| :--- | :--- | :--- | :--- |
| **Triage Interval** | Mean duration between alert assignment/ingestion and the analyst's first recorded action. | Seconds | Find all alerts assigned within the 60-min window. Calculate: $\text{Mean}(t_{\text{action}} - t_{\text{triage}})$. If no alerts are triaged, default is 0. |
| **Uninvestigated Closures** | Total number of alerts marked as resolved/closed without any enrichment steps or accompanying notes. | Integer (Count) | Filter alerts closed in the window where `enrichment_actions == 0` AND `notes == ""`. Count the total. |
| **Escalation Deviations** | Absolute deviation of the analyst's current escalation rate from their historical baseline escalation rate. | Percentage Points | Calculate: $|\text{Rate}_{\text{window}} - \text{Rate}_{\text{baseline}}|$, where $\text{Rate} = \frac{\text{escalated alerts}}{\text{total closed alerts}}$. |
| **Enrichment Depth** | Mean number of investigative/enrichment actions performed per alert. | Float (Mean Count) | Sum the value of `enrichment_actions` for all alerts closed in the window, divided by the total count of closed alerts. |
| **Hourly Closure Rate** | The rate of alert closures compared to the analyst's historical baseline closure rate. | Ratio | Calculate: $\frac{\text{Alerts Closed in Window}}{\text{Baseline Mean Hourly Closures}}$. A ratio $> 1.0$ indicates a surge; $< 1.0$ indicates a slowdown. |

---

## 2. AFI Scoring & Normalization Structure

The scoring engine aggregates these signals to produce a normalized Analyst Fatigue Index (AFI):

1. **Baseline Ingestion:** Load the analyst's historical 30-day performance baseline parameters, specifically the mean ($\mu$) and standard deviation ($\sigma$) for each of the five signals.
2. **z-Score Normalization:** For each signal $i$, compute the z-score using SciPy:
   $$z_i = \frac{x_i - \mu_i}{\sigma_i}$$
   *Note: For signals where a decrease indicates fatigue (Enrichment Depth), the z-score is negated to ensure positive values represent higher fatigue.*
3. **Sigmoid Scaling:** Map the z-score to a $[0, 1]$ probability range to prevent extreme outliers from skewing the final score:
   $$S(z_i) = \frac{1}{1 + e^{-z_i}}$$
4. **Weighted Aggregation:** Compute the composite score by applying literature-derived weights (weights finalized in Week 3 based on citation values):
   $$\text{Raw AFI} = \sum_{i=1}^{5} w_i \cdot S(z_i) \quad \text{where} \quad \sum w_i = 1.0$$
5. **Output Constraints:** Scale the raw AFI to the final range:
   $$\text{AFI} = \text{Raw AFI} \times 100 \in [0, 100]$$

---

## 3. Module Interface Contracts (Input/Output)

To enforce the single-direction data flow, each module exposes strict inputs and outputs:

### 3.1 Configuration Module (`config/settings.py`)
* **Input:** None.
* **Output:** Named constants (constants, paths, weights, thresholds) imported by all other modules.

### 3.2 Ingestion Module (`ingestion/`)
* **Input:** Raw log exports (CSV or JSON format) located in `data/raw/`.
* **Output:** A structured, validated pandas DataFrame containing normalized field names and data types, passed to the Signals module.

### 3.3 Signal Module (`signals/`)
* **Input:** Validated pandas DataFrame from the Ingestion module.
* **Output:** A computed feature DataFrame containing rolling 60-minute window signal metrics for each active analyst.

### 3.4 Scoring Module (`scoring/`)
* **Input:** Computed signals DataFrame and stored baseline parameters (from `data/baseline/`).
* **Output:** Stored time-series files (`data/output/`) containing the computed AFI (0-100) per analyst per window.

### 3.5 Degradation Detector (`degradation/`)
* **Input:** Current window closure behaviors (enrichments, closure types) and baseline records.
* **Output:** Timestamps and details of flagged anomalies where current behavior statistically deviates from the baseline (using SciPy Mann–Whitney U test at $p < 0.05$).

### 3.6 Prediction Module (`prediction/`)
* **Input:** Historical signal sequences and time features.
* **Output:** A trained Random Forest model artifact and real-time binary prediction flags indicating impending peak fatigue periods (0 = normal, 1 = high risk).

### 3.7 Recommendation Module (`recommendations/`)
* **Input:** Current AFI scores and active anomaly/prediction warning flags.
* **Output:** Structured advisory recommendations as text suggestions (e.g., alert suppression, shift rotation handovers).

### 3.8 Streamlit Dashboard (`dashboard/`)
* **Input:** Read-only output files from `data/output/` (AFI scores, signals history, anomaly logs, recommendations).
* **Output:** Web browser UI rendering interactive gauges, trend lines, anomaly tables, and recommendation cards.
