"""B19 Weekly/Monthly assessment — pure, no DB."""

from __future__ import annotations

from rivaflow.core.assessment import period_assessment


def test_rising_hrv_is_improving():
    r = period_assessment("week", {"lnrmssd": [3.8, 3.8, 4.2, 4.3]})
    assert r["available"] is True
    assert "HRV (lnRMSSD)" in r["improving"]


def test_rising_rhr_is_declining():
    r = period_assessment("week", {"rhr": [50, 50, 55, 56]})
    assert "Resting HR" in r["declining"]


def test_empty_series_unavailable():
    assert period_assessment("month", {"lnrmssd": [1, 2]})["available"] is False


def test_headline_mentions_period():
    r = period_assessment(
        "month", {"lnrmssd": [3.8, 3.9, 4.2, 4.3], "rhr": [55, 54, 51, 50]}
    )
    assert "month" in r["headline"]
