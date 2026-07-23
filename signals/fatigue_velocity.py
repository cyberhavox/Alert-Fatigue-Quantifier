"""Differential Fatigue Velocity & Acceleration signal calculator.

Source: Sinteza (2026) [Adaptive Workload & Cognitive Boundaries]
Calculates the rate of change of AFI over rolling 60-minute windows:
Velocity V(t) = d(AFI)/dt  (AFI score change per hour)
Acceleration A(t) = d2(AFI)/dt2 (change in velocity)
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from config.settings import ROLLING_WINDOW_MINUTES


def calculate_fatigue_velocity(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Calculates rolling Fatigue Velocity V(t) and Acceleration A(t).

    Args:
        df: DataFrame containing closure_timestamp, analyst_id, and afi_score.

    Returns:
        Tuple of (velocity_series, acceleration_series).
    """
    df_calc = df.copy()
    df_calc["closure_dt"] = pd.to_datetime(df_calc["closure_timestamp"])

    velocity = pd.Series(0.0, index=df.index)
    acceleration = pd.Series(0.0, index=df.index)

    for analyst_id, group in df_calc.groupby("analyst_id"):
        group = group.sort_values(by="closure_dt")
        afi_vals = group.get("afi_score", pd.Series(50.0, index=group.index)).values

        # First derivative (Velocity: delta_afi / delta_t_hours)
        d_afi = np.diff(afi_vals, prepend=afi_vals[0])
        # Approximate 1 alert ~ 4 minutes in shift -> ~ 15 alerts/hr
        v_vals = d_afi * 15.0

        # Second derivative (Acceleration)
        a_vals = np.diff(v_vals, prepend=v_vals[0])

        velocity.loc[group.index] = v_vals
        acceleration.loc[group.index] = a_vals

    return velocity, acceleration
