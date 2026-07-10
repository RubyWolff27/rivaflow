"""Readiness Scorer seam (Wave 2.5).

The weights/bands/version live in a swappable ReadinessModel. These verify the
default heuristic is behaviour-identical and that a fitted/learned model can be
swapped in without touching blend_readiness. Pure functions — no DB.
"""

import pytest

from rivaflow.core.readiness import (
    ReadinessModel,
    blend_readiness,
    get_readiness_model,
    set_readiness_model,
)


@pytest.fixture(autouse=True)
def _restore_default_model():
    yield
    set_readiness_model(None)  # never leak a swapped model into other tests


@pytest.mark.parametrize(
    "hrv_z,expected_state",
    [
        (1.0, "Prime"),
        (0.5, "Prime"),
        (0.0, "Balanced"),
        (-0.5, "Balanced"),
        (-1.0, "Strained"),
        (-1.5, "Strained"),
        (-2.0, "Rundown"),
    ],
)
def test_default_bands_unchanged(hrv_z, expected_state):
    assert blend_readiness({"hrv": hrv_z})["state"] == expected_state


def test_default_stamps_heuristic_version_and_score():
    r = blend_readiness({"hrv": 1.0})
    assert r["score_version"] == "heuristic-v1"
    assert r["score"] == 70  # 50 + composite(1.0) * 20


def test_sabbath_and_cold_start_still_guard():
    assert blend_readiness({}, today_is_sabbath=True)["state"] == "Rest"
    assert blend_readiness({"hrv": None})["state"] == "Building"


def test_swap_model_changes_weights_and_version():
    set_readiness_model(
        ReadinessModel(
            weights={"hrv": 1.0, "rhr": 0.0, "sleep": 0.0, "resp": 0.0},
            version="test-v2",
        )
    )
    # rhr weight is now 0, so a terrible rhr z must not drag the score down.
    r = blend_readiness({"hrv": 0.6, "rhr": -3.0})
    assert r["score_version"] == "test-v2"
    assert r["state"] == "Prime"  # composite 0.6 >= 0.5, rhr ignored


def test_set_none_restores_default():
    set_readiness_model(ReadinessModel(weights={"hrv": 1.0}, version="tmp"))
    set_readiness_model(None)
    assert get_readiness_model().version == "heuristic-v1"
