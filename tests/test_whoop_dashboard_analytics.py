"""Unit tests for the raw-derived WHOOP dashboard analytics (Wave 1b-cleanup).

Cardiovascular drift is stubbed on daily_resting_hr (no DB). The other panels
return honest-empty payloads whose shapes must match what the web
WhoopAnalyticsTab reads, so it renders/hides panels correctly.
"""

import pytest

from rivaflow.core import whoop_analytics
from rivaflow.core.services import whoop_dashboard_analytics as wda


@pytest.fixture
def stub_rhr(monkeypatch):
    # Three ISO weeks of resting HR, gently declining (improving fitness).
    rows = []
    for wk, base in enumerate((54, 52, 50)):
        for d in range(3):
            rows.append(
                {"day": f"2026-06-{1 + wk * 7 + d:02d}", "resting_hr": base + d}
            )
    monkeypatch.setattr(whoop_analytics, "daily_resting_hr", lambda uid, days=90: rows)


def test_cardiovascular_drift_shape_and_trend(stub_rhr):
    c = wda.cardiovascular_drift(1, days=90)
    assert set(c.keys()) == {
        "weekly_rhr",
        "slope",
        "trend",
        "current_rhr",
        "baseline_rhr",
        "insight",
    }
    assert len(c["weekly_rhr"]) == 3
    assert all(set(w) == {"week", "avg_rhr", "data_points"} for w in c["weekly_rhr"])
    assert c["trend"] == "improving"  # declining RHR
    assert c["baseline_rhr"] > c["current_rhr"]


def test_cardiovascular_insufficient_data(monkeypatch):
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_hr",
        lambda uid, days=90: [{"day": "2026-06-01", "resting_hr": 50}],
    )
    c = wda.cardiovascular_drift(1)
    assert c["trend"] == "insufficient_data"
    assert c["weekly_rhr"] == []


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
