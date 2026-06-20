# Chapter 5: Conclusion and Future Work

This concluding chapter summarizes the research findings, highlights the project's key academic and practical contributions, acknowledges system limitations, and proposes a roadmap for future development and production integration.

---

## 5.1 Project Summary
The **Alert Fatigue Quantifier (AFQ)** successfully demonstrates the feasibility of monitoring Security Operations Centre (SOC) analyst cognitive load in real-time, using non-intrusive system interaction telemetry. By designing a modular pipeline, the system ingests SIEM logs, evaluates rolling 60-minute behavioral signals, normalizes scores against a 30-day historical baseline, detects decision-quality degradation via Mann-Whitney U testing, and predicts upcoming fatigue spikes using a Random Forest classifier.

The system was validated on a synthetic dataset mimicking SANS and Ponemon distributions. The Random Forest model achieved a **99.92% accuracy** and **94.27% F1-score** in cross-validation, with zero data leakage between train, test, and validation folds. Furthermore, cProfile statistics confirmed that all processing calculations execute within sub-second latency bounds, validating the pipeline's suitability for real-time operational deployment.

---

## 5.2 Key Contributions
This study makes several contributions to the fields of cybersecurity operations and human factors engineering:
1. **Real-time Fatigue Proxy Metric:** Establishes the **Analyst Fatigue Index (AFI)**, a quantitative, log-derived metric (0–100) that captures cognitive fatigue continuously, replacing static, retrospective surveys.
2. **Behavioral Shortcuts Detection:** Proves that non-parametric statistical hypothesis testing (Mann-Whitney U) can identify subtle, statistically significant quality shifts (such as drops in enrichment lookup counts) during a shift.
3. **Proactive Workforce Management:** Integrates predictive machine learning models to forecast operator fatigue *before* errors occur, introducing a human-centric approach to threat detection automation.
4. **Advisory Decision Support:** Maps real-time data to actionable recommendations, providing SOC managers with a tool to rebalance queues without introducing vulnerabilities.

---

## 5.3 System Limitations
While the AFQ achieves its design objectives, several limitations should be noted:
* **Synthetic Data Evaluation:** The system was tested on simulated datasets. In real-world environments, baseline metrics (such as average enrichment counts or triage times) vary significantly across organisations, requiring local calibration.
* **Read-Only Mappings:** The prototype is advisory. It does not interface directly with live alert ticketing queues to automatically reassign incidents, leaving the operational decision entirely with the SOC manager.
* **Literature-Derived Scoring Weights:** The weights assigned to the scoring signals (e.g., $w_1 = 0.25$ for Triage Intervals) are derived from averages in published literature. Training these weights on a large, labeled empirical dataset of actual SOC security omissions is designated for future research.

---

## 5.4 Production Integration Roadmap
To transition the Alert Fatigue Quantifier from a prototype to a production-grade enterprise system, the following integration paths are proposed:

### 5.4.1 Splunk Integration
* **Data Ingestion:** Splunk managers can write a scheduled search that queries the `Splunk REST API` or internal audit index (`_audit` or security event indexes), extracting analyst closure events.
* **Query Example:**
  ```spl
  index=security_ticketing action=close 
  | table analyst_id alert_id _time triage_time closure_type enrichment_count notes_length escalation_flag
  | rename _time as closure_timestamp
  ```
* **Execution:** A Python script runs as a Splunk Alert Action or Modular Input, executing the AFQ scoring pipeline on the table output and writing scored data back to a summary index for visualization.

### 5.4.2 Microsoft Sentinel Integration
* **Data Ingestion:** Log Analytics workspaces store analyst ticketing logs in the `SecurityIncident` table.
* **Query Example:**
  ```kql
  SecurityIncident
  | where Status == "Closed"
  | project Analyst = Owner, IncidentId = IncidentNumber, ClosedTime = TimeGenerated, TriageTime = CreatedTime, Classification, NotesLength = strlen(Comments)
  ```
* **Execution:** A **Microsoft Sentinel Logic App** triggers upon incident closure, posting the telemetry payload to a hosted AFQ Azure Function. The function processes the scores and updates Sentinel Owner work lists or alerts managers via Microsoft Teams if an analyst's AFI crosses the critical threshold.

### 5.4.3 IBM QRadar Integration
* **Data Ingestion:** Ingests events from QRadar's ticketing logs using the **QRadar REST API** (`/api/siem/offenses`).
* **Execution:** QRadar App Framework hosts the AFQ service locally, showing the manager dashboard inside a custom tab in the QRadar Console.
