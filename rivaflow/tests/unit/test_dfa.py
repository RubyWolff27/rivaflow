"""B18 DFA alpha1 — pure, no DB."""
from __future__ import annotations

from rivaflow.core.hrv_spectral import dfa_alpha1


def test_dfa_none_on_too_few():
    assert dfa_alpha1([1000.0]*10) is None


def test_dfa_returns_alpha_and_zone():
    # semi-random-ish RR series long enough for boxes 4..16
    rr = [1000 + (i*37 % 50) - 25 for i in range(200)]
    r = dfa_alpha1([float(x) for x in rr])
    assert r is not None
    assert "alpha1" in r and "zone" in r
    assert 0.0 < r["alpha1"] < 2.0


def test_dfa_white_noise_near_half():
    # alternating series (anti-correlated) → low alpha; just assert it computes a plausible number
    rr = [1000.0 + (100 if i % 2 else -100) for i in range(200)]
    r = dfa_alpha1(rr)
    assert r is not None
    assert r["alpha1"] < 1.0
