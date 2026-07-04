"""B0 QC-gate tests — the foundation every RR-derived metric consumes."""

from __future__ import annotations

from math import log

import pytest

from rivaflow.core.rr_quality import (
    MALIK_REL_THRESHOLD,
    MAX_ARTIFACT_FRACTION,
    RR_MAX_MS,
    RR_MIN_MS,
    assess_rr,
    clean_segments,
    ln_rmssd,
    rmssd,
)


def test_clean_series_no_artifacts():
    """A steady physiological series passes untouched at 0% artifact and is usable."""
    series = [
        900 + (i % 5) for i in range(60)
    ]  # small physiological jitter, all in-band, all <20% jumps
    q = assess_rr(series)
    assert q.n_flagged == 0
    assert q.artifact_pct == 0.0
    assert q.usable is True
    assert len(q.cleaned) == 60
    assert q.corrected_idx == []


def test_bradycardia_beats_are_kept():
    """A trained athlete's slow nocturnal beats (RR up to ~1600 ms / ~37 bpm) must survive — the old
    1500 ms ceiling clipped them and biased RMSSD downward."""
    series = [
        1550 + (i % 3) for i in range(40)
    ]  # ~38-39 bpm, above the old 1500 ms cap, inside the new band
    q = assess_rr(series)
    assert RR_MIN_MS <= 1550 <= RR_MAX_MS
    assert q.n_flagged == 0
    assert q.usable is True


def test_relative_filter_catches_ectopic_the_absolute_filter_missed():
    """A single ectopic beat jumps ~300 ms — under the old absolute 400 ms drop it slipped through and
    inflated RMSSD. The Malik relative (>20%) filter flags it and interpolation repairs it.
    """
    series = [800] * 30
    series[15] = (
        1150  # +350 ms = +43% jump; passes |diff|<400 but fails the 20% relative test
    )
    q = assess_rr(series)
    assert q.n_flagged == 1
    assert 15 in q.corrected_idx or any(
        abs(v - 800) < 1 for v in [q.cleaned[i] for i in q.corrected_idx]
    )
    # interpolated between two 800s → back to 800, so RMSSD collapses to ~0
    assert rmssd(q.cleaned) == pytest.approx(0.0, abs=1e-6)


def test_out_of_band_flagged_as_artifact():
    """Values outside the physiological band are flagged and, mid-series, interpolated."""
    series = [850] * 20 + [200] + [850] * 20  # 200 ms = 300 bpm, impossible
    q = assess_rr(series)
    assert q.n_flagged == 1
    assert q.cleaned[20] == pytest.approx(
        850, abs=1e-6
    )  # interpolated back to neighbours


def test_artifact_pct_and_usability_gate():
    """A series above the 30% artifact budget is marked unusable so it can't poison a baseline."""
    good = [850] * 10
    bad = [300, 1900] * 10  # 20 out-of-band intervals
    q = assess_rr(good + bad)
    assert q.artifact_pct > MAX_ARTIFACT_FRACTION * 100.0
    assert q.usable is False


def test_edge_flagged_run_is_dropped_not_fabricated():
    """A flagged run at the series edge has no left neighbour to interpolate from, so it is dropped —
    we never fabricate beats across a true dropout."""
    series = [300, 300] + [850] * 40  # leading artifacts, no prior valid beat
    q = assess_rr(series)
    assert q.n_flagged == 2
    assert (
        len(q.cleaned) == 40
    )  # the two leading artifacts are dropped, not interpolated
    assert q.corrected_idx == []


def test_clean_segments_splits_on_gap_and_respects_min_len():
    """clean_segments returns only contiguous in-spec runs >= min_len, splitting at an artifact."""
    seg_a = [850] * 40
    seg_b = [860] * 40
    series = seg_a + [200] + seg_b  # a single impossible beat splits the two runs
    segs = clean_segments(series, min_len=30)
    assert len(segs) == 2
    assert all(len(s) >= 30 for s in segs)
    # a short run below min_len is discarded
    assert clean_segments([850] * 10, min_len=30) == []


def test_rmssd_and_ln_rmssd_math():
    """RMSSD matches the closed-form on a known series; lnRMSSD is its log."""
    series = [800, 810, 800, 810, 800]  # successive diffs alternate +/-10 → RMSSD = 10
    assert rmssd(series) == pytest.approx(10.0)
    assert ln_rmssd(series) == pytest.approx(log(10.0))


def test_rmssd_none_on_too_few():
    assert rmssd([800]) is None
    assert ln_rmssd([800]) is None


def test_relative_threshold_boundary():
    """A jump of exactly the threshold is kept; just over it is flagged."""
    at = 800 * (1 + MALIK_REL_THRESHOLD)  # exactly +20% → kept
    over = 800 * (1 + MALIK_REL_THRESHOLD) + 5  # just over → flagged
    assert assess_rr([800, at, 800]).n_flagged == 0
    assert assess_rr([800, over, 800]).n_flagged == 1


def test_empty_series():
    q = assess_rr([])
    assert q.n_raw == 0
    assert q.usable is False
    assert q.artifact_pct == 100.0
