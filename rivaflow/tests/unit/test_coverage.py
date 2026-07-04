"""B3 capture-coverage / RR-coverage guard — pure-core tests (no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.coverage import (
    MIN_CONTIGUOUS_MINUTES,
    MIN_RR_MINUTES,
    assess_coverage,
    coverage_in_days,
)


def test_well_covered_night_is_sufficient():
    """~10 min of contiguous in-band RR clears both thresholds."""
    rr = [1000] * 600  # 600 intervals * 1000 ms = 600 s = 10 min
    cov = assess_coverage(rr, hr_samples=600)
    assert cov.rr_minutes == pytest.approx(10.0, abs=0.1)
    assert cov.longest_segment_minutes == pytest.approx(10.0, abs=0.1)
    assert cov.sufficient is True
    assert cov.reason == "sufficient"


def test_rr_starved_night_excluded_despite_full_hr():
    """The core B3 case: 8 h of HR backfill but almost no RR (phone charging away). The HR view looks fine;
    the guard must still exclude the night and NAME the masking."""
    rr = [1000] * 60  # 1 min of RR only
    hr = 8 * 3600  # 8 h of HR samples at 1 Hz
    cov = assess_coverage(rr, hr_samples=hr)
    assert cov.rr_minutes == pytest.approx(1.0, abs=0.1)
    assert cov.hr_minutes == pytest.approx(480.0, abs=1)
    assert cov.sufficient is False
    assert "RR-starved" in cov.reason and "charging" in cov.reason


def test_low_capture_below_rr_threshold():
    rr = [1000] * 120  # 2 min < MIN_RR_MINUTES
    cov = assess_coverage(rr, hr_samples=120)
    assert cov.rr_minutes < MIN_RR_MINUTES
    assert cov.sufficient is False
    assert "Low capture" in cov.reason


def test_fragmented_night_fails_contiguity():
    """Enough total RR minutes, but broken into sub-2-minute runs by repeated artifacts → excluded."""
    block = [1000] * 60  # 1-min clean run
    junk = [200]  # one impossible beat splits the runs
    rr = []
    for _ in range(8):  # 8 min total in-band, but longest run only 1 min
        rr += block + junk
    cov = assess_coverage(rr, hr_samples=len(rr))
    assert cov.rr_minutes >= MIN_RR_MINUTES
    assert cov.longest_segment_minutes < MIN_CONTIGUOUS_MINUTES
    assert cov.sufficient is False
    assert "Fragmented" in cov.reason


def test_out_of_band_beats_dont_count_as_rr_minutes():
    rr = [200] * 1000  # impossible beats — zero usable RR
    cov = assess_coverage(rr, hr_samples=1000)
    assert cov.rr_minutes == 0.0
    assert cov.rr_intervals == 0
    assert cov.sufficient is False


def test_empty_day():
    cov = assess_coverage([], hr_samples=0)
    assert cov.rr_minutes == 0.0
    assert cov.hr_minutes == 0.0
    assert cov.sufficient is False


def test_coverage_in_days_summary():
    good = assess_coverage([1000] * 600, hr_samples=600)
    bad = assess_coverage([1000] * 30, hr_samples=8 * 3600)
    summ = coverage_in_days([good, bad, good])
    assert summ["days_total"] == 3
    assert summ["days_sufficient"] == 2
    assert summ["days_excluded"] == 1
    assert summ["rr_coverage_pct"] == pytest.approx(66.7, abs=0.1)


def test_coverage_in_days_empty():
    summ = coverage_in_days([])
    assert summ["days_total"] == 0
    assert summ["rr_coverage_pct"] == 0.0
