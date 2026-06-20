# System UML Diagrams

This document contains the structural and behavioral UML specifications for the **Alert Fatigue Quantifier (AFQ)** system.

---

## 1. Class Diagram

The class diagram below illustrates the attributes, methods, and relationships of the modular classes across the 7 pipeline stages.

```mermaid
classDiagram
    class ConfigSettings {
        <<global>>
        +WEIGHT_TRIAGE_INTERVAL: float
        +WEIGHT_UNINVESTIGATED_CLOSURES: float
        +WEIGHT_ENRICHMENT_DEPTH: float
        +WEIGHT_ESCALATION_DEVIATIONS: float
        +WEIGHT_HOURLY_CLOSURE_RATE: float
        +THRESHOLD_NOMINAL_MAX: float
        +THRESHOLD_ELEVATED_MAX: float
        +THRESHOLD_HIGH_MAX: float
        +THRESHOLD_CRITICAL_MIN: float
        +ROLLING_WINDOW_MINUTES: int
        +BASELINE_DAYS: int
        +PATH_RAW_LOGS: str
        +PATH_BASELINE_LOGS: str
        +PATH_OUTPUT_LOGS: str
    }

    class Parser {
        +parse_csv(file_path: str) pd.DataFrame
        +parse_json(file_path: str) pd.DataFrame
    }

    class Validator {
        +validate_schema(df: pd.DataFrame) bool
        +check_data_ranges(df: pd.DataFrame) bool
    }

    class SignalEngine {
        +calculate_triage_interval(df: pd.DataFrame, window_mins: int) pd.DataFrame
        +calculate_uninvestigated_closures(df: pd.DataFrame, window_mins: int) pd.DataFrame
        +calculate_escalation_deviations(df: pd.DataFrame, window_mins: int) pd.DataFrame
        +calculate_enrichment_depth(df: pd.DataFrame, window_mins: int) pd.DataFrame
        +calculate_hourly_closure_rate(df: pd.DataFrame, window_mins: int) pd.DataFrame
    }

    class BaselineCalibrator {
        +build_analyst_baseline(df: pd.DataFrame, baseline_days: int) dict
        +load_baseline(analyst_id: str) dict
        +store_baseline(analyst_id: str, baseline: dict) None
    }

    class Normaliser {
        +normalise_zscore(value: float, mean: float, std: float) float
        +apply_sigmoid(z_score: float) float
    }

    class AfiCalculator {
        +calculate_score(normalised_signals: dict, weights: dict) float
    }

    class DegradationDetector {
        +compare_to_baseline(current_df: pd.DataFrame, baseline_df: pd.DataFrame) float
        +detect_anomalies(df: pd.DataFrame) pd.DataFrame
    }

    class PredictiveModel {
        -rf_classifier: RandomForestClassifier
        +train(features: pd.DataFrame, labels: pd.Series) None
        +predict_impending_fatigue(features: pd.DataFrame) pd.Series
        +save_model(path: str) None
        +load_model(path: str) None
    }

    class RecommendationEngine {
        +map_afi_to_advisory(afi_score: float) str
        +generate_actions(afi_score: float, anomalies: list) dict
    }

    class DashboardApp {
        +load_dashboard_data() dict
        +render_main_layout() None
    }

    %% Relationships
    Parser ..> Validator : "validates data"
    Validator --> SignalEngine : "pandas.DataFrame"
    SignalEngine --> Normaliser : "raw signal values"
    BaselineCalibrator --> Normaliser : "baseline mean/std parameters"
    Normaliser --> AfiCalculator : "sigmoid-scaled z-scores"
    SignalEngine --> DegradationDetector : "closure behaviors"
    AfiCalculator --> PredictiveModel : "rolling AFI time-series"
    AfiCalculator --> RecommendationEngine : "active AFI scores"
    DegradationDetector --> RecommendationEngine : "active anomaly flags"
    PredictiveModel --> RecommendationEngine : "impending fatigue flags"
    RecommendationEngine --> DashboardApp : "writes pre-computed data"
```

---

## 2. Sequence Diagram

The sequence diagram below displays the chronologically ordered call sequence execution at a pipeline processing tick:

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as System Scheduler / Cron
    participant Ingestion as Ingestion Module
    participant Signals as Signals Module
    participant Scoring as Scoring Module & Anomaly
    participant Prediction as ML Prediction Module
    participant Recommendations as Recommendation Engine
    participant Output as Storage (data/output/)

    Scheduler->>Ingestion: Execute Pipeline Tick (Path to Raw Logs)
    activate Ingestion
    Ingestion->>Ingestion: parse_logs()
    Ingestion->>Ingestion: validate_schema()
    Ingestion-->>Signals: pd.DataFrame (Validated)
    deactivate Ingestion

    activate Signals
    Signals->>Signals: calculate_rolling_signals()
    Signals-->>Scoring: pd.DataFrame (Rolling Signals)
    deactivate Signals

    activate Scoring
    Scoring->>Scoring: load_baseline()
    Scoring->>Scoring: normalise_zscore()
    Scoring->>Scoring: apply_sigmoid()
    Scoring->>Scoring: calculate_score() -> AFI (0-100)
    Scoring->>Scoring: detect_anomalies() -> Mann-Whitney U
    Scoring-->>Prediction: AFI Sequence & Anomaly Flags
    deactivate Scoring

    activate Prediction
    Prediction->>Prediction: generate_features()
    Prediction->>Prediction: predict_impending_fatigue()
    Prediction-->>Recommendations: AFI + Anomaly + Fatigue Warning
    deactivate Prediction

    activate Recommendations
    Recommendations->>Recommendations: map_afi_to_advisory()
    Recommendations->>Recommendations: generate_actions()
    Recommendations->>Output: Save AFI, Anomalies, Forecasts & Advisory JSONs
    deactivate Recommendations
    
    note over Output: Dashboard App reads from Output asynchronously on st.rerun()
```
