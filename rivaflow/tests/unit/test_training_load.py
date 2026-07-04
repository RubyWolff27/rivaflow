"""P1 training-load — B7 ACWR, B8 HRR, B12 recovery-cost (pure, no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.training_load import acwr, heart_rate_recovery, recovery_cost

# --- B7 ACWR --------------------------------------------------------------

def test_acwr_needs_chronic_window():
    assert acwr([10] * 20)["available"] is False


def test_acwr_sweet_spot():
    r = acwr([10] * 28)
    assert r["ratio"] == pytest.approx(1.0)
    assert r["zone"] == "sweet-spot"


def test_acwr_high_risk_on_spike():
    load = [5] * 21 + [15] * 7           # chronic ~7.5, acute 15 → ratio ~2.0
    r = acwr(load)
    assert r["ratio"] > 1.5
    assert r["zone"] == "high-risk"


def test_acwr_undertraining():
    load = [12] * 21 + [4] * 7           # acute below chronic
    assert acwr(load)["zone"] == "undertraining"


# --- B8 HRR ---------------------------------------------------------------

def test_hrr_measures_drop_after_peak():
    hr = [120, 150, 180, 160, 140, 120] + [110] * 60   # peak 180 at idx2, +60s = 110
    r = heart_rate_recovery(hr, window_sec=60)
    assert r["available"] is True
    assert r["peak"] == 180
    assert r["hrr_bpm"] == 180 - hr[2 + 60]
    assert "not a mortality marker" in r["note"]


def test_hrr_unclean_when_peak_near_end():
    hr = [120, 140, 180]                 # peak at the very end
    r = heart_rate_recovery(hr, window_sec=60)
    assert r["available"] is False
    assert r["clean"] is False


# --- B12 recovery-cost coupling -------------------------------------------

def test_recovery_cost_negative_slope():
    """Higher prior-day load → lower next-day recovery ⇒ negative slope."""
    load = [1, 5, 1, 5, 1, 5, 1, 5]
    nextm = [10, 10, 6, 10, 6, 10, 6, 10]   # after a load=5 day, next metric is low
    r = recovery_cost(load, nextm)
    assert r["available"] is True
    assert r["slope"] < 0
    assert "costs" in r["headline"]


def test_recovery_cost_needs_enough_pairs():
    assert recovery_cost([1, 2], [3, 4])["available"] is False


def test_recovery_cost_no_variance():
    assert recovery_cost([5] * 8, [5] * 8)["available"] is False
