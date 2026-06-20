# Rules & Hard Constraints: Alert Fatigue Quantifier

These rules are non-negotiable. Every line of code, every file, every decision must comply. When in doubt, stop and re-read this document before proceeding.

---

## Rule 1 — Scope Boundary (Hard Stop)

The system is **read-only and advisory at all times.** This is stated explicitly in the project synopsis.

- NEVER write to, modify, or interact with live SIEM platforms (Splunk, Sentinel, QRadar, or any other)
- NEVER modify ServiceDesk tools, alert queues, or ticketing systems
- NEVER automatically reassign alerts or change severity priorities in live workflows
- The recommendation engine outputs suggestions as text/UI elements only — it executes nothing
- Operational decisions remain entirely with the SOC manager — the tool provides no automated enforcement
- If a feature request would cause the system to write to an external system, reject it immediately

---

## Rule 2 — Data Boundary (Hard Stop)

The only permitted data sources are **synthetic CSV and JSON log files.**

- NEVER build live API connections to Splunk, Sentinel, QRadar, or any SIEM
- NEVER ingest real analyst data or real incident data
- NEVER use databases, message queues, or streaming data pipelines (Kafka, Redis, etc.)
- All log data must be generated synthetically to match statistical distributions from published SOC research (SANS Institute, Ponemon Institute, USENIX, IEEE, ACM Computing Surveys)
- Synthetic data must include these fields at minimum: `analyst_id`, `alert_id`, `triage_timestamp`, `closure_timestamp`, `closure_type`, `severity_assigned`, `severity_verified`, `enrichment_actions`, `escalation_flag`, `notes`
- Validation focuses on behavioral patterns — not on actual security incident outcomes

---

## Rule 3 — Technology Lock (No Substitutions)

Use **only** the approved stack defined in the project synopsis. No exceptions, no additions without explicit instruction.

**Permitted:**
- Python 3.10
- Pandas, NumPy
- SciPy (z-score normalization and Mann–Whitney U tests only)
- Scikit-Learn (Random Forest only)
- Matplotlib, Seaborn
- Streamlit
- Git
- PyTest
- Python standard library (`cProfile`, `os`, `json`, `csv`, `datetime`, etc.)

**Prohibited (examples, not exhaustive):**
- FastAPI, Flask, Django, or any web framework other than Streamlit
- SQLAlchemy or any ORM/database connector
- TensorFlow, PyTorch, XGBoost, or any ML library other than Scikit-Learn
- Kafka, Celery, or any async/task queue library
- Docker, Kubernetes, or containerization tooling
- Any paid or external API

If a library is not listed as permitted, it is prohibited.

---

## Rule 4 — Architecture Rule (No Monoliths)

All pipeline stages must remain **separate Python modules** in separate files/directories. The synopsis defines seven distinct components — all seven must stay separated.

> **Authoritative reference:** `docs/folder_structure.md` is the single source of truth for the complete directory tree, every file's location and responsibility, naming conventions, and the sprint–folder mapping. Before creating any file or directory, consult it. If a file's location is not specified there, stop and confirm before proceeding.

```
ingestion/
signals/
scoring/
degradation/
prediction/
recommendations/
dashboard/
```

- NEVER collapse two or more modules into a single file
- NEVER import downstream modules into upstream ones — data flows strictly one direction
- NEVER create circular imports
- Each module must expose a clean, documented public interface
- The Streamlit dashboard is the only consumer of the final output — it must not contain business logic

Data flow is strictly: `ingestion → signals → scoring + degradation → prediction → recommendations → dashboard`. No shortcuts, no bypasses.

---

## Rule 5 — Code Standards (Enforced on Every File)

Every `.py` file must comply with the following before being considered complete:

> **File naming:** All naming conventions (module files, test files, data files, baseline files, output files) are defined in `docs/folder_structure.md` §File Naming Conventions. Follow them exactly — do not invent new patterns.

- **Python version:** 3.10 syntax only
- **PEP 8:** All code must pass `pycodestyle` or `flake8` without errors
- **Type hints:** Every function signature must include parameter types and return types
- **Docstrings:** Every module, class, and function must have a docstring explaining purpose, parameters, and return values (Google style preferred)
- **No magic numbers:** Every numeric constant (weights, thresholds, window sizes) must be defined as a named constant with a comment citing its source from the literature
- **No hardcoded paths:** All file paths must be configurable via a config file or environment variable

Example of an acceptable function signature:
```python
def calculate_triage_interval(
    df: pd.DataFrame,
    analyst_id: str,
    window_minutes: int = 60
) -> float:
    """
    Calculates the mean triage interval for an analyst over a rolling window.

    Args:
        df: DataFrame containing alert log records with triage timestamps.
        analyst_id: Unique identifier for the analyst being evaluated.
        window_minutes: Size of the rolling window in minutes. Defaults to 60.

    Returns:
        Mean triage interval in seconds for the specified window.
    """
```

---

## Rule 6 — Testing Requirement (Blocking)

**No signal calculation function is marked complete until it has a corresponding PyTest unit test.**

As defined in the synopsis: PyTest runs unit tests for each signal function using custom sample inputs.

Requirements for every unit test:
- Located in `tests/` directory, mirroring the module structure
- Uses mock/synthetic inputs — never depends on a real file being present on disk
- Tests at minimum: a normal case, an edge case (empty window, single record), and an anomalous case (extreme values)
- Test function names must describe the scenario: `test_triage_interval_returns_zero_for_empty_window()`

