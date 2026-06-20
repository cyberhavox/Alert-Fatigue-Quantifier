"""Unit tests for the advisory recommendations engine.
"""

from recommendations.engine import get_advisory_recommendations


def test_get_advisory_recommendations_routing() -> None:
    """Verifies that AFI scores are correctly mapped to their respective severity states."""
    # 1. Nominal
    res = get_advisory_recommendations(30.0, [], 0)
    assert res["state"] == "NOMINAL"
    assert "disclaimer" in res
    assert "All recommendations are advisory" in res["disclaimer"]

    # 2. Elevated
    res = get_advisory_recommendations(60.0, [], 0)
    assert res["state"] == "ELEVATED"

    # 3. High
    res = get_advisory_recommendations(80.0, [], 0)
    assert res["state"] == "HIGH"

    # 4. Critical
    res = get_advisory_recommendations(95.0, [], 0)
    assert res["state"] == "CRITICAL"


def test_get_advisory_recommendations_warnings() -> None:
    """Verifies that anomalies list and ML predictions trigger appropriate warning strings."""
    anomalies = [
        {"Signal": "Enrichment Depth", "Deviation": -2.5, "p-value": 0.01}
    ]
    
    # Run with anomaly and prediction flag
    res = get_advisory_recommendations(80.0, anomalies, 1)
    
    warnings = res["warnings"]
    assert len(warnings) == 2
    
    # Assert that warnings contain descriptions of both the statistical drop and ML risk
    assert any("enrichment depth" in w.lower() for w in warnings)
    assert any("predictive risk" in w.lower() for w in warnings)
