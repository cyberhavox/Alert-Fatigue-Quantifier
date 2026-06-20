# Research Project Synopsis

## 1. Project Metadata

* **Title:** Alert Fatigue Quantifier: A Data-Driven Cognitive Load Monitoring System for SOC Analysts
* **Author:** Raghav Gupta
* **USN:** 241VMTR01929
* **Institution:** JAIN Online (Deemed-to-be University)
* **Academic Program:** Master of Computer Applications (MCA)
* **Semester / Elective:** Semester IV / Cyber Security Elective

---

## 2. Problem Statement

Security Operations Centers (SOCs) run on a simple premise: human analysts monitor security alerts, investigate threat activities, and respond to incidents before damage occurs. However, this system fails quietly in practice. Modern Security Information and Event Management (SIEM) platforms generate thousands of alerts daily, far exceeding the processing capacity of security analyst teams. The Ponemon Institute found that SOC teams receive an average of 9,854 false positive alerts every week (2022). Furthermore, SANS Institute surveys show that 66% of SOC teams cannot keep pace with their alert queues, leading to a state of chronic workload saturation (2023).

Under the influence of alert fatigue, analysts are forced to adapt by cutting corners. They close alerts without thorough investigation, accept default severity ratings without verifying the underlying logs, and dismiss up to 44% of alerts without any enrichment during peak fatigue periods. 

The core technical and academic gap is specific: **no existing cybersecurity tool measures live mental fatigue for individual analysts during a shift.** Existing tools focus either on reducing alert volume at the SIEM layer or evaluating burnout retrospectively through post-incident human resource surveys. Neither approach provides real-time alerts to managers when an analyst's decision quality begins to degrade. This project builds a non-intrusive, continuous early-warning system that tracks behavioral indicators directly from interaction logs and computes a dynamic Analyst Fatigue Index (AFI).

---

## 3. Objectives of the Research

This project is structured around five primary research objectives:

1. **Real-time Fatigue Scoring Framework:** Design and evaluate a quantitative model that aggregates five live behavioral signals (triage intervals, uninvestigated closures, escalation deviations, enrichment depth, and hourly closure rates) into a single Analyst Fatigue Index (AFI) scaled from 0 to 100, normalized against an analyst's 30-day baseline.
2. **Decision Quality Anomaly Detection:** Build and validate a statistical method that compares current alert closure types and enrichment patterns against historical baselines using the Mann–Whitney U test to detect drops in investigation quality.
3. **Predictive Fatigue Modeling:** Train a Random Forest classifier utilizing alert timing, volume patterns, and rolling behavioral signals to forecast peak fatigue periods, enabling SOC managers to rebalance workloads before operational safety thresholds are crossed.
4. **Queue Optimization Engine:** Develop an advisory algorithm mapping the computed AFI levels to specific queue adjustments (temporary alert suppression, optimized shift handovers) to mitigate cognitive load without introducing security vulnerabilities.
5. **Research Contribution:** Package a validated, reproducible, and standardized fatigue measurement pipeline based on standard logs, contributing the AFI framework to the cybersecurity research community for future empirical studies.

---

## 4. Research Methodology

* **Research Type:** Empirical. The study relies on observing and quantifying analyst behavior through interaction metrics.
* **Data Collection Method:** Secondary-Synthetic. Due to the high sensitivity and proprietary nature of live SOC incident data, the project uses a synthetic generator that produces activity logs. These logs are programmatically configured to match statistical distributions published in cybersecurity industry research (SANS, Ponemon, USENIX).
* **SDLC Model:** Agile SDLC with two-week sprints. The Agile approach is selected because the scoring logic and statistical thresholds require early, iterative testing against simulated data. A Waterfall approach would delay testing until the end of development, making it difficult to tune the AFI weights and anomaly detection parameters based on initial results.

---

## 5. Technology Stack

The project utilizes a locked, compliant Python technology stack:

