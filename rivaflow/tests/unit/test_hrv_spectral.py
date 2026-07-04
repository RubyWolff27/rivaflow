"""B4 frequency-domain + non-linear HRV — pure-core tests (no DB)."""

from __future__ import annotations

from math import pi, sin, sqrt

import pytest

from rivaflow.core.hrv_spectral import (
    MIN_BEATS,
    frequency_domain,
    poincare,
    sdnn,
)


def _modulated_rr(
    freq_hz: float, n: int = 400, base: float = 1000.0, amp: float = 40.0
) -> list[float]:
    """RR series (~1 beat/s) oscillating at freq_hz — a synthetic respiratory/baroreflex signal."""
    return [base + amp * sin(2 * pi * freq_hz * i) for i in range(n)]


def test_hf_modulation_shows_hf_dominant():
    """A 0.25 Hz oscillation (respiratory band) must put more power in HF than LF."""
    fd = frequency_domain(_modulated_rr(0.25))
    assert fd is not None
    assert fd.hf > fd.lf
    assert fd.hf_nu > fd.lf_nu


def test_lf_modulation_shows_lf_dominant():
    """A 0.10 Hz oscillation (LF band) must put more power in LF than HF."""
    fd = frequency_domain(_modulated_rr(0.10))
    assert fd is not None
    assert fd.lf > fd.hf


def test_short_window_returns_none():
    """Below 5 min / 150 beats, spectral HRV is not computed."""
    assert frequency_domain(_modulated_rr(0.25, n=100)) is None  # too few beats
    assert frequency_domain([250.0] * 200) is None  # 200 beats * 0.25s = 50s < 5min


def test_lf_hf_note_is_not_sympatho_vagal():
    fd = frequency_domain(_modulated_rr(0.25))
    d = fd.as_dict()
    assert "NOT a sympatho-vagal" in d["note"]
    assert "lf_hf" in d


def test_poincare_sd1_equals_rmssd_over_sqrt2():
    """SD1 must equal SD(successive diffs)/√2 — confirming it carries no info beyond RMSSD."""
    rr = _modulated_rr(0.2, n=300)
    diffs = [rr[i + 1] - rr[i] for i in range(len(rr) - 1)]
    dmean = sum(diffs) / len(diffs)
    sdsd = sqrt(sum((d - dmean) ** 2 for d in diffs) / len(diffs))
    pc = poincare(rr)
    assert pc is not None
    assert pc.sd1 == pytest.approx(sdsd / sqrt(2), rel=1e-6)
    assert pc.sd2 > 0
    assert pc.ratio == pytest.approx(pc.sd2 / pc.sd1, rel=1e-6)


def test_poincare_note_flags_sd1_identity():
    pc = poincare(_modulated_rr(0.2, n=200))
    assert "RMSSD" in pc.as_dict()["note"]


def test_sdnn_matches_manual():
    vals = [900.0, 1000.0, 1100.0]
    m = 1000.0
    expect = sqrt(sum((x - m) ** 2 for x in vals) / 3)
    assert sdnn(vals) == pytest.approx(expect)


def test_sdnn_none_on_too_few():
    assert sdnn([900.0]) is None


def test_min_beats_constant_guard():
    assert frequency_domain([1000.0] * (MIN_BEATS - 1)) is None
