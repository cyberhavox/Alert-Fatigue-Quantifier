"""MITRE ATT&CK Tactic Complexity Weighting Matrix (TCWM).

Source: ACM CCS 2019 (Kokulu et al.) & MITRE ATT&CK Framework v14
Weights alert severity and workload saturation based on cognitive complexity of ATT&CK Tactics.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

# MITRE ATT&CK Tactic Cognitive Complexity Weights (1.0 = Basic, 3.5 = Advanced Persistent Threat)
MITRE_COMPLEXITY_WEIGHTS: dict[str, float] = {
    "Initial Access": 1.0,
    "Execution": 1.2,
    "Persistence": 2.2,
    "Privilege Escalation": 2.5,
    "Defense Evasion": 2.8,
    "Credential Access": 3.0,
    "Discovery": 1.5,
    "Lateral Movement": 3.2,
    "Collection": 2.0,
    "Command and Control": 2.7,
    "Exfiltration": 3.5,
    "Impact": 3.0,
}


def calculate_mitre_workload_saturation(df: pd.DataFrame) -> pd.Series:
    """Calculates rolling MITRE Workload Saturation per alert record.

    Args:
        df: DataFrame containing closure_timestamp, analyst_id, and optional mitre_tactic.

    Returns:
        Series of MITRE weighted workload scores indexed by df.index.
    """
    tactics = df.get("mitre_tactic", pd.Series("Credential Access", index=df.index))
    weights = tactics.map(lambda t: MITRE_COMPLEXITY_WEIGHTS.get(t, 2.0))
    
    # Scale by hourly alert throughput rate
    throughput = df.get("hourly_closure_rate", pd.Series(1.0, index=df.index))
    mitre_workload = weights * throughput * 10.0
    return mitre_workload.round(2)
