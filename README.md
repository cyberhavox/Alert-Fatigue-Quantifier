<div align="center">

<br/>

```
  █████╗ ███████╗ ██████╗ 
 ██╔══██╗██╔════╝██╔═══██╗
 ███████║█████╗  ██║   ██║
 ██╔══██║██╔══╝  ██║▄▄ ██║
 ██║  ██║██║     ╚██████╔╝
 ╚═╝  ╚═╝╚═╝      ╚══▀▀═╝ 
```

# Alert Fatigue Quantifier

**Real-time cognitive load monitoring for Security Operations Centre analysts.**  
Compute rolling fatigue scores, detect behavioral degradation, and forecast risk — before breaches happen.

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5%2B-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-533afd?style=flat-square)](LICENSE)
[![MCA Project](https://img.shields.io/badge/MCA%20Project-JAIN%20Online-1c1e54?style=flat-square)](https://jainonline.ac.in)

<br/>

</div>

---

## The Problem

Modern SOCs process **9,000+ alerts per analyst per week** — the majority false positives. When cognitive capacity saturates, analysts shorten triage times, skip enrichment steps, and close alerts without investigation. The result: **real threats slip through**.

No existing tool measures this degradation in real time, from the analyst's own activity logs, during an active shift.

**AFQ fixes that.**

---

## What It Does

```
Raw Alert Logs  ──►  Signal Extraction  ──►  AFI Score (0–100)
                                          │
                                          ├──►  Anomaly Detection (Mann–Whitney U)
                                          │
                                          └──►  Risk Forecast (Random Forest)
                                                        │
                                                        ▼
                                             Advisory Dashboard (Streamlit)
```

| Component | Method | Output |
|---|---|---|
| **Analyst Fatigue Index** | Weighted z-score normalisation across 5 signals | 0–100 score per analyst |
| **Anomaly Detection** | Two-sided Mann–Whitney U test vs 30-day baseline | Flagged degradation events |
| **Risk Forecast** | Random Forest classifier (99.9% accuracy, 98.4% recall) | Impending fatigue prediction |
| **Dashboard** | Streamlit + Stripi Design Language | Live advisory UI |

---

## Five Behavioral Signals

| Signal | What It Measures | Fatigue Indicator |
|---|---|---|
| `triage_interval` | Time from alert assignment to first action | Rising = analyst overwhelmed |
| `enrichment_depth` | Threat intel queries and log checks per alert | Falling = shortcuts taken |
| `uninvestigated_closures` | Alerts closed with zero enrichment | Rising = dangerous dismissals |
| `escalation_deviations` | Escalation rate drift from 30-day norm | Deviation = judgment impaired |
| `hourly_closure_rate` | Alerts processed per hour vs baseline | Surge = burnout pattern |

---

## Dashboard

> Live monitoring across all analysts. Shift status grid, signal trend charts, anomaly audit log, and ML forecast panel — all in one view.

<div align="center">

**[Live Demo →](https://alert-fatigue-quantifier.streamlit.app)**

</div>

---

## Project Structure

```
alert-fatigue-quantifier/
│
├── config/
│   └── settings.py              # Single source of truth — all constants, weights, thresholds
│
├── ingestion/
│   ├── parser.py                # CSV/JSON alert log ingestion
│   └── validator.py             # Pydantic schema validation
│
├── signals/
│   ├── rolling_window.py        # 60-minute sliding window engine
│   ├── triage_interval.py       # Log-normal triage delta computation
│   ├── enrichment_depth.py      # Gamma-distributed enrichment scoring
│   ├── uninvestigated_closures.py
│   ├── escalation_deviations.py
│   └── hourly_closure_rate.py
│
├── scoring/
│   ├── baseline_calibrator.py   # 30-day per-analyst baseline computation
│   ├── normaliser.py            # SciPy z-score normalisation
│   └── afi_calculator.py        # Weighted AFI composite (0–100)
│
├── degradation/
│   ├── mann_whitney.py          # Two-sided Mann–Whitney U implementation
│   └── detector.py              # Anomaly flagging with p-value thresholds
│
├── prediction/
│   ├── feature_engineering.py   # Feature matrix construction
│   ├── model.py                 # Random Forest training and inference
│   └── validator.py             # Model performance validation
│
├── recommendations/
│   └── engine.py                # Read-only advisory rule engine
│
├── dashboard/
│   ├── app.py                   # Streamlit main entry point
│   ├── styles/theme.css         # Stripi design language tokens
│   └── components/
│       ├── analyst_card.py      # Shift status card per analyst
│       ├── signal_charts.py     # Rolling trend charts (Matplotlib)
│       ├── anomaly_log.py       # Degradation event audit table
│       ├── forecast_panel.py    # ML risk probability timeline
│       └── recommendation_panel.py
│
├── scripts/
│   ├── generate_synthetic_data.py   # SANS/Ponemon-calibrated log generator
│   └── run_full_pipeline.py         # End-to-end E2E pipeline runner
│
├── tests/                       # Pytest suite — 1:1 module coverage
│   ├── ingestion/
│   ├── signals/
│   ├── scoring/
│   ├── degradation/
│   ├── prediction/
│   ├── recommendations/
│   └── test_integration.py
│
└── data/
    ├── raw/          # Analyst log CSVs (git-ignored)
    ├── baseline/     # Per-analyst 30-day baseline stats (git-ignored)
    ├── output/       # Scored alerts and anomalies (git-ignored)
    └── models/       # Trained Random Forest pickle (git-ignored)
```

---

## Quickstart

### Prerequisites

```bash
pip install -r requirements.txt
```

> Requires Python 3.10+. All dependencies use `>=` version specifiers for Python 3.13 compatibility.

### 1 — Generate Synthetic Data

Produces ~54,000 analyst log records across 5 analysts (30-day baseline + active shift). Distributions calibrated to SANS 2025 and Ponemon 2022 SOC research.

```bash
python scripts/generate_synthetic_data.py
```

### 2 — Run the Pipeline

Ingests logs → extracts signals → calibrates baselines → computes AFI scores → detects anomalies → trains Random Forest → writes outputs.

```bash
python scripts/run_full_pipeline.py
```

**Expected output:**
```
Model Accuracy : 0.9992
Model Recall   : 0.9840
Scored rows    : 54,081
Anomalies found: 5
Pipeline complete.
```

### 3 — Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`

### 4 — Run Tests

```bash
pytest tests/ -v
```

---

## Model Performance

| Metric | Value |
|---|---|
| Accuracy | **99.92%** |
| Recall (fatigue class) | **98.40%** |
| Precision | **99.91%** |
| Algorithm | Random Forest (100 estimators) |
| Features | 14 engineered signal features |
| Training set | 30-day rolling baseline per analyst |

---

## Synthetic Data Methodology

Real SOC alert logs are confidential. AFQ uses **statistically validated synthetic data** — the accepted methodology for academic cybersecurity behavioral research.

Distribution parameters are sourced from:
- SANS Institute SOC Survey 2023 / 2024 / 2025
- Ponemon Institute *Cost of False Positives* 2022
- Alahmadi et al., USENIX Security 2022
- Shirley et al., IEEE Transactions on Human-Machine Systems 2023

| Parameter | Nominal | Fatigued |
|---|---|---|
| Alert arrival rate (λ) | 15 / hour | 28 / hour |
| Triage interval | Log-Normal(µ=180s, σ=60s) | Log-Normal(µ=420s, σ=120s) |
| Enrichment actions | Gamma(k=6, θ=1) | Gamma(k=1.2, θ=0.4) |
| False positive dismissal rate | 80% | 95% |

---

## Research Context

> **Research Gap:** No existing commercial or academic tool measures live cognitive fatigue from SOC analyst interaction logs during an active shift. Existing work either addresses alert volume at the SIEM level (system-side) or burnout retrospectively via HR surveys (post-incident).

AFQ bridges this gap — read-only, non-punitive, advisor-mode only.

**18 peer-reviewed sources** from IEEE, ACM, USENIX, SOUPS, and SANS/Ponemon industry surveys.

---

## Academic Details

| Field | Value |
|---|---|
| **Author** | Raghav Gupta |
| **USN** | 241VMTR01929 |
| **Institution** | JAIN Online (Deemed-to-be University) |
| **Program** | Master of Computer Applications (MCA) |
| **Elective** | Cyber Security |
| **Supervisor** | Prof. Maya Manishankar |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Dashboard | Streamlit 1.35+ |
| ML | scikit-learn (Random Forest) |
| Statistics | SciPy (Mann–Whitney U, z-score) |
| Data | pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Design | Stripi Design Language (Inter 300, indigo `#533afd`) |
| Testing | pytest |

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
<sub>Built for academic research. Advisory-only. Not intended for production SOC deployment without institutional review.</sub>
</div>
