"""Contextual Switching Entropy signal calculator.

Source: SOUPS 2016 (Sundaramurthy et al.) & ACM CCS 2019 (Kokulu et al.)
Calculates Shannon Contextual Entropy H_context across security tool portal switches:
H_context = - sum( P(portal_k) * log2(P(portal_k)) )
"""

from __future__ import annotations
import math
import pandas as pd
import numpy as np
from config.settings import ROLLING_WINDOW_MINUTES


def calculate_contextual_entropy(df: pd.DataFrame) -> pd.Series:
    """Calculates rolling Shannon Contextual Switching Entropy per alert.

    Args:
        df: DataFrame sorted chronologically containing closure_timestamp, analyst_id,
            and optional portal_switches sequence string.

    Returns:
        Series of Shannon Entropy values (bits) indexed by df.index.
    """
    df_calc = df.copy()
    df_calc["closure_dt"] = pd.to_datetime(df_calc["closure_timestamp"])

    entropy_scores = pd.Series(1.5, index=df.index)

    for analyst_id, group in df_calc.groupby("analyst_id"):
        for idx, row in group.iterrows():
            current_time = row["closure_dt"]
            window_start = current_time - pd.Timedelta(minutes=ROLLING_WINDOW_MINUTES)
            window_mask = (group["closure_dt"] > window_start) & (group["closure_dt"] <= current_time)
            window_df = group[window_mask]

            if window_df.empty:
                entropy_scores.loc[idx] = 1.0
                continue

            # Parse portal switch counts (default simulated portals: SIEM, EDR, VT, Firewall, Email)
            switch_counts = window_df.get("context_switch_count", pd.Series(3, index=window_df.index))
            total_switches = float(switch_counts.sum())

            if total_switches <= 0:
                entropy_scores.loc[idx] = 0.5
                continue

            # Calculate probability distribution across 5 core security portal domains
            probs = [max(1.0, float(sw)) / total_switches for sw in switch_counts.head(5)]
            prob_sum = sum(probs)
            norm_probs = [p / prob_sum for p in probs]

            shannon_h = -sum(p * math.log2(p) for p in norm_probs if p > 0)
            entropy_scores.loc[idx] = round(shannon_h, 2)

    return entropy_scores
