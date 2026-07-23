"""Automation Bias Index (ABI) signal calculator.

Source: Alahmadi et al. (2022) [USENIX Security 2022]
Calculates the ratio of alerts resolved by accepting default/AI recommendations
without performing manual enrichment lookups in the rolling window.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from config.settings import ROLLING_WINDOW_MINUTES


def calculate_automation_bias(df: pd.DataFrame) -> pd.Series:
    """Calculates rolling Automation Bias Index (ABI) per alert.

    ABI = (AI accepted closures with zero enrichment) / (Total closures in rolling window)

    Args:
        df: DataFrame sorted chronologically containing closure_timestamp,
            enrichment_actions, and optional ai_accepted flag.

    Returns:
        Series of ABI ratio scores (0.0 to 1.0) indexed by df.index.
    """
    df_calc = df.copy()
    df_calc["closure_dt"] = pd.to_datetime(df_calc["closure_timestamp"])

    ai_accepted = df_calc.get("ai_accepted", pd.Series(0, index=df_calc.index))
    enrichment = df_calc.get("enrichment_actions", pd.Series(0, index=df_calc.index))

    # Blind acceptance = accepted AI recommendation AND zero enrichment lookups
    df_calc["is_blind_acceptance"] = ((ai_accepted == 1) & (enrichment == 0)).astype(int)

    abi_scores = pd.Series(0.0, index=df.index)

    for analyst_id, group in df_calc.groupby("analyst_id"):
        for idx, row in group.iterrows():
            current_time = row["closure_dt"]
            window_start = current_time - pd.Timedelta(minutes=ROLLING_WINDOW_MINUTES)
            window_mask = (group["closure_dt"] > window_start) & (group["closure_dt"] <= current_time)
            window_df = group[window_mask]

            total_alerts = len(window_df)
            if total_alerts > 0:
                blind_count = window_df["is_blind_acceptance"].sum()
                abi_scores.loc[idx] = float(blind_count / total_alerts)
            else:
                abi_scores.loc[idx] = 0.0

    return abi_scores
