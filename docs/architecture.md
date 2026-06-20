# System Architecture & Data Flow Design

This document details the modular software architecture, data boundaries, and processing pipeline for the **Alert Fatigue Quantifier (AFQ)**.

---

## 1. Pipeline Data Flow

The system is designed with a strict **one-way, acyclic data flow**. No feedback loops, sideways transitions, or circular imports are permitted. This ensures that every phase of the pipeline remains decoupled and testable in isolation.

```mermaid
graph LR
    A[(Raw CSV/JSON Logs)] --> B[Ingestion Module]
    B --> C[Signals Module]
    C --> D[Scoring Module]
    C --> E[Degradation Detector]
    D --> F[Prediction Module]
    E --> F
    F --> G[Recommendation Module]
    G --> H[Streamlit Dashboard]

    style A fill:#161B22,stroke:#30363D,stroke-width:2px,color:#E6EDF3
    style H fill:#1f4a7a,stroke:#58A6FF,stroke-width:2px,color:#E6EDF3
```

---

## 2. Module Boundary and Interface Contracts

The system comprises seven modules. The table below defines the boundaries, input parameters, outputs, and the data types crossing each boundary.

```mermaid
classDiagram
    class Ingestion {
        +parse_logs(path: str) pd.DataFrame
        +validate_schema(df: pd.DataFrame) bool
    }
    class Signals {
        +calculate_rolling_signals(df: pd.DataFrame, window_mins: int) pd.DataFrame
    }
    class Scoring {
        +calibrate_baselines(df: pd.DataFrame) dict
        +calculate_afi(signals_df: pd.DataFrame, baselines: dict) pd.DataFrame
    }
    class Degradation {
        +detect_anomalies(df: pd.DataFrame, baselines: dict) pd.DataFrame
    }
    class Prediction {
        +generate_features(signals_df: pd.DataFrame) pd.DataFrame
        +predict_peak_fatigue(features_df: pd.DataFrame) pd.DataFrame
    }
    class Recommendations {
        +map_afi_to_advisories(afi_df: pd.DataFrame, anomalies_df: pd.DataFrame) list
    }
    class Dashboard {
        +render_ui() StreamlitUI
    }

    Ingestion --> Signals : "pd.DataFrame (validated)"
    Signals --> Scoring : "pd.DataFrame (rolling_metrics)"
    Signals --> Degradation : "pd.DataFrame (rolling_metrics)"
    Scoring --> Prediction : "pd.DataFrame (afi_scores)"
    Degradation --> Prediction : "pd.DataFrame (anomalies)"
    Prediction --> Recommendations : "pd.DataFrame (forecast_results)"
    Recommendations --> Dashboard : "data/output/ JSON / CSV files"
```

### Module Inputs and Outputs

| Component Name | File Boundaries | Core Inputs | Core Outputs | Data Type Crossing Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | `ingestion/parser.py`<br>`ingestion/validator.py` | Raw log file paths (`data/raw/*.csv` or `*.json`) | Validated DataFrame | `pd.DataFrame` with normalized field types |
| **Signals** | `signals/<signal_files>.py`<br>`signals/rolling_window.py` | Validated DataFrame | Rolling 60-min window metrics | `pd.DataFrame` containing rolling signal values per analyst |
| **Scoring** | `scoring/normaliser.py`<br>`scoring/afi_calculator.py`<br>`scoring/baseline_calibrator.py` | Rolling signals and 30-day baseline dictionary | Stored AFI score histories | `pd.DataFrame` containing float AFI values in range `[0, 100]` |
| **Degradation** | `degradation/detector.py`<br>`degradation/mann_whitney.py` | Ingested alert closure types and baseline metrics | Statistical anomaly flags | `pd.DataFrame` of anomalies with p-values from Mann-Whitney U test |
| **Prediction** | `prediction/model.py`<br>`prediction/feature_engineering.py`<br>`prediction/validator.py` | Historical AFI scores and time-series features | Impending fatigue risk forecasts | `pd.DataFrame` of predictions with binary flags (0 = normal, 1 = high risk) |
| **Recommendations** | `recommendations/engine.py` | Final AFI scores and anomaly/predictive warning flags | Advisory action text suggestions | `dict` containing structured advisory text mapping |
| **Dashboard** | `dashboard/app.py`<br>`dashboard/components/*` | Stored pipeline outputs from `data/output/` | Streamlit browser view | Ingests `data/output/` JSON/CSV files; writes zero data |

---

## 3. Configuration Management (`config/settings.py`)

The configuration module `config/settings.py` is the **single source of truth** for all constants:
* It sits entirely outside the pipeline flow.
* It does not import or depend on any pipeline module.
* Every module that requires a constant (e.g., weights, thresholds, durations, paths) must import it directly from `config/settings.py`.
* No magic numbers are permitted in any other file.

---

## 4. The Dashboard Integration Boundary

Consistent with **Rule 1 (Scope)** and **Rule 4 (Architecture)**:
* The Streamlit dashboard (`dashboard/app.py`) is completely decoupled from the processing pipeline.
* The dashboard **never imports or runs** ingestion, scoring, prediction, or recommendation functions directly.
* The dashboard only reads pre-computed JSON and CSV files from `data/output/` at a configurable refresh interval.
* This read-only separation guarantees that dashboard execution cannot impact the performance of the alert pipeline.
