"""Analyst Fatigue Index (AFI) calculator for the Alert Fatigue Quantifier.

Applies z-score normalization, sigmoid scaling, and literature-derived weights
to combine rolling signals into the final composite AFI (0-100).
"""

import numpy as np
import pandas as pd
from config.settings import (
    WEIGHT_ENRICHMENT_DEPTH,
    WEIGHT_ESCALATION_DEVIATIONS,
    WEIGHT_HOURLY_CLOSURE_RATE,
    WEIGHT_TRIAGE_INTERVAL,
    WEIGHT_UNINVESTIGATED_CLOSURES,
)
from scoring.normaliser import apply_sigmoid, normalise_zscore


def calculate_analyst_afi(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    """Calculates the composite Analyst Fatigue Index (AFI) for each record.

    Vectorizes z-score normalization and sigmoid scaling across the signal columns,
    applies the weights from config/settings.py, and scales to range [0, 100].

    Args:
        df: DataFrame containing the 5 computed rolling signals per row.
        baselines: Dictionary of baseline parameters keyed by analyst_id.

    Returns:
        A copy of the DataFrame with appended normalisation and afi_score columns.
    """
    res = df.copy()

    # Pre-allocate array for calculated score
    afi_scores = np.zeros(len(res))

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
        
        # Escalation deviations & Hourly closure rate are already rate deviations.
        # We compute their z-scores assuming normal baseline is centered at 0 with standard deviations.
        # However, to be mathematically consistent, we normalize them against 0 baseline parameter means.
        # For simplicity and correctness, we z-score normalize them:
        z_escalation = res.loc[mask, "escalation_deviations"] / 0.15  # Scale by expected deviation
        z_closures = (res.loc[mask, "hourly_closure_rate"] - 1.0) / 0.5  # Scale relative to nominal 1.0 ratio

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

        afi_scores[mask] = raw_afi * 100.0

    res["afi_score"] = afi_scores
    return res
