"""B11 Behaviour correlation — pure, no DB."""

from __future__ import annotations

import pytest

from rivaflow.core.behaviour import behaviour_effect, cohens_d


def test_cohens_d_known_direction():
    d = cohens_d([10, 11, 12], [5, 6, 7])
    assert d > 0


def test_cohens_d_none_on_small_or_flat():
    assert cohens_d([1], [2, 3]) is None
    assert cohens_d([5, 5, 5], [5, 5, 5]) is None


def test_behaviour_effect_large_negative():
    """Alcohol nights with clearly lower HRV → large negative delta."""
    r = behaviour_effect("alcohol", "lnRMSSD", yes_values=[3.5, 3.4, 3.6], no_values=[4.2, 4.3, 4.1])
    assert r["available"] is True
    assert r["delta"] < 0
    assert r["magnitude"] == "large"
    assert "alcohol" in r["headline"]


def test_behaviour_effect_insufficient():
    r = behaviour_effect("late-training", "lnRMSSD", [3.5], [4.0, 4.1])
    assert r["available"] is False


def test_behaviour_effect_reports_counts():
    r = behaviour_effect("sabbath-rest", "lnRMSSD", [4.5, 4.6, 4.4, 4.5], [4.0, 4.1, 3.9])
    assert r["n_yes"] == 4 and r["n_no"] == 3
    assert r["delta"] == pytest.approx(round(4.5 - 4.0, 2), abs=0.05)
