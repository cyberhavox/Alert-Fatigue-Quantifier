# Project Folder Structure: Alert Fatigue Quantifier

## Root Layout

```
alert-fatigue-quantifier/
│
├── README.md                        # Setup, run, and test instructions
├── requirements.txt                 # Pinned Python 3.10 dependencies
├── .gitignore                       # Excludes data/, __pycache__, .env, *.pyc
├── .env.example                     # Template for environment variables (paths, thresholds)
│
├── .streamlit/
│   └── config.toml                  # Streamlit theme + server settings (see design.md §7)
│
├── config/
│   └── settings.py                  # All named constants: window size, AFI weights,
│                                    # file paths, refresh interval — nothing hardcoded elsewhere
│
├── data/
│   ├── raw/                         # Synthetic CSV/JSON log files (generated, not committed)
│   │   └── .gitkeep
│   ├── baseline/                    # 30-day per-analyst baseline exports (generated)
│   │   └── .gitkeep
│   └── output/                      # Pipeline output files consumed by dashboard
│       └── .gitkeep
│
├── scripts/
│   └── generate_synthetic_data.py   # Week 4 deliverable: generates raw/ log files
│                                    # matching SANS/Ponemon statistical distributions
│
├── ingestion/
│   ├── __init__.py
│   ├── parser.py                    # Reads CSV/JSON, validates schema, normalises fields
│   └── validator.py                 # Checks required fields, types, and value ranges
│
├── signals/
│   ├── __init__.py
│   ├── triage_interval.py           # Signal 1: mean time from assignment to first action
│   ├── uninvestigated_closures.py   # Signal 2: alerts closed without enrichment or notes
│   ├── escalation_deviations.py     # Signal 3: deviation from analyst's baseline escalation rate
│   ├── enrichment_depth.py          # Signal 4: mean enrichment actions per alert
│   ├── hourly_closure_rate.py       # Signal 5: alerts closed per hour vs. baseline
│   └── rolling_window.py            # Shared utility: applies 60-minute rolling window logic
│
├── scoring/
│   ├── __init__.py
│   ├── normaliser.py                # SciPy z-score normalisation per signal per analyst
│   ├── afi_calculator.py            # Applies literature-derived weights → AFI (0–100)
│   └── baseline_calibrator.py       # Builds and stores 30-day per-analyst baseline
│
├── degradation/
│   ├── __init__.py
│   ├── detector.py                  # Compares current FP closure rate to baseline
│   └── mann_whitney.py              # SciPy Mann–Whitney U test wrapper with logging
│
├── prediction/
│   ├── __init__.py
│   ├── model.py                     # Scikit-Learn Random Forest: train, predict, save
│   ├── feature_engineering.py       # Builds feature matrix from signal outputs
│   └── validator.py                 # 70/30 split + k-fold cross-validation + metrics log
│
├── recommendations/
│   ├── __init__.py
│   └── engine.py                    # Maps AFI level → advisory text suggestions
│                                    # Thresholds sourced from config/settings.py (literature-derived)
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py                       # Streamlit entry point: st.set_page_config + layout orchestration
│   ├── components/
│   │   ├── __init__.py
│   │   ├── analyst_card.py          # AFI gauge card per analyst
│   │   ├── signal_charts.py         # Matplotlib trend charts for all 5 signals
│   │   ├── anomaly_log.py           # st.dataframe for degradation anomaly table
│   │   ├── forecast_panel.py        # Random Forest prediction chart + risk flags
│   │   └── recommendation_panel.py  # Advisory suggestions + persistent disclaimer
│   └── styles/
│       └── theme.css                # Injected via st.markdown(); uses CSS vars from design.md
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared PyTest fixtures: mock DataFrames, sample analysts
│   │
│   ├── ingestion/
│   │   ├── test_parser.py
│   │   └── test_validator.py
│   │
│   ├── signals/
│   │   ├── test_triage_interval.py
│   │   ├── test_uninvestigated_closures.py
│   │   ├── test_escalation_deviations.py
│   │   ├── test_enrichment_depth.py
│   │   ├── test_hourly_closure_rate.py
│   │   └── test_rolling_window.py
│   │
│   ├── scoring/
│   │   ├── test_normaliser.py
│   │   ├── test_afi_calculator.py
│   │   └── test_baseline_calibrator.py
│   │
│   ├── degradation/
│   │   ├── test_detector.py
│   │   └── test_mann_whitney.py
│   │
│   ├── prediction/
│   │   ├── test_model.py            # Covers 70/30 split, k-fold, metric logging
│   │   └── test_feature_engineering.py
│   │
│   └── recommendations/
│       └── test_engine.py
│
└── docs/
    ├── agent.md                     # Coding agent project briefing
    ├── rules.md                     # Hard constraints and coding standards
    ├── design.md                    # This dashboard design specification
    ├── data_schema.md               # Synthetic dataset field definitions
    └── afi_formula.md               # AFI formula: inputs, weights (cited), normalisation, output
```

---

## Key Rules This Structure Enforces

**One-way data flow is physically enforced by the folder layout.** Each module imports only from the module directly above it in the pipeline chain. No module reaches sideways or downstream.

```
ingestion/ → signals/ → scoring/ + degradation/ → prediction/ → recommendations/ → dashboard/
```

**`config/settings.py` is the single source of truth** for all numeric constants. No weight, threshold, window size, or path appears anywhere else. Any change to AFI logic changes one file.

**`data/` is never committed.** All three subdirectories (`raw/`, `baseline/`, `output/`) hold generated files only. `.gitkeep` files preserve the directory structure in Git without committing data.

**Tests mirror the source tree exactly.** `tests/signals/test_triage_interval.py` tests `signals/triage_interval.py`. This makes it immediately obvious when a module is missing its test.

**`dashboard/` contains zero business logic.** All computation happens upstream. The dashboard only reads from `data/output/` and calls display functions. Components are split into individual files — one file per UI panel.

---

## File Naming Conventions

| Convention | Example |
|------------|---------|
| Module files | `snake_case.py` |
| Test files | `test_<module_name>.py` |
| Data files | `analyst_logs_YYYYMMDD.csv` |
| Baseline files | `baseline_<analyst_id>.json` |
| Output files | `afi_output_<timestamp>.json` |

---

## `requirements.txt` (Pinned Stack)

```
pandas==2.2.2
numpy==1.26.4
scipy==1.13.0
scikit-learn==1.5.0
matplotlib==3.9.0
seaborn==0.13.2
streamlit==1.35.0
pytest==8.2.0
```

No other packages. If a sprint requires a new library, it must be approved against `rules.md Rule 3` before being added here.

---

## Sprint–Folder Mapping

| Week | Folders Created / Files Added |
|------|-------------------------------|
| 1 | Project root, `docs/`, `README.md`, `.gitignore` skeleton |
| 2 | `docs/data_schema.md`, `docs/afi_formula.md` (draft) |
| 3 | `docs/` completed, `config/settings.py` skeleton |
| 4 | `scripts/generate_synthetic_data.py`, `data/raw/` populated |
| 5 | `ingestion/`, `signals/`, `scoring/` — all source files + Git init |
| 6 | `degradation/`, `prediction/`, `recommendations/`, `dashboard/` |
| 7 | `tests/` — all test files written and passing |
| 8 | `docs/` finalised, `requirements.txt` pinned, repo cleaned |
