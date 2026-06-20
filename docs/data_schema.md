# Synthetic Log Dataset Schema

This document specifies the formal data schema, constraints, value ranges, and statistical distributions utilized to generate the synthetic Security Operations Center (SOC) activity logs.

---

## 1. Schema Specifications

The ingestion module expects a CSV or JSON file containing the following 10 fields. All fields are mandatory (no nulls in the key columns).

| Field Name | Type | format / Range | Description | Nullability |
| :--- | :--- | :--- | :--- | :--- |
| `analyst_id` | String | `ANALYST_[0-9]{2}` | Unique identifier for the SOC analyst (e.g., `ANALYST_01`). | Non-Null |
| `alert_id` | String | `ALERT_[0-9]{6}` | Unique identifier for the triggered alert. | Non-Null |
| `triage_timestamp` | String | ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`) | The exact time the alert was assigned to or opened by the analyst. | Non-Null |
| `closure_timestamp` | String | ISO 8601 UTC (must be >= `triage_timestamp`) | The exact time the analyst closed or resolved the alert. | Non-Null |
| `closure_type` | String | `dismissed` \| `investigated` \| `escalated` | The analyst's final resolution for the alert. | Non-Null |
| `severity_assigned` | String | `low` \| `medium` \| `high` \| `critical` | The initial severity rating assigned to the alert by the SIEM rules. | Non-Null |
| `severity_verified` | String | `low` \| `medium` \| `high` \| `critical` | The final severity rating verified/adjusted by the analyst. | Non-Null |
| `enrichment_actions` | Integer | `[0, 50]` | The count of threat-intelligence lookups, log searches, or payload checks. | Non-Null |
| `escalation_flag` | Boolean | `true` \| `false` | Indicates whether the alert was escalated to Tier 2/Tier 3 analysts. | Non-Null |
| `notes` | String | Text, up to 1000 characters | Narrative text logged by the analyst explaining their closure decision. | Nullable (Empty String `""` is permitted) |

---

## 2. Statistical Distribution Design (Based on Literature)

The synthetic logs are programmatically modeled to match actual industry distributions documented by SANS, Ponemon, and USENIX Security research:

### 2.1 Alert Arrival Rate (SANS Institute, 2023)
* **NOMINAL PERIODS:** Alert assignments follow a **Poisson distribution** with $\lambda = 15$ alerts per hour per analyst. This simulates a high-density environment where an alert is assigned roughly every 4 minutes.
* **FATIGUE SURGES:** During simulated alert surges, $\lambda$ increases to $25$ alerts per hour, forcing the analyst into cognitive overload.

### 2.2 Closure Types & False Positives (Ponemon Institute, 2022 / SANS Institute, 2025)
* **NOMINAL RATIO:**
  * `dismissed` (False Positive): $80\%$ of total closures.
  * `investigated` (True Positive, closed): $15\%$.
  * `escalated` (True Positive, sent to Tier 2): $5\%$.
* **FATIGUED RATIO:** During high-fatigue periods, the false positive rate artificially spikes due to shortcutting behavior:
  * `dismissed` increases to $95\%$.
  * `investigated` drops to $4\%$.
  * `escalated` drops to $1\%$.

### 2.3 Investigative Behaviors & Shortcuts (USENIX Security, 2022)
Under alert fatigue, the quality of analyst investigations degrades, which is reflected in these specific distributions:
* **Enrichment Actions:**
  * *Nominal baseline:* Modeled as a **Gamma distribution** with shape $k = 3.0$ and scale $\theta = 2.0$ (mean $\mu = 6.0$ actions per alert).
  * *Fatigued state:* Shifts to a **Gamma distribution** with $k = 1.2$ and $\theta = 1.0$ (mean $\mu = 1.2$ actions per alert), representing analysts skipping validation steps.
* **Notes Length:**
  * *Nominal baseline:* Average notes length follows a **Normal distribution** centered around $120$ characters ($\sigma = 30$).
  * *Fatigued state:* Notes length drops to a mean of $10$ characters, with over $65\%$ of fields left as empty strings (`""`), indicating analysts closing alerts rapidly without documenting rationales.

### 2.4 Time to Action (Triage Interval)
* *Nominal baseline:* Triage interval is modeled as a log-normal distribution with $\mu = 180$ seconds (3 minutes) and $\sigma = 60$ seconds.
* *Fatigued state:* Average triage interval increases to a mean of $480$ seconds (8 minutes) with a standard deviation of $240$ seconds, indicating delayed response and cognitive slowing.
