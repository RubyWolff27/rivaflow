"""B2 Multi-input Readiness — pure fusion-core tests (no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.readiness import (
    GREEN_CAVEAT,
    WEIGHTS,
    blend_readiness,
    zscore,
)

# --- zscore ---------------------------------------------------------------

def test_zscore_none_when_too_few():
    assert zscore([1, 2, 3]) is None          # < MIN_BASELINE_DAYS + 1
    assert zscore([]) is None


def test_zscore_known_value():
    z = zscore([1, 1, 1, 1, 1, 2])            # prior mean 1, sd 0→1.0, today 2
    assert z is not None
    assert z["z"] == pytest.approx(1.0)
    assert z["n"] == 5


def test_zscore_uses_prior_not_today():
    """The baseline excludes today, so a stable history with a high today reads as a positive deviation."""
    z = zscore([50, 50, 50, 50, 50, 50, 60])
    assert z["baseline_mean"] == pytest.approx(50.0)
    assert z["z"] > 0


# --- blend: gates ---------------------------------------------------------

def test_sabbath_is_rest_no_score():
    r = blend_readiness({"hrv": 1.0}, today_is_sabbath=True)
    assert r["state"] == "Rest"
    assert r["score"] is None
    assert r["caveat"] is None


def test_missing_hrv_is_building():
    r = blend_readiness({"hrv": None, "rhr": 0.5})
    assert r["state"] == "Building"
    assert r["score"] is None


# --- blend: fusion math ---------------------------------------------------

def test_single_signal_renormalises_to_full_weight():
    """With only HRV present its weight renormalises to 1.0, so composite == hrv z."""
    r = blend_readiness({"hrv": 1.0, "rhr": None, "resp": None, "sleep": None})
    assert r["composite_z"] == pytest.approx(1.0)
    assert r["state"] == "Prime"
    assert r["score"] == 70            # 50 + 1.0*20
    assert r["signals_used"] == ["hrv"]


def test_elevated_rhr_drags_recovery():
    """A raw +z on nocturnal RHR means WORSE recovery (direction -1) — it must pull the composite down."""
    r = blend_readiness({"hrv": 0.0, "rhr": 2.0})
    assert r["composite_z"] < 0
    assert r["state"] in ("Strained", "Rundown")
    rhr_c = next(c for c in r["contributors"] if c["signal"] == "rhr")
    assert rhr_c["effect"] < 0
    assert rhr_c["direction"] == "drags recovery"


def test_high_hrv_low_rhr_is_prime():
    r = blend_readiness({"hrv": 1.5, "rhr": -1.0, "sleep": 0.5, "resp": -0.5})
    assert r["state"] == "Prime"
    assert 0 <= r["score"] <= 100


def test_hrv_is_the_dominant_weight():
    """HRV carries the largest weight, so the same-magnitude deviation moves the score more via HRV than RHR."""
    via_hrv = blend_readiness({"hrv": -2.0, "rhr": 0.0, "sleep": 0.0, "resp": 0.0})["composite_z"]
    via_rhr = blend_readiness({"hrv": 0.0, "rhr": 2.0, "sleep": 0.0, "resp": 0.0})["composite_z"]
    assert abs(via_hrv) > abs(via_rhr)
    assert WEIGHTS["hrv"] > WEIGHTS["rhr"] > WEIGHTS["sleep"] >= WEIGHTS["resp"]


# --- blend: green != healthy caveat --------------------------------------

def test_green_states_carry_caveat():
    assert blend_readiness({"hrv": 1.0})["caveat"] == GREEN_CAVEAT      # Prime
    assert blend_readiness({"hrv": 0.0})["caveat"] == GREEN_CAVEAT      # Balanced


def test_non_green_states_have_no_caveat():
    assert blend_readiness({"hrv": -1.0})["caveat"] is None             # Strained
    assert blend_readiness({"hrv": -3.0})["caveat"] is None             # Rundown


# --- blend: bookkeeping ---------------------------------------------------

def test_score_is_clamped():
    assert blend_readiness({"hrv": 10.0})["score"] == 100
    assert blend_readiness({"hrv": -10.0})["score"] == 0


def test_contributors_sorted_by_effect_magnitude():
    r = blend_readiness({"hrv": 0.2, "rhr": 2.0})
    effects = [abs(c["effect"]) for c in r["contributors"]]
    assert effects == sorted(effects, reverse=True)
