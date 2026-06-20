# Agent Briefing: Alert Fatigue Quantifier

## Project Identity

**Title:** Alert Fatigue Quantifier: A Data-Driven Cognitive Load Monitoring System for SOC Analysts
**Author:** Raghav Gupta | USN: 241VMTR01929
**Institution:** JAIN Online (Deemed-to-be University) | Semester IV | Cyber Security Elective
**Current Sprint:** Week 1 of 8-week Agile plan (two-week sprints)

---

## Mission Statement

Build a continuous, real-time early-warning system that measures mental fatigue for individual SOC analysts during a live shift — without interfering with live workflows.

---

## Core Problem Being Solved

Modern SIEM platforms generate thousands of alerts per day. SOC analysts are overwhelmed: the Ponemon Institute documented an average of 9,854 false positive alerts per week per team (Ponemon Institute, 2022), and SANS Institute surveys show 66% of SOC teams cannot keep pace with their queues (SANS Institute, 2023). Analysts dismiss up to 44% of alerts without investigation during peak fatigue periods (SANS Institute, 2023).

The gap this project fills: **no existing cybersecurity tool measures live mental fatigue for individual analysts during a shift.** Current tools either reduce alert volume or assess burnout post-incident via surveys. Neither provides real-time warnings when decision quality drops.

---

## Research Type & Data Collection

- **Research Type:** Empirical
- **Data Collection Method:** Secondary-Synthetic — datasets generated to match statistical distributions from published SOC industry research (SANS Institute, Ponemon Institute, USENIX, IEEE, ACM Computing Surveys)
- **SDLC Model:** Agile with two-week sprints. Agile is chosen because the scoring logic needs early testing against data to refine formulas based on real results. A Waterfall model would delay this feedback.

---

## Five Research Objectives

| # | Objective | Description |
|---|-----------|-------------|
| 1 | Real-time Fatigue Scoring Framework | Design and evaluate a quantitative model combining live behavioral signals (alert volume, time-to-triage, escalation deviations) into an Analyst Fatigue Index (AFI), normalized against a 30-day per-analyst baseline |
| 2 | Decision Quality Anomaly Detection | Build and test a method comparing current alert closure patterns against historical baselines to detect drops in investigation quality (e.g., rising false-positive rates) |
| 3 | Predictive Fatigue Modeling | Build a Random Forest classifier using alert timing and volume patterns to predict peak fatigue periods, enabling managers to rebalance workloads before operational safety limits are reached |
| 4 | Queue Optimization Engine | Build an algorithm mapping fatigue levels to queue adjustments (temporary alert suppression, optimized shift handovers) to reduce cognitive load without leaving the network vulnerable |
| 5 | Research Contribution | Share a validated, reproducible method for measuring analyst fatigue based on standard logs, providing the cybersecurity research community with a standardized metric (AFI) for future empirical studies |

---

## System Architecture

The application is strictly modular. Each component below is a **separate module** — never collapsed into a single script. System requirements were gathered by reviewing 18 academic and industry publications (SANS surveys, Ponemon reports, USENIX papers on analyst workload), confirming that no real-time, log-based fatigue tracking system currently exists.

> **Authoritative reference:** `docs/folder_structure.md` defines the complete file and folder layout, per-file responsibilities, naming conventions, sprint–folder mapping, and the pinned `requirements.txt`. Use it as the single source of truth for where every file lives and what it contains. The outline below is a pipeline summary only.

```
alert-fatigue-quantifier/
├── config/             # All named constants: weights, thresholds, paths, window size
├── data/               # raw/, baseline/, output/ — generated files, never committed
├── scripts/            # Synthetic data generator (Week 4)
├── ingestion/          # Reads and parses CSV/JSON log exports
├── signals/            # Calculates 5 behavioral indicators over 60-min rolling windows
├── scoring/            # Normalizes signals → AFI (0–100) per analyst baseline
├── degradation/        # Detects anomalies in false-positive closure rates
├── prediction/         # Random Forest model; flags rising fatigue trends
├── recommendations/    # Maps AFI level → advisory queue adjustments
├── dashboard/          # Streamlit web UI: live gauges, trend charts, recommendations
├── tests/              # PyTest suite mirroring the source tree 1:1
└── docs/               # agent.md, rules.md, design.md, folder_structure.md, afi_formula.md
```

### Module Specifications

**Ingestion Module**
- Reads standard CSV and JSON log exports
- Handles schema validation and normalization
- Input fields: `analyst_id`, `alert_id`, `triage_timestamp`, `closure_timestamp`, `closure_type`, `severity_assigned`, `severity_verified`, `enrichment_actions`, `escalation_flag`, `notes`

**Signal Module**
Calculates five indicators over **60-minute rolling windows**:

| Signal | Description |
|--------|-------------|
| Triage Interval | Average time between alert assignment and first analyst action |
| Uninvestigated Closures | Count of alerts closed without enrichment or notes |
| Escalation Deviations | Divergence from analyst's baseline escalation rate |
| Enrichment Depth | Average number of enrichment actions taken per alert |
| Hourly Closure Rate | Total alerts closed per hour vs. baseline |

