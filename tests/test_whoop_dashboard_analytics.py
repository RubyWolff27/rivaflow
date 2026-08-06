"""WHOOP dashboard analytics panels are all honest-empty stubs since v2 Wave 1c.

The raw BLE feed retired with the self-hosted WHOOP backend, so every panel —
including cardiovascular drift, which used to compute from the raw HR stream —
returns a correctly-shaped empty payload. The web WhoopAnalyticsTab renders a
panel only when it has data, so they all hide until Wave 2 repoints these to
Fitbit Air / Google Health data.
"""

from rivaflow.core.services import whoop_dashboard_analytics as wda


def test_cardiovascular_drift_is_honest_empty():
    c = wda.cardiovascular_drift(1, days=90)
    assert set(c.keys()) == {
        "weekly_rhr",
        "slope",
        "trend",
        "current_rhr",
        "baseline_rhr",
        "insight",
    }
    assert c["weekly_rhr"] == []
    assert c["trend"] == "insufficient_data"
    assert c["current_rhr"] is None


def test_honest_empty_panels_match_frontend_contract():
    pc = wda.performance_correlation(1)
    assert pc["recovery_correlation"]["scatter"] == []
    assert pc["recovery_correlation"]["zones"] == {}
    assert pc["hrv_predictor"]["scatter"] == []

    ef = wda.efficiency(1)
    assert ef["strain_efficiency"]["top_sessions"] == []
    assert ef["sleep_analysis"]["scatter"] == []

    assert wda.readiness_model(1)["zones"] == {}
    assert wda.sleep_debt_tracker(1)["weekly"] == []
