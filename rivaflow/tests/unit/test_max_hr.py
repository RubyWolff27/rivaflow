"""B1 Max-HR calibration — pure-core tests (no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.max_hr import calibrate_max_hr, sustained_max, tanaka_max


def test_tanaka_for_ruby():
    assert tanaka_max(44) == pytest.approx(177.2)


# --- sustained_max: the artifact guard ------------------------------------

def test_single_spike_does_not_set_max():
    """A lone 200 bpm sample among 120s must NOT raise the sustained max — the core artifact rejection."""
    hr = [120] * 60
    hr[30] = 200
    assert sustained_max(hr, window=10) == 120


def test_sustained_plateau_is_captured():
    """A genuine 15-sample run at 185 IS a sustained max."""
    hr = [120] * 20 + [185] * 15 + [120] * 20
    assert sustained_max(hr, window=10) == 185


def test_sustained_max_none_when_too_short():
    assert sustained_max([180] * 5, window=10) is None


# --- calibrate: observed vs Tanaka ----------------------------------------

def test_observed_above_tanaka_is_used():
    hr = [120] * 30 + [186] * 15 + [120] * 30   # sustained 186 > Tanaka 177
    r = calibrate_max_hr(hr, age=44)
    assert r["source"] == "observed_sustained"
    assert r["max_hr"] == 186
    assert r["floor"] is False
    assert r["uncertainty"] == [181, 191]


def test_submaximal_observed_falls_back_to_tanaka_with_floor():
    """Low-endurance athlete never nears max: observed 150 < Tanaka → floor flag, Tanaka estimate."""
    hr = [120] * 30 + [150] * 15 + [120] * 30
    r = calibrate_max_hr(hr, age=44)
    assert r["source"] == "tanaka_default"
    assert r["max_hr"] == 177
    assert r["floor"] is True
    assert r["observed_sustained"] == 150
    assert "sub-maximal" in r["note"]


def test_no_data_uses_tanaka_no_floor():
    r = calibrate_max_hr([], age=44)
    assert r["source"] == "tanaka_default"
    assert r["max_hr"] == 177
    assert r["floor"] is False
    assert r["uncertainty"] == [167, 187]


def test_impossible_readings_are_rejected_before_calibrating():
    """A 260 bpm spike is out of range and filtered; the real sustained level (120) drives the floor."""
    hr = [120] * 40 + [260] * 20        # 260 > HR_CEILING, dropped
    r = calibrate_max_hr(hr, age=44)
    assert r["observed_sustained"] == 120
    assert r["source"] == "tanaka_default"
    assert r["floor"] is True


def test_kills_the_190_default():
    """Regression: whatever Ruby's calibrated value, it must not be the old ~30yo 190 unless he truly
    sustains it — with sub-maximal data it lands at his age-predicted 177, not 190."""
    r = calibrate_max_hr([130] * 100, age=44)
    assert r["max_hr"] == 177
    assert r["max_hr"] != 190


def test_uncertainty_band_always_present():
    for hr in ([], [130] * 100, [120] * 30 + [186] * 15):
        r = calibrate_max_hr(hr, age=44)
        assert isinstance(r["uncertainty"], list) and len(r["uncertainty"]) == 2
        assert r["uncertainty"][0] < r["uncertainty"][1]
