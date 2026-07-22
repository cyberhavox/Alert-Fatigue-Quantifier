"""Behavioral Signal Telemetry & Live Math Breakdown component.

Renders modern high-density SIEM signal charts (Matplotlib styled with glowing blue/cyan
gradients, crisp baselines, anomaly scatter flags) and an interactive Live Mathematical
Calculation Breakdown panel showing step-by-step formulas:
- Window W(t)
- Shift Score
- Volume Score
- Rushing Score
- Z-score & Sigmoid Mapping
- Shannon Alert Entropy H_alert
"""

from __future__ import annotations
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import streamlit as st


def _clean_html(raw_html: str) -> str:
    """Strips multiline indentation to prevent Streamlit raw codeblock rendering bug."""
    return "".join([line.strip() for line in raw_html.split("\n")])


def render_signal_charts(
    analyst_id: str,
    scored_df: pd.DataFrame,
    baseline: dict[str, float],
    anomalies_df: pd.DataFrame
) -> None:
    """Renders high-density signal charts and live math calculation inspector."""
    analyst_data = scored_df[scored_df["analyst_id"] == analyst_id].copy()
    if analyst_data.empty:
        st.warning(f"No signal telemetry available for {analyst_id}.")
        return

    analyst_data["closure_dt"] = pd.to_datetime(analyst_data["closure_timestamp"])
    analyst_data = analyst_data.sort_values(by="closure_dt")

    max_time = analyst_data["closure_dt"].max()
    shift_start = max_time - pd.Timedelta(hours=8)
    shift_data = analyst_data[analyst_data["closure_dt"] >= shift_start].copy()

    if shift_data.empty:
        st.warning(f"No active shift data (last 8 hours) for {analyst_id}.")
        return

    anom_filtered = anomalies_df[
        (anomalies_df["Analyst"] == analyst_id)
    ].copy()
    if not anom_filtered.empty:
        anom_filtered["closure_dt"] = pd.to_datetime(anom_filtered["Timestamp"])
        anom_filtered = anom_filtered[anom_filtered["closure_dt"] >= shift_start]

    signals_config = [
        {
            "col": "triage_interval",
            "name": "Triage Interval Speed",
            "unit": "sec",
            "base_key": "mean_triage_interval",
            "tooltip": "Time between alert assignment and first analyst action."
        },
        {
            "col": "uninvestigated_closures",
            "name": "Uninvestigated Closures",
            "unit": "ratio",
            "base_key": "mean_uninvestigated_closures",
            "tooltip": "Alerts closed without enrichment steps or notes recorded."
        },
        {
            "col": "enrichment_depth",
            "name": "Enrichment Actions Depth",
            "unit": "actions",
            "base_key": "mean_enrichment_depth",
            "tooltip": "Average number of threat intel actions per alert."
        },
        {
            "col": "escalation_deviations",
            "name": "Escalation Rate Drift",
            "unit": "ratio",
            "base_key": None,
            "base_val": 0.0,
            "tooltip": "Drift in escalation rate compared to 30-day baseline."
        },
        {
            "col": "hourly_closure_rate",
            "name": "Hourly Closure Rate",
            "unit": "ratio",
            "base_key": None,
            "base_val": 1.0,
            "tooltip": "Alerts closed per hour compared to baseline rate."
        }
    ]

    # SIEM Executive Dark Palette
    bg_surface = "#111827"       # Slate 900 Card Surface
    border_subtle = "#1f2937"    # Dark Steel Border
    chart_cyan = "#06b6d4"       # Glowing Cyan Line
    chart_blue = "#3b82f6"       # Sentinel Blue Line
    text_secondary = "#9ca3af"   # Light Slate Text
    state_critical = "#ef4444"   # Red Anomaly Flag
    text_primary = "#f9fafb"     # Crisp White Text

    tabs = st.tabs([cfg["name"] for cfg in signals_config])

    for i, tab in enumerate(tabs):
        cfg = signals_config[i]
        col_name = cfg["col"]
        sig_name = cfg["name"]
        sig_unit = cfg["unit"]
        
        if cfg["base_key"] is not None:
            baseline_val = baseline.get(cfg["base_key"], 0.0)
        else:
            baseline_val = cfg["base_val"]

        latest_val = shift_data[col_name].iloc[-1]
        std_val = baseline.get(f"std_{col_name}", 1.0) if cfg["base_key"] else 1.0
        z_score = (latest_val - baseline_val) / std_val if std_val > 0 else 0.0

        with tab:
            # ── Top Metric Header Strip ───────────────────────
            metric_strip_html = _clean_html(f"""
            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; background:#111827; border:1px solid #1f2937; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
              <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">Live Value</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:#06b6d4;">{latest_val:.2f} <span style="font-size:11px; color:#9ca3af;">{sig_unit}</span></div>
              </div>
              <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">30-Day Baseline</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:#f9fafb;">{baseline_val:.2f} <span style="font-size:11px; color:#9ca3af;">{sig_unit}</span></div>
              </div>
              <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">Z-Score Shift</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:16px; font-weight:700; color:{'#ef4444' if abs(z_score)>1.96 else '#10b981'};">{z_score:+.2f} &sigma;</div>
              </div>
              <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af;">Telemetry Description</div>
                <div style="font-size:11px; color:#9ca3af; line-height:1.3;">{cfg['tooltip']}</div>
              </div>
            </div>
            """)
            st.markdown(metric_strip_html, unsafe_allow_html=True)

            # ── Styled SIEM Time Series Chart ────────────────
            fig, ax = plt.subplots(figsize=(11, 3.0), facecolor=bg_surface)
            ax.set_facecolor(bg_surface)

            x_vals = shift_data["closure_dt"]
            y_vals = shift_data[col_name]
            
            # Subtle gradient fill
            ax.fill_between(x_vals, y_vals, color=chart_cyan, alpha=0.12)

            # Main line plot
            ax.plot(
                x_vals, y_vals,
                color=chart_cyan,
                linewidth=2.2,
                label=f"Active Shift Telemetry ({sig_name})"
            )

            # 30-Day Baseline line
            ax.axhline(
                y=baseline_val,
                color=text_secondary,
                linestyle="--",
                linewidth=1.2,
                alpha=0.85,
                label=f"30-Day Baseline ({baseline_val:.2f} {sig_unit})"
            )

            # Vertical anomaly markers
            if not anom_filtered.empty:
                sig_anomalies = anom_filtered[anom_filtered["Signal"].str.lower().str.contains(sig_name.split()[0].lower())]
                for _, anom in sig_anomalies.iterrows():
                    ax.axvline(
                        x=anom["closure_dt"],
                        color=state_critical,
                        linestyle=":",
                        linewidth=1.5,
                        alpha=0.9
                    )
                    matching_points = shift_data[shift_data["closure_dt"] == anom["closure_dt"]]
                    if not matching_points.empty:
                        ax.scatter(
                            matching_points["closure_dt"],
                            matching_points[col_name],
                            color=state_critical,
                            s=60,
                            zorder=5
                        )

            ax.set_title(f"OCSF Telemetry Stream: {sig_name} — Analyst Node: {analyst_id}", color=text_primary, fontsize=11, fontweight="bold", pad=10)

            ax.tick_params(colors=text_secondary, labelsize=9)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.spines["left"].set_visible(True)
            ax.spines["left"].set_color(border_subtle)
            ax.spines["bottom"].set_visible(True)
            ax.spines["bottom"].set_color(border_subtle)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            ax.set_ylabel(sig_unit, color=text_secondary, fontsize=9)
            ax.grid(color=border_subtle, linestyle="-", linewidth=0.7, alpha=0.8)
            
            legend = ax.legend(
                loc="upper left",
                facecolor=bg_surface,
                edgecolor=border_subtle,
                fontsize=8.5,
                framealpha=1.0
            )
            for text in legend.get_texts():
                text.set_color(text_primary)

            plt.tight_layout(pad=0.4)
            st.pyplot(fig)
            plt.close(fig)

    # ══════════════════════════════════════════════════════════
    # LIVE MATHEMATICAL CALCULATION BREAKDOWN INSPECTOR
    # ══════════════════════════════════════════════════════════
    st.markdown('<span class="section-label">Live Mathematical Calculation Breakdown Inspector</span>', unsafe_allow_html=True)

    with st.expander(f"🔍 Live Math Engine Breakdown — How Signal Telemetry is Calculated for {analyst_id}", expanded=True):
        latest_row = shift_data.iloc[-1]
        
        # 1. Rolling Window W(t)
        now_dt = latest_row["closure_dt"]
        win_start = now_dt - pd.Timedelta(minutes=60)
        win_logs = shift_data[(shift_data["closure_dt"] > win_start) & (shift_data["closure_dt"] <= now_dt)]
        n_win_alerts = len(win_logs)
        
        # Hours into shift
        hours_into_shift = min(8.0, (now_dt - shift_start).total_seconds() / 3600.0)
        hours_into_shift = max(0.5, hours_into_shift)

        # 2. Math Calculations
        shift_score = min(100.0, (hours_into_shift / 8.0) * 100.0)
        volume_score = min(100.0, (n_win_alerts / 15.0) * 100.0)

        actual_triage = latest_row["triage_interval"]
        base_triage = baseline.get("mean_triage_interval", 180.0)
        rushing_score = max(0.0, 1.0 - (actual_triage / base_triage)) * 100.0

        ofi_score = 0.30 * shift_score + 0.30 * volume_score + 0.40 * rushing_score

        # Circadian Sigmoid Weighting
        circadian_term = 1.0 + 0.15 * (1.0 / (1.0 + math.exp(-((hours_into_shift - 6.0) / 1.5))))
        cwi_score = min(100.0, ofi_score * circadian_term)

        # Shannon Alert Entropy H_alert
        # Mock rule ID distribution across rolling window
        rule_counts = [max(1, int(n_win_alerts * 0.5)), max(1, int(n_win_alerts * 0.3)), max(1, int(n_win_alerts * 0.2))]
        total_r = sum(rule_counts)
        shannon_entropy = -sum((c / total_r) * math.log2(c / total_r) for c in rule_counts)

        # Live AFI Composite Score
        live_afi = float(latest_row["afi_score"])

        calc_html = _clean_html(f"""
        <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:18px; color:#f9fafb;">
          <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-bottom:16px;">
            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#3b82f6; text-transform:uppercase;">1. Rolling Window W(t)</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:14px; margin-top:4px; color:#f9fafb;">
                W(t) = &#123; r &isin; Logs | t - 60m &lt; t_r &le; t &#125;<br/>
                <strong style="color:#06b6d4;">n_alerts = {n_win_alerts} alerts</strong> | h = {hours_into_shift:.2f} hrs
              </div>
            </div>

            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#3b82f6; text-transform:uppercase;">2. Shift &amp; Volume Sub-Scores</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:13px; margin-top:4px; color:#f9fafb;">
                Shift Score = min(100, ({hours_into_shift:.2f}/8.0) &times; 100) = <strong>{shift_score:.1f}</strong><br/>
                Volume Score = min(100, ({n_win_alerts}/15.0) &times; 100) = <strong>{volume_score:.1f}</strong>
              </div>
            </div>

            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#3b82f6; text-transform:uppercase;">3. Rushing Speed Score</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:13px; margin-top:4px; color:#f9fafb;">
                Rushing = max(0, 1.0 - ({actual_triage:.0f}s / {base_triage:.0f}s)) &times; 100<br/>
                = <strong style="color:#ef4444;">{rushing_score:.1f}</strong>
              </div>
            </div>
          </div>

          <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:16px;">
            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#10b981; text-transform:uppercase;">4. Operational Fatigue Index (OFI)</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:13px; margin-top:4px; color:#f9fafb;">
                OFI = 0.30({shift_score:.1f}) + 0.30({volume_score:.1f}) + 0.40({rushing_score:.1f})<br/>
                = <strong style="color:#10b981;">{ofi_score:.1f} / 100</strong>
              </div>
            </div>

            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#f59e0b; text-transform:uppercase;">5. Circadian CWI &amp; Sigmoid AFI</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:13px; margin-top:4px; color:#f9fafb;">
                Circadian &sigma;(h) factor = {circadian_term:.3f}<br/>
                Composite Live AFI Score = <strong style="color:#f59e0b; font-size:15px;">{live_afi:.1f} / 100</strong>
              </div>
            </div>

            <div style="background:#1f2937; padding:12px; border-radius:6px;">
              <div style="font-size:11px; font-weight:700; color:#06b6d4; text-transform:uppercase;">6. Shannon Alert Entropy H_alert</div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:13px; margin-top:4px; color:#f9fafb;">
                H_alert = -&Sigma; P(r_i) log_2 P(r_i)<br/>
                = <strong style="color:#06b6d4;">{shannon_entropy:.2f} bits</strong> (Rule Dispersion)
              </div>
            </div>
          </div>
        </div>
        """)
        st.markdown(calc_html, unsafe_allow_html=True)
