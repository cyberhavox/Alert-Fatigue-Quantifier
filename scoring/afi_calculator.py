"""Analyst Fatigue Index (AFI) calculator for the Alert Fatigue Quantifier.

Applies z-score normalization, sigmoid scaling, Circadian Rhythm Time-of-Day Multiplier (1.20x),
and literature-derived weights to combine rolling signals into the final composite AFI (0-100).
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from config.settings import (
    WEIGHT_ENRICHMENT_DEPTH,
    WEIGHT_ESCALATION_DEVIATIONS,
    WEIGHT_HOURLY_CLOSURE_RATE,
    WEIGHT_TRIAGE_INTERVAL,
    WEIGHT_UNINVESTIGATED_CLOSURES,
)


def calculate_analyst_afi(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """Calculates the composite Analyst Fatigue Index (AFI) for each record.

    Vectorizes z-score normalization and sigmoid scaling across signal columns,
    applies time-of-day circadian rhythm multiplier (1.20x during 02:00-06:00 UTC),
    and scales to range [0, 100].

    Args:
        df: DataFrame containing computed rolling signals per row.
        baselines: Dictionary of baseline parameters keyed by analyst_id.

    Returns:
        A copy of the DataFrame with appended normalisation and afi_score columns.
    """
    res = df.copy()

    # Pre-allocate array for calculated score
    afi_scores = np.zeros(len(res))
    closure_dts = pd.to_datetime(res["closure_timestamp"])

    # Vectorized computation grouped by analyst to map correct baselines
    for analyst_id, baseline in baselines.items():
        mask = res["analyst_id"] == analyst_id
        if not mask.any():
            continue

        # Extract baseline parameters
        triage_mean = baseline.get("mean_triage_interval", 0.0)
        triage_std = baseline.get("std_triage_interval", 1.0)
        uninvest_mean = baseline.get("mean_uninvestigated_closures", 0.0)
        uninvest_std = baseline.get("std_uninvestigated_closures", 1.0)
        enrich_mean = baseline.get("mean_enrichment_depth", 0.0)
        enrich_std = baseline.get("std_enrichment_depth", 1.0)

        # 1. Normalize z-scores
        z_triage = (res.loc[mask, "triage_interval"] - triage_mean) / triage_std
        z_uninvest = (res.loc[mask, "uninvestigated_closures"] - uninvest_mean) / uninvest_std
        z_enrich = (enrich_mean - res.loc[mask, "enrichment_depth"]) / enrich_std  # Negated z-score
        
        z_escalation = res.loc[mask, "escalation_deviations"] / 0.15
        z_closures = (res.loc[mask, "hourly_closure_rate"] - 1.0) / 0.5

        # 2. Apply Sigmoid Scaling
        s_triage = 1.0 / (1.0 + np.exp(-z_triage))
        s_uninvest = 1.0 / (1.0 + np.exp(-z_uninvest))
        s_enrich = 1.0 / (1.0 + np.exp(-z_enrich))
        s_escalation = 1.0 / (1.0 + np.exp(-z_escalation))
        s_closures = 1.0 / (1.0 + np.exp(-z_closures))

        # 3. Weighted Aggregation
        raw_afi = (
            WEIGHT_TRIAGE_INTERVAL * s_triage +
            WEIGHT_UNINVESTIGATED_CLOSURES * s_uninvest +
            WEIGHT_ENRICHMENT_DEPTH * s_enrich +
            WEIGHT_ESCALATION_DEVIATIONS * s_escalation +
            WEIGHT_HOURLY_CLOSURE_RATE * s_closures
        )

        # 4. Circadian Rhythm Time-of-Day Multiplier (Al-Mhiqani et al. IEEE Cyber Ops)
        # Night shift (02:00 UTC to 06:00 UTC) applies a 1.20x multiplier due to physiological vigilance drop
        hours = closure_dts.loc[mask].dt.hour
        night_mask = (hours >= 2) & (hours <= 6)
        circadian_multiplier = np.where(night_mask, 1.20, 1.0)

        adjusted_afi = raw_afi * 100.0 * circadian_multiplier
        afi_scores[mask] = np.clip(adjusted_afi, 0.0, 100.0)

    res["afi_score"] = afi_scores
    return res
