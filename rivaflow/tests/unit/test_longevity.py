"""P2 longevity — B14 VO2max, B15 cardio-age proxy (pure, no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.longevity import cardio_age_proxy, passive_vo2max


def test_vo2max_is_banded_not_a_point():
    r = passive_vo2max(hr_max=177, hr_rest=50)
    assert r["available"] is True
    assert r["vo2max_estimate"] == pytest.approx(15.3 * 177 / 50, abs=0.1)
    assert r["range"][0] < r["vo2max_estimate"] < r["range"][1]


def test_vo2max_rejects_bad_inputs():
    assert passive_vo2max(0, 50)["available"] is False
    assert passive_vo2max(150, 160)["available"] is False   # max below rest


def test_cardio_age_proxy_is_flagged_proxy():
    r = cardio_age_proxy(vo2max=50, age=44)
    assert r["available"] is True
    assert r["is_proxy"] is True
    assert "not clinical" in r["note"]


def test_fitter_reads_younger():
    fit = cardio_age_proxy(vo2max=55, age=44)["cardio_age_proxy"]
    unfit = cardio_age_proxy(vo2max=35, age=44)["cardio_age_proxy"]
    assert fit < unfit


def test_cardio_age_clamped():
    r = cardio_age_proxy(vo2max=90, age=44)   # very fit → clamped at 18
    assert r["cardio_age_proxy"] >= 18
