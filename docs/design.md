# Design Specification: Alert Fatigue Quantifier Dashboard

## Overview

This document defines the complete UI/UX design system for the Streamlit dashboard component of the Alert Fatigue Quantifier. It covers visual identity, colour tokens, typography, layout, component behaviour, and copy standards. Every design decision traces back to the domain: a security operations centre, where information density, low-latency reading, and cognitive load management are not aesthetic options — they are functional requirements.

The dashboard is a **monitoring surface for SOC managers**, not a control panel. It displays, warns, and advises. It never acts.

---

## 1. Design Principles

### 1.1 Readability at a Glance
A SOC manager checking this dashboard mid-shift has three seconds to understand the current state. Every element must answer one of three questions instantly: *Who is fatigued? How fatigued? What should I do?* Anything that does not answer one of these questions has no place on the screen.

### 1.2 Severity Must Be Felt, Not Decoded
Fatigue state is communicated through colour first, label second, number third. A manager should never need to read a number to know that an analyst is in a critical state. The visual grammar of the dashboard must encode severity as naturally as a traffic light.

### 1.3 Advisory Tone Throughout
The system has no authority. Its copy and UI must consistently communicate that all recommendations are suggestions, not directives. The UI must never use imperative language that implies automated action.

### 1.4 Terminal Aesthetic Grounded in SOC Reality
SOC environments are dark, dense, and functional. The dashboard inherits this vernacular: near-black background, monospace data values, structured grid layout. This is not a decorative choice — it reduces eye strain on extended shifts and signals that this is an operational tool, not a reporting tool.

---

## 2. Colour Token System

All Streamlit theme overrides go into `.streamlit/config.toml`. Component-level colours are applied via `st.markdown()` with injected CSS using these exact hex values as CSS custom properties.

```css
:root {
  /* Backgrounds */
  --bg-primary:    #0D1117;   /* Page background — near-black, GitHub-dark register */
  --bg-surface:    #161B22;   /* Card / panel surface */
  --bg-elevated:   #1C2128;   /* Hover states, selected rows */
  --bg-input:      #21262D;   /* Input fields, dropdowns */

  /* Borders */
  --border-subtle: #30363D;   /* Dividers, card outlines */
  --border-active: #58A6FF;   /* Focused inputs, active tabs */

  /* Text */
  --text-primary:  #E6EDF3;   /* Main body copy */
  --text-secondary:#8B949E;   /* Labels, metadata, timestamps */
  --text-muted:    #484F58;   /* Placeholder, disabled */
  --text-inverse:  #0D1117;   /* Text on coloured backgrounds */

  /* AFI Severity Scale — maps directly to fatigue states */
  --state-nominal:  #3FB950;  /* AFI: low fatigue — green */
  --state-elevated: #D29922;  /* AFI: moderate fatigue — amber */
  --state-high:     #F78166;  /* AFI: high fatigue — coral-red */
  --state-critical: #FF4444;  /* AFI: critical fatigue — saturated red */

  /* Accent */
  --accent-primary: #58A6FF;  /* Interactive elements, links, active indicators */
  --accent-dim:     #1F4A7A;  /* Accent backgrounds, badges */

  /* Data Visualisation Palette (Matplotlib / Seaborn overrides) */
  --chart-1: #58A6FF;   /* Primary series */
  --chart-2: #3FB950;   /* Secondary series */
  --chart-3: #D29922;   /* Tertiary series */
  --chart-4: #BC8CFF;   /* Quaternary series */
  --chart-5: #F78166;   /* Alert / warning series */
}
```

### 2.1 AFI Severity Mapping

The AFI score (0–100) maps to four named states. Threshold values must be derived from literature in the scoring module and passed to the dashboard as constants — never hardcoded here.

| State | Colour Token | Visual Treatment |
|-------|-------------|-----------------|
| Nominal | `--state-nominal` | Green gauge fill, green border on analyst card |
| Elevated | `--state-elevated` | Amber gauge fill, amber border, amber badge |
| High | `--state-high` | Coral-red fill, pulsing border animation |
| Critical | `--state-critical` | Saturated red fill, persistent alert banner, audio cue optional |

---

## 3. Typography

Streamlit uses system fonts by default. Override via injected CSS.

```css
/* Display — used for AFI score numbers, analyst name headers */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

/* Body — used for all prose, labels, recommendations */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
```

