"""P1 sleep — B9 Need/Debt, B10 Regularity (pure, no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.sleep_metrics import NEED_HOURS, sleep_debt, sleep_regularity


def test_no_debt_when_meeting_need():
    r = sleep_debt([9.0, 9.5, 9.2, 9.0, 9.1])
    assert r["debt_hours"] == pytest.approx(0.0)
    assert "no meaningful debt" in r["headline"]


def test_debt_accrues_on_short_nights():
    r = sleep_debt([7.0, 7.0, 8.0])          # short vs 9h need
    assert r["debt_hours"] == pytest.approx((9 - 7) + (9 - 7) + (9 - 8))
    assert r["need_hours"] == NEED_HOURS


def test_debt_window_limits_lookback():
    durations = [5.0] * 20                    # only last 7 counted
    r = sleep_debt(durations, window=7)
    assert r["nights"] == 7
    assert r["debt_hours"] == pytest.approx(7 * (9 - 5))


def test_debt_empty():
    assert sleep_debt([])["available"] is False


def test_regularity_high_for_consistent_bedtimes():
    r = sleep_regularity([22.5, 22.6, 22.4, 22.5, 22.5])
    assert r["score"] >= 90
    assert r["onset_sd_hours"] < 0.2


def test_regularity_handles_midnight_wrap():
    """23:30 and 00:30 are 1h apart, not 23h — circular SD must be small."""
    r = sleep_regularity([23.5, 0.5, 23.5, 0.5, 0.0])
    assert r["onset_sd_hours"] < 1.0


def test_regularity_low_for_scattered_bedtimes():
    r = sleep_regularity([20.0, 23.0, 1.0, 22.0, 19.0])
    assert r["score"] < 50


def test_regularity_needs_three_nights():
    assert sleep_regularity([22.0, 22.5])["available"] is False