**Scoring Module**
- Normalizes all five signal outputs using z-score normalization (SciPy)
- Applies literature-derived weights to produce a single AFI (0–100)
- Calibrates against each analyst's individual 30-day historical baseline

**Degradation Detector**
- Compares current false-positive closure rate to the analyst's historical baseline
- Uses Mann–Whitney U test (SciPy) to flag statistically significant anomalies

**Prediction Module**
- Scikit-Learn Random Forest classifier
- Features: alert volume patterns, timing patterns, rolling signal values
- Output: binary flag for impending peak fatigue period
- Validation: 70/30 train-test split + k-fold cross-validation

**Recommendation Module**
- Advisory engine only — read-only, never modifies live systems
- Maps AFI threshold levels to suggested queue adjustments (e.g., temporary alert suppression, optimized shift handovers)
- Thresholds must be derived from literature — no arbitrary bands are permitted

**Streamlit Dashboard**
- Live AFI gauge per analyst
- Rolling trend charts for each signal
- Degradation anomaly alerts
- Predictive fatigue warnings
- Advisory recommendations panel
- No write access to any external system
- Streamlit's hot-reload feature is used during development for faster iteration

> **Authoritative reference:** `docs/design.md` is the single source of truth for all dashboard decisions — colour tokens, typography, layout wireframes, component behaviour, copy standards, Streamlit `config.toml`, and accessibility requirements. No dashboard code may be written without first reading `design.md`.

---

## Data Flow

Single-direction only. No feedback loops, no writes to external systems.

```
Raw Logs (CSV/JSON)
    → Ingestion Module
        → Signal Module
            → Scoring Module + Degradation Detector
                → Prediction Module
                    → Recommendation Module
                        → Streamlit Dashboard
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10 |
| Data Processing | Pandas, NumPy |
| Statistics | SciPy (z-score normalization, Mann–Whitney U tests) |
| Machine Learning | Scikit-Learn (Random Forest) |
| Visualization | Matplotlib, Seaborn |
| Dashboard / UI | Streamlit |
| Version Control | Git |
| Data I/O | CSV and JSON files only |

No other libraries, frameworks, or external dependencies are permitted.

---

## Testing, Profiling & Debugging

- **Unit Tests:** PyTest for every signal calculation function, using custom sample (mock) inputs
- **Model Validation:** 70/30 train-test split + k-fold cross-validation to prevent overfitting
- **Performance Profiling:** Python `cProfile` on all Pandas operations to ensure fast processing
- **Debugging:** VS Code debugger used to trace signal values at each pipeline stage
- **Dashboard Iteration:** Streamlit's hot-reload feature used during dashboard development
- **Integration Tests:** End-to-end pipeline run in Week 7

---

## 8-Week Sprint Plan (Reference)

> **Authoritative reference:** `docs/folder_structure.md` §Sprint–Folder Mapping defines exactly which folders and files are created each week. The table below is a task summary; the folder structure document governs what gets built and where.

| Week | Focus |
|------|-------|
| 1 | Literature review Phase 1 (9 sources: SANS, Ponemon, USENIX); topic finalization; synthetic dataset schema design (fields: analyst ID, alert ID, triage times, closure types, notes) |
| 2 | Literature review Phase 2 (9 sources: IEEE, ACM, security conferences); synopsis draft + plagiarism check + ERP upload; requirement analysis — finalize AFI signals and scoring formula structure |
| 3 | System architecture design — data flow diagrams; derive AFI weights from literature significance values; document five signal definitions and 60-minute window calculations |
| 4 | UML class and sequence diagrams for all five modules; degradation detector baseline logic and threshold calculations; synthetic CSV log generation scripts |
| 5 | Build ingestion module (parser, validation, schema normalization); build signal engine (Pandas window functions, SciPy z-score routines); build scoring module (0–100 logic, per-analyst baseline calibration); Git repository setup |
| 6 | Implement degradation detector; train Random Forest model and set up validation; build recommendation engine; build Streamlit dashboard (gauges, charts, recommendations) |
| 7 | PyTest unit tests for all signal functions; k-fold cross-validation and cProfile profiling; debug and refine (edge cases, dashboard polish); end-to-end integration tests |
| 8 | Draft final report (five chapters per university guidelines); compile 18 APA references + plagiarism check; record five-minute presentation; prepare for viva |

---

## Known Limitations (Do Not Exceed Scope)

- System is **read-only and advisory** — it cannot modify SIEM platforms, ServiceDesk tools, or alert queues
- Data is **synthetic only** — no live API integrations to Splunk, Sentinel, or QRadar
- Validation focuses on behavioral patterns rather than actual security incidents; organizations would need to re-validate with their own baseline data
- Recommendation engine **suggests** adjustments only; operational decisions remain entirely with the SOC manager — no automated enforcement
- AFI formula weights are derived from existing literature — future research should train these weights using supervised learning on larger real SOC datasets
- This is an **8-week academic project** — scope creep beyond the five objectives is not permitted