| Role | Family | Weight | Size | Usage |
|------|--------|--------|------|-------|
| AFI Score | JetBrains Mono | 700 | 48px | The large numeric AFI value on each analyst card |
| Analyst Name | Inter | 600 | 18px | Card header |
| Section Header | Inter | 600 | 14px | Panel titles (uppercase, 1px letter-spacing) |
| Body / Label | Inter | 400 | 13px | Descriptions, metadata, signal labels |
| Timestamp | JetBrains Mono | 400 | 11px | All time values — monospace keeps columns aligned |
| Recommendation | Inter | 500 | 13px | Advisory text in recommendation panel |
| Badge / Status | Inter | 600 | 11px | State labels (NOMINAL, ELEVATED, HIGH, CRITICAL) |

**Rationale:** JetBrains Mono for numeric values enforces the terminal/operational register and keeps numbers column-aligned in dense tables. Inter for prose is legible at small sizes and avoids the sterile look of system-sans without being decorative.

---

## 4. Layout

### 4.1 Page Structure

```
┌─────────────────────────────────────────────────────────┐
│  HEADER BAR                                             │
│  Alert Fatigue Quantifier · [Analyst Filter] · [Clock] │
├──────────────────────────────────┬──────────────────────┤
│                                  │                      │
│  ANALYST GRID (2–3 cols)         │  RECOMMENDATION      │
│  [Card] [Card] [Card]            │  PANEL               │
│  [Card] [Card] [Card]            │                      │
│                                  │  [AFI Advisory]      │
│                                  │  [Queue Actions]     │
├──────────────────────────────────┴──────────────────────┤
│  SIGNAL TREND CHARTS (full width, tabbed per analyst)   │
│  [Triage Interval] [Uninvestigated] [Escalation]        │
│  [Enrichment Depth] [Hourly Closure Rate]               │
├─────────────────────────────────────────────────────────┤
│  DEGRADATION ANOMALY LOG                                │
│  Timestamped table of flagged false-positive deviations │
├─────────────────────────────────────────────────────────┤
│  PREDICTIVE FATIGUE FORECAST                            │
│  Rolling window forecast chart + upcoming risk flags    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Analyst Card

Each analyst gets a card showing their current fatigue state at a glance.

```
┌──────────────────────────────┐
│ ● ELEVATED          [14:32] │  ← state badge + last updated
│                              │
│  Analyst_07                  │  ← analyst ID / name
│                              │
│       67                     │  ← AFI score (48px mono, amber)
│    out of 100                │
│                              │
│  ████████████░░░░  67%      │  ← progress bar, coloured by state
│                              │
│  ↑ Triage +22%   ↓ Enrich  │  ← two dominant signal deltas
└──────────────────────────────┘
```

- Card border: 1px solid, coloured by severity state
- Background: `--bg-surface`
- Score number colour: matches severity state token
- Cards update on each Streamlit rerun (data refresh interval configurable in config)

### 4.3 Recommendation Panel

Right-hand sidebar panel. Width: 280px fixed on desktop, collapses to full-width on narrow viewports.

```
┌──────────────────────────────┐
│  RECOMMENDATIONS             │
│  ─────────────────────────  │
│  Analyst_07 · AFI 67         │
│                              │
│  [!] Consider temporary      │
│      alert suppression for   │
│      medium-severity queue.  │
│                              │
│  [i] Signal: Triage interval │
│      is 22% above baseline.  │
│                              │
│  ─────────────────────────  │
│  All suggestions are         │
│  advisory. Decisions rest    │
│  with the SOC manager.       │
└──────────────────────────────┘
```

- `[!]` icon: `--state-elevated` colour
- `[i]` icon: `--accent-primary` colour
- Footer disclaimer is always visible — never collapsed

### 4.4 Signal Trend Charts (Matplotlib / Seaborn)

Each of the five signals renders as a line chart with:
- Background: `--bg-surface` (passed as `facecolor` to Matplotlib figure)
- Grid lines: `--border-subtle`, alpha 0.4
- Line colour: `--chart-1` for the rolling value, `--text-secondary` dashed for the baseline
- Baseline label: "30-day baseline" in `--text-secondary`
- Y-axis: left-aligned, no top spine, no right spine
- X-axis: timestamps in `JetBrains Mono` 10px
- Anomaly markers: vertical dotted line in `--state-high` at flagged timestamps

Chart titles follow this pattern exactly: `Triage Interval · Analyst_07 · Last 8h`

### 4.5 Degradation Anomaly Log

A `st.dataframe()` table with these columns:

| Column | Description |
|--------|-------------|
| Timestamp | ISO 8601, monospace |
| Analyst | Analyst ID |
| Signal | Which signal triggered |
| Deviation | Z-score delta from baseline |
| p-value | Mann–Whitney U result |
| State | Severity badge |

Rows with State = CRITICAL render with `--state-critical` row background at 15% opacity.

---

## 5. Component Behaviour

### 5.1 Data Refresh
- Streamlit's `st.rerun()` is called on a configurable interval (default: 60 seconds)
- A subtle timestamp in the header shows last refresh: `Last updated 14:33:07`
- No spinner on refresh — it interrupts reading. Use a quiet top-bar progress indicator only

### 5.2 Analyst Filter
- `st.multiselect` in the header bar
- Default: all analysts shown
- Selecting analysts filters the grid, trend charts, and recommendation panel simultaneously
- Label: "Filter analysts" (not "Select analysts" — the action is narrowing, not choosing)

### 5.3 Empty States
- No data loaded: `No log file detected. Load a CSV or JSON export to begin.`
- No anomalies detected: `No degradation anomalies in the current window.` — in `--text-secondary`, not a warning colour
- Model not yet trained: `Predictive model requires baseline data. Run baseline calibration first.`

### 5.4 Tooltips
Every signal name in the trend chart tabs and the anomaly log has a tooltip (via `help=` in Streamlit widgets) explaining the signal in plain language:

- **Triage Interval:** "Average time between alert assignment and first analyst action in this window."
- **Uninvestigated Closures:** "Alerts closed without enrichment steps or notes recorded."
- **Escalation Deviations:** "How far this analyst's escalation rate has drifted from their 30-day norm."
- **Enrichment Depth:** "Average number of enrichment actions taken per alert in this window."
- **Hourly Closure Rate:** "Alerts closed per hour compared to this analyst's baseline rate."

---

## 6. Copy Standards

All UI text follows these rules, consistent with the advisory-only nature of the system:

| Context | Do | Don't |
|---------|-----|-------|
| Recommendations | "Consider temporary alert suppression" | "Suppress alerts now" |
| State labels | "ELEVATED" | "Warning" or "⚠️ Alert" |
| Empty states | "No anomalies in the current window." | "All clear! 🎉" |
| Errors | "Log file could not be parsed. Check the CSV schema." | "Something went wrong." |
| Timestamps | ISO 8601: `2026-06-20 14:33:07` | "2 minutes ago" |
| Analyst IDs | Render exactly as they appear in the log file | Do not rename or reformat |

The disclaimer **"All recommendations are advisory. Decisions rest with the SOC manager."** must appear persistently in the recommendation panel. It is not a footer — it is part of the interface contract.

---

## 7. Streamlit Configuration

`.streamlit/config.toml` must contain:

```toml
[theme]
base = "dark"
backgroundColor = "#0D1117"
secondaryBackgroundColor = "#161B22"
textColor = "#E6EDF3"
primaryColor = "#58A6FF"
font = "sans serif"

[server]
headless = true
port = 8501

[browser]
gatherUsageStats = false
```

---

## 8. Accessibility

- All colour pairs used for text-on-background must meet WCAG AA contrast (4.5:1 minimum)
- Severity state must never be communicated by colour alone — always paired with a text label
- `st.set_page_config(page_title="Alert Fatigue Quantifier", page_icon="🛡️", layout="wide")` at the top of `dashboard/app.py`
- Reduced motion: charts should not animate on every rerun — render static, update in place

---

## 9. What the Dashboard Must Never Do

These constraints come directly from the project scope defined in the synopsis:

- Never display a button or control that modifies alert queues, SIEM rules, or analyst assignments
- Never connect to a live API — all data comes from the pipeline output, not direct queries
- Never display raw log file contents — only computed outputs (AFI, signals, anomalies, recommendations)
- Never show an analyst's personal details beyond their ID as it appears in the log file
- Never imply the system has taken or will take action — all language is past-tense observation or conditional suggestion
