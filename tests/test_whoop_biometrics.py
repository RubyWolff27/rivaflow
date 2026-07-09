"""Unit tests for the raw-derived biometrics provider (Wave 1b).

Pure logic — the underlying whoop_analytics functions are stubbed, so no DB is
needed. Verifies the provider reconstructs the recovery-cache record shape that
the grapple consumers expect.
"""

import pytest

from rivaflow.core import whoop_analytics
from rivaflow.core.services import whoop_biometrics


@pytest.fixture
def stub_analytics(monkeypatch):
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_rmssd",
        lambda uid, days=21: [
            {"day": "2026-07-08", "rmssd": 55.0},
            {"day": "2026-07-09", "rmssd": 48.0},
            {"day": "2026-07-10", "rmssd": 60.0},
        ],
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_hr",
        lambda uid, days=14: [
            {"day": "2026-07-09", "resting_hr": 50},
            {"day": "2026-07-10", "resting_hr": 49},
        ],
    )
    monkeypatch.setattr(
        whoop_analytics,
        "whoop_summary",
        lambda uid, today_is_sabbath=False: {
            "readiness": {"score": 72, "state": "Balanced"},
            "hrv_today": {"rmssd": 60.0},
            "resting_hr_today": {"resting_hr": 49},
            "sleep": {"duration_hours": 7.4, "quality_score": 82},
        },
    )


def test_latest_record_carries_full_snapshot(stub_analytics):
    series = whoop_biometrics.recovery_series(1, days=7)
    assert len(series) == 3
    latest = series[-1]
    assert latest["date"] == "2026-07-10"
    assert latest["recovery_score"] == 72
    assert latest["hrv_ms"] == 60.0
    assert latest["resting_hr"] == 49
    assert latest["sleep_duration_ms"] == round(7.4 * 3_600_000)
    assert latest["sleep_performance"] == 82


def test_earlier_days_are_hrv_only(stub_analytics):
    series = whoop_biometrics.recovery_series(1, days=7)
    first = series[0]
    assert first["hrv_ms"] == 55.0
    assert first["recovery_score"] is None  # readiness is a today rollup
    assert first["resting_hr"] is None  # no rhr series entry for that day


def test_locked_fields_are_none(stub_analytics):
    for r in whoop_biometrics.recovery_series(1, days=7):
        assert r["spo2"] is None
        assert r["rem_sleep_ms"] is None
        assert r["slow_wave_ms"] is None


def test_empty_when_no_raw_data(monkeypatch):
    monkeypatch.setattr(whoop_analytics, "daily_resting_rmssd", lambda uid, days=21: [])
    monkeypatch.setattr(whoop_analytics, "daily_resting_hr", lambda uid, days=14: [])
    assert whoop_biometrics.recovery_series(1) == []
    assert whoop_biometrics.latest_recovery(1) is None


def test_latest_recovery_returns_newest(stub_analytics):
    assert whoop_biometrics.latest_recovery(1)["date"] == "2026-07-10"