Model validation tests must confirm:
- 70/30 train-test split is applied correctly with no data leakage
- k-fold cross-validation runs without data leakage
- Model accuracy metrics are logged (accuracy, precision, recall, F1)

Performance tests must confirm:
- `cProfile` output is captured for all Pandas operations to ensure fast processing
- No single pipeline stage takes more than a defined, documented threshold

---

## Rule 7 — Debugging & Development Tools

These tools are part of the project's defined approach (per the synopsis) and must be used as specified:

- **VS Code debugger:** Use to trace signal values at each pipeline stage during development and bug-fixing
- **Streamlit hot-reload:** Use during dashboard development to speed up iteration — do not disable it
- **cProfile:** Use to profile Pandas operations — not optional, required before Week 7 sign-off

---

## Rule 8 — Model Integrity Rule (Academic Requirement)

**Every weight in the AFI scoring formula must trace back to a cited source from the 18 reviewed publications.**

- Weights must be defined as named constants with an inline comment citing the paper/report they originate from
- Example: `WEIGHT_TRIAGE_INTERVAL = 0.30  # SANS Institute (2023): triage delay most correlated with fatigue onset`
- NEVER assign arbitrary weights to satisfy a numerical outcome
- AFI threshold bands (e.g., fatigue level boundaries) must also be derived from literature — never invented
- If a weight or threshold cannot be justified by literature, flag it explicitly in a code comment and document it as a limitation for future research

---

## Rule 9 — Academic Integrity Rule

This is a **university research project submitted for academic assessment at JAIN Online.**

- NEVER paste unmodified code blocks from tutorials, Stack Overflow, GitHub, or any external source
- All code must be original or sufficiently transformed and documented
- If a standard algorithm (e.g., z-score formula) is implemented, document the mathematical basis in the docstring
- All 18 references cited in the synopsis must be traceable to specific design decisions in the code and documentation
- The synthetic dataset generation logic must cite the statistical distributions it mimics (specific SANS and Ponemon figures used)

---

## Rule 10 — Git Discipline

- Initialize the Git repository in **Week 5** as per the sprint plan
- Maintain a `.gitignore` from the moment the repository is created
- Commit after completing each discrete task — not at the end of a week
- Commit messages must be descriptive using conventional commits format: `feat(signals): add triage_interval rolling window function` — never just `update` or `fix`
- Permitted prefixes: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`
- NEVER commit generated data files, `__pycache__`, `.pyc` files, or virtual environment folders

---

## Rule 11 — Documentation Requirement

- `README.md` must exist at the project root and include: project description, setup instructions, how to run the synthetic data generator, how to launch the Streamlit dashboard, and how to run the test suite
- Each module directory must contain a brief `README.md` or inline module docstring explaining its role in the pipeline
- The AFI formula must be documented in full — inputs, weights (with citations), normalization method (z-score via SciPy), and output range (0–100) — in both code comments and the project documentation
- The final report must cover five chapters per university guidelines, with 18 APA-formatted references

---

## Rule 12 — Agile Sprint Compliance

- The project follows an **Agile SDLC with two-week sprints** — this is defined in the synopsis
- Do not attempt to compress or skip sprint activities
- The current default phase is **Week 1** unless instructed otherwise
- Week 1 deliverables are: 9 sources reviewed, research gap confirmed, synthetic dataset schema defined
- Do not begin coding before Week 5 — earlier weeks are reserved for literature review, architecture design, and UML work

---

## Rule 13 — Dashboard Design Rule (Blocking)

**No dashboard code may be written until `docs/design.md` has been read in full.**

`docs/design.md` is the single source of truth for the entire `dashboard/` module. Every decision made in `dashboard/app.py`, `dashboard/components/`, and `dashboard/styles/` must trace back to it.

Specifically:

- **Colours:** All hex values and CSS custom properties come from `design.md` §2. Never hardcode a colour value directly in Python or CSS — always reference the named token
- **Typography:** Font families, weights, and sizes come from `design.md` §3. Do not substitute system fonts or Google Fonts families not listed there
- **Layout:** Page structure, analyst card wireframe, recommendation panel dimensions, and chart styling rules come from `design.md` §4. Do not redesign the layout without updating `design.md` first
- **Component behaviour:** Refresh logic, filter behaviour, and empty states come from `design.md` §5. Implement them exactly as specified
- **Copy:** All UI text — labels, tooltips, empty states, error messages, the advisory disclaimer — must follow `design.md` §6. The disclaimer *"All recommendations are advisory. Decisions rest with the SOC manager."* must appear persistently and may never be removed or collapsed
- **`config.toml`:** The exact Streamlit configuration from `design.md` §7 must be placed in `.streamlit/config.toml` before the dashboard is run for the first time
- **Accessibility:** Contrast ratios, colour-plus-label severity encoding, and `st.set_page_config()` settings come from `design.md` §8
- **Dashboard prohibitions:** `design.md` §9 lists five things the dashboard must never do. Treat them as hard stops equivalent to Rule 1

If `design.md` does not cover a specific dashboard decision, stop and flag it before making a choice.

---

## Quick Reference: Stop and Flag Before Proceeding

Do not proceed without review if you are about to:
- Add any library not listed in Rule 3
- Connect to any live external system
- Collapse module boundaries defined in Rule 4
- Assign an AFI weight or threshold band without a literature citation
- Mark a signal function complete without a corresponding unit test
- Begin coding activities before Week 5 of the sprint plan
- Write any dashboard code without having read `docs/design.md` in full