| Layer | Library / Tool | Version | Responsibility |
| :--- | :--- | :--- | :--- |
| Language | Python | 3.10 | Core runtime environment |
| Data Processing | Pandas, NumPy | 2.2.2, 1.26.4 | Log parsing, feature engineering, and rolling window calculation |
| Statistics | SciPy | 1.13.0 | z-score normalization and Mann–Whitney U testing |
| Machine Learning | Scikit-Learn | 1.5.0 | Random Forest model training, validation, and prediction |
| Visualization | Matplotlib, Seaborn | 3.9.0, 0.13.2 | Static trend line and distribution chart generation |
| Dashboard UI | Streamlit | 1.35.0 | Web-based operational monitoring surface for managers |
| Testing | PyTest | 8.2.0 | Automated unit tests for signals and pipeline validation |
| Data I/O | CSV, JSON | Standard | Raw log input files and pipeline output exchanges |

---

## 6. System Architecture & Data Flow

The Alert Fatigue Quantifier is designed as a modular pipeline with a strict single-direction data flow, physically enforced by the package structure:

```
[Raw CSV/JSON Logs] 
      │
      ▼
1. Ingestion Module (parser.py + validator.py)
      │
      ▼
2. Signal Module (5 signal calculators + rolling_window.py)
      │
      ▼
3. Scoring Module (normaliser.py + afi_calculator.py + baseline_calibrator.py)
   & Degradation Detector (detector.py + mann_whitney.py)
      │
      ▼
4. Prediction Module (model.py + feature_engineering.py)
      │
      ▼
5. Recommendation Module (engine.py)
      │
      ▼
6. Streamlit Dashboard (app.py + UI components)
```

No downstream module is imported into an upstream one, and the dashboard remains entirely decoupled from any business logic, acting strictly as a display layer.

---

## 7. Testing & Performance Approach

* **Unit Testing:** PyTest runs unit tests for each signal calculation function under `tests/signals/` using mock inputs, covering normal, edge (empty windows, single records), and anomalous scenarios.
* **Model Validation:** The Random Forest classifier is validated using a 70/30 train-test split. A k-fold cross-validation strategy is executed, ensuring no data leakage, and standard metrics (accuracy, precision, recall, and F1-score) are logged.
* **Performance Profiling:** Python's standard `cProfile` module profiles Pandas rolling window operations, ensuring that the ingestion and scoring engine processes files within acceptable operational time constraints.

---

## 8. Known Limitations

* **Read-Only / Advisory:** The system does not write to or modify SIEM queues, ServiceDesk environments, or ticketing systems. Recommendations are suggestions only; human SOC managers retain full authority.
* **Synthetic Log Input:** The model is evaluated on simulated data. Live organizational deployment would require calibrating the baseline against real environment logs.
* **Literature-Derived Weights:** Scoring weights are derived from statistical ratios in existing literature. Training these weights on a large, labeled real-world SOC dataset is designated for future research.

---

## 9. 8-Week Work Plan

| Week | Phase | Focus Activities | Deliverables |
| :--- | :--- | :--- | :--- |
| **Week 1** | Inception | Literature review Phase 1 (9 sources); topic finalization; synthetic schema definition. | `README.md` skeleton, `.gitignore`, reference documents. |
| **Week 2** | Requirements | Literature review Phase 2 (9 sources); requirement analysis; synopsis draft. | `docs/data_schema.md`, `docs/afi_formula.md` (drafts), updated `README.md`. |
| **Week 3** | System Design | Pipeline data flow architecture; AFI weight derivations; signal window specs. | Complete `docs/`, `config/settings.py` skeleton. |
| **Week 4** | UML & Data Gen | UML class/sequence diagrams; baseline and anomaly logic; data generation scripts. | `scripts/generate_synthetic_data.py`, `data/raw/` logs. |
| **Week 5** | Pipeline Build | Ingestion parser; signal rolling functions; baseline scoring calibration. | `ingestion/`, `signals/`, and `scoring/` source packages. |
| **Week 6** | ML & UI Build | Degradation detector; Random Forest training; Streamlit dashboard interface. | `degradation/`, `prediction/`, `recommendations/`, `dashboard/`. |
| **Week 7** | Quality Gate | PyTest signal unit tests; k-fold model evaluation; cProfile optimization; E2E tests. | Pass pytest, profile logs, dashboard polish. |
| **Week 8** | Wrap-Up | Report writing (5 chapters); reference styling; presentation recording. | Final PDF thesis, presentation video, clean repository. |
