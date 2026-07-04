"""B16 Resilience & Cumulative Stress — pure, no DB."""

from __future__ import annotations

from rivaflow.core.resilience import cumulative_stress, resilience


def test_resilience_high_when_recent_at_baseline_and_stable():
    r = resilience(recent_lnrmssd=[4.0] * 14, baseline_lnrmssd=[4.0] * 30)
    assert r["available"] is True
    assert r["level"] in ("Solid", "Strong", "Exceptional")


def test_resilience_low_when_recent_suppressed():
    r = resilience(recent_lnrmssd=[3.0] * 14, baseline_lnrmssd=[4.0] * 30 + [4.1, 3.9])
    assert r["level_vs_baseline_z"] < 0


def test_resilience_needs_enough_data():
    assert resilience([4.0] * 3, [4.0] * 30)["available"] is False


def test_cumulative_stress_bands():
    assert cumulative_stress([False] * 31)["band"] == "low"
    assert cumulative_stress([True] * 20 + [False] * 11)["band"] == "high"


def test_cumulative_stress_window():
    r = cumulative_stress([True] * 50, window=31)
    assert r["days"] == 31 and r["strained_days"] == 31


def test_cumulative_stress_empty():
    assert cumulative_stress([])["available"] is False
