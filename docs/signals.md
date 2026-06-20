# Signal Specifications & Technical Definitions

This document details the exact technical implementation rules, input columns, mathematical operations, and academic validations for the five analyst behavior signals calculated under the `signals/` module.

---

## 1. Summary of Behavioral Signal Specifications

All signals are computed per analyst over a **60-minute rolling window** that slides based on the `closure_timestamp` values in the log stream.

```
Ingested Data Stream
  │
  ├─► signals/triage_interval.py           ──► [Mean Response Time]
  ├─► signals/uninvestigated_closures.py   ──► [Count of Zero-Action Resolves]
  ├─► signals/escalation_deviations.py     ──► [Absolute Rate Deviations]
  ├─► signals/enrichment_depth.py          ──► [Mean Lookup Density]
  └─► signals/hourly_closure_rate.py       ──► [Closure Volatility Ratio]
```

---

## 2. Signal Specifications

### 2.1 Triage Interval
* **Signal Name:** Triage Interval (`triage_interval`)
* **File:** `signals/triage_interval.py`
* **Input Columns:** `triage_timestamp`, `closure_timestamp`, `analyst_id`
* **Window Type:** 60-minute time-based rolling window.
* **Step-by-Step Calculation:**
  1. Convert `triage_timestamp` and `closure_timestamp` to pandas datetime objects.
  2. Compute alert investigation duration for each row:
     $$\Delta t_j = \text{closure\_timestamp}_j - \text{triage\_timestamp}_j \quad \text{(in seconds)}$$
  3. Group rows by `analyst_id` and apply a rolling 60-minute time window index on `closure_timestamp`.
  4. For the current window, calculate the arithmetic mean of $\Delta t$:
     $$\text{Triage Interval} = \frac{1}{N} \sum_{j=1}^{N} \Delta t_j$$
  5. If the window contains zero alerts, return `0.0`.
* **Output Type / Unit:** `float` / Seconds.
* **Direction:** Positive (rising values indicate increasing fatigue).
* **Literature Basis:** SANS Institute (2023) / Al-Mhiqani et al. (2020). Delayed triage response and extended resolution cycles reflect cognitive slowing under heavy load.

---

### 2.2 Uninvestigated Closures
* **Signal Name:** Uninvestigated Closures (`uninvestigated_closures`)
* **File:** `signals/uninvestigated_closures.py`
* **Input Columns:** `closure_type`, `enrichment_actions`, `notes`, `closure_timestamp`, `analyst_id`
* **Window Type:** 60-minute time-based rolling window.
* **Step-by-Step Calculation:**
  1. For each log row, evaluate the "uninvestigated shortcut" criteria:
     $$\text{Shortcut}_j = (\text{closure\_type}_j == \text{'dismissed'}) \land (\text{enrichment\_actions}_j == 0) \land (\text{notes}_j == "")$$
  2. Group rows by `analyst_id` and apply rolling 60-minute time window index on `closure_timestamp`.
  3. Sum the boolean flags to count occurrences:
     $$\text{Uninvestigated Closures} = \sum_{j=1}^{N} \text{Shortcut}_j$$
* **Output Type / Unit:** `int` / Count of alerts.
* **Direction:** Positive (rising values indicate increasing fatigue).
* **Literature Basis:** Alahmadi et al. (2022) [USENIX Security] / Werlinger et al. (2010). Analysts under time pressure bypass data lookup steps and close alerts without rationales to reduce queues.

---

### 2.3 Escalation Deviations
* **Signal Name:** Escalation Deviations (`escalation_deviations`)
* **File:** `signals/escalation_deviations.py`
* **Input Columns:** `escalation_flag`, `closure_timestamp`, `analyst_id`
* **Window Type:** 60-minute time-based rolling window.
* **Step-by-Step Calculation:**
  1. Group rows by `analyst_id` and index on `closure_timestamp`.
  2. For the rolling 60-minute window, calculate the current escalation rate:
     $$\text{Rate}_{\text{window}} = \frac{\sum_{j=1}^{N} (\text{escalation\_flag}_j == \text{True})}{N}$$
     *(If $N == 0$, set $\text{Rate}_{\text{window}} = 0.0$)*
  3. Load the pre-calculated 30-day baseline escalation rate for the analyst ($\text{Rate}_{\text{baseline}}$).
  4. Compute the absolute deviation:
     $$\text{Deviation} = |\text{Rate}_{\text{window}} - \text{Rate}_{\text{baseline}}|$$
* **Output Type / Unit:** `float` / Ratio difference (0.0 to 1.0).
* **Direction:** Positive (rising deviation indicates increasing fatigue).
* **Literature Basis:** Sundaramurthy et al. (2015). Burnout manifests as deviations from standard guidelines, resulting in either excessive escalation (defensive behavior) or insufficient escalation (apathy).

---

### 2.4 Enrichment Depth
* **Signal Name:** Enrichment Depth (`enrichment_depth`)
* **File:** `signals/enrichment_depth.py`
* **Input Columns:** `enrichment_actions`, `closure_timestamp`, `analyst_id`
* **Window Type:** 60-minute time-based rolling window.
* **Step-by-Step Calculation:**
  1. Group rows by `analyst_id` and index on `closure_timestamp`.
  2. For the 60-minute rolling window, calculate the arithmetic mean of enrichment actions:
     $$\text{Enrichment Depth} = \frac{1}{N} \sum_{j=1}^{N} \text{enrichment\_actions}_j$$
  3. If the window contains zero alerts, return `0.0`.
* **Output Type / Unit:** `float` / Mean action count.
* **Direction:** Negative (falling values indicate increasing fatigue).
* **Literature Basis:** Best et al. (2021) / Werlinger et al. (2010). Cognitive fatigue causes "attention narrowing," prompting operators to focus only on main alert fields and omit secondary enrichment checks.

---

### 2.5 Hourly Closure Rate
* **Signal Name:** Hourly Closure Rate (`hourly_closure_rate`)
* **File:** `signals/hourly_closure_rate.py`
* **Input Columns:** `closure_timestamp`, `analyst_id`
* **Window Type:** 60-minute time-based rolling window.
* **Step-by-Step Calculation:**
  1. Group rows by `analyst_id` and index on `closure_timestamp`.
  2. Count the total alerts closed in the rolling 60-minute window ($N_{\text{window}}$).
  3. Load the analyst's 30-day historical mean hourly closures ($\mu_{\text{closures}}$).
  4. Compute the ratio of current throughput to baseline:
     $$\text{Closure Ratio} = \frac{N_{\text{window}}}{\mu_{\text{closures}}}$$
     *(If $\mu_{\text{closures}} == 0$, return $1.0$)*
* **Output Type / Unit:** `float` / Throughput ratio.
* **Direction:** Positive (surges in closures represent speed-pressure fatigue; slowdowns indicate exhaustion. Deviations from $1.0$ are tracked via standard normalization).
* **Literature Basis:** Ponemon Institute (2022) / SANS (2024). Alert volume surges force analysts to accelerate throughput, leading to fatigue, followed by a subsequent drop in performance.
