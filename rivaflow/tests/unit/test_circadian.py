"""B17 Circadian cosinor — pure, no DB."""

from __future__ import annotations

from math import cos, pi

import pytest

from rivaflow.core.circadian import cosinor


def test_cosinor_recovers_known_rhythm():
    # HR = 60 + 15*cos(omega*(t-15)) → peak at 15h, amplitude 15, mesor 60
    hours = [h for h in range(0, 24)]
    omega = 2 * pi / 24
    vals = [60 + 15 * cos(omega * (h - 15)) for h in hours]
    r = cosinor(hours, vals)
    assert r["available"] is True
    assert r["mesor"] == pytest.approx(60, abs=1.0)
    assert r["amplitude"] == pytest.approx(15, abs=1.0)
    assert r["acrophase_hour"] == pytest.approx(15, abs=0.5)


def test_cosinor_needs_points():
    assert cosinor([1, 2, 3], [1, 2, 3])["available"] is False
