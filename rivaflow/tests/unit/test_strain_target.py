"""B5 Strain Target / Load Coach — pure-core tests (no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.strain_target import DEFAULT_CHRONIC, STRAIN_CAP, prescribe_strain


def test_prime_allows_above_usual():
    r = prescribe_strain("Prime", chronic_load=10.0)
    assert r["available"] is True
    assert r["target_load"] == pytest.approx(11.5)
    assert r["capped"] is False
    assert r["band"] == [9.5, 13.5]


def test_balanced_matches_usual():
    r = prescribe_strain("Balanced", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(10.0)
    assert r["capped"] is False


def test_strained_caps_below_usual():
    r = prescribe_strain("Strained", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(6.0)
    assert r["capped"] is True
    assert "capped" in r["headline"]


def test_rundown_is_a_hard_cap():
    r = prescribe_strain("Rundown", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(4.0)
    assert r["capped"] is True


def test_rest_and_building_have_no_target():
    assert prescribe_strain("Rest", 10.0)["available"] is False
    assert prescribe_strain("Building", None)["available"] is False
    assert prescribe_strain(None, 10.0)["available"] is False


def test_unknown_state_is_unavailable():
    assert prescribe_strain("Nonsense", 10.0)["available"] is False


def test_no_history_uses_default_base():
    r = prescribe_strain("Prime", chronic_load=None)
    assert r["chronic_load"] == pytest.approx(DEFAULT_CHRONIC)
    assert r["target_load"] == pytest.approx(DEFAULT_CHRONIC * 1.15)


def test_target_is_capped_at_21():
    r = prescribe_strain("Prime", chronic_load=20.0)  # 20 * 1.15 = 23 → capped
    assert r["target_load"] == STRAIN_CAP
    assert r["band"][1] == STRAIN_CAP


def test_acute_below_target_reports_headroom():
    r = prescribe_strain("Balanced", chronic_load=10.0, acute_load=4.0)
    assert r["acute_load"] == pytest.approx(4.0)
    assert r["remaining"] == pytest.approx(6.0)


def test_acute_at_or_above_target_flips_headline():
    r = prescribe_strain(
        "Strained", chronic_load=10.0, acute_load=8.0
    )  # target 6, already 8
    assert r["remaining"] == pytest.approx(0.0)
    assert "hit today's target" in r["headline"]
    assert "recover now" in r["headline"]  # capped state → recover
