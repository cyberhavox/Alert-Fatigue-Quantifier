"""Tool Friction & Context Switching Frequency signal calculator.

Source: Kokulu et al. (2019) [ACM CCS 2019] & Sundaramurthy et al. (2016) [SOUPS 2016]
Calculates the mean number of security tool/portal context switches per ticket
in the rolling window.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from config.settings import ROLLING_WINDOW_MINUTES


def calculate_context_switching(df: pd.DataFrame) -> pd.Series:
    """Calculates rolling mean Tool Friction / Context Switch count per alert.

    Args:
        df: DataFrame sorted chronologically containing closure_timestamp
            and context_switch_count.

    Returns:
        Series of mean context switches per ticket in rolling window.
    """
    df_calc = df.copy()
    df_calc["closure_dt"] = pd.to_datetime(df_calc["closure_timestamp"])

    context_switches = df_calc.get("context_switch_count", pd.Series(2, index=df_calc.index))
    df_calc["switches"] = context_switches

    cs_scores = pd.Series(2.0, index=df.index)

    for analyst_id, group in df_calc.groupby("analyst_id"):
        for idx, row in group.iterrows():
            current_time = row["closure_dt"]
            window_start = current_time - pd.Timedelta(minutes=ROLLING_WINDOW_MINUTES)
            window_mask = (group["closure_dt"] > window_start) & (group["closure_dt"] <= current_time)
            window_df = group[window_mask]

            if not window_df.empty:
                cs_scores.loc[idx] = float(window_df["switches"].mean())
            else:
                cs_scores.loc[idx] = 2.0

    return cs_scores
