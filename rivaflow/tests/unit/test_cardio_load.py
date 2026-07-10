"""Wave 3.2 — Banister-TRIMP cardio load (pure; no DB, no network).

Fixtures model two synthetic all-day HR streams (a quiet rest day, and a rest day plus a 90-minute hard
BJJ session) at a fixed max_hr/rest_hr, used both to pin the 0-21 display band (scale_to_21) and to
exercise the raw TRIMP math (banister_trimp/session_load) directly. `test_scale_to_21_*` are the pins the
module's _SCALE_A/_SCALE_B were fit against — if those constants ever change, these are the tests that
should catch it.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import rivaflow.core.cardio_load as cl
from rivaflow.core import whoop_analytics
from rivaflow.core.cardio_load import (
    banister_trimp,
    classify_hardness,
    hardness_cutoffs,
    scale_to_21,
    session_load,
)
from rivaflow.db.repositories.whoop_repo import WhoopRepository

MAX_HR = 180.0
REST_HR = 55.0
HRR = MAX_HR - REST_HR


# ── Synthetic fixtures ────────────────────────────────────────────────────────


def _rest_day_samples(
    start: datetime = datetime(2026, 1, 1, 6, 0, 0), hours: int = 14, step_sec: int = 5
) -> list[tuple[datetime, int]]:
    """~14h wear: baseline sinusoid 55-75bpm, two 15-min 'errand' blocks at ~90-110bpm."""
    out = []
    n = int(hours * 3600 / step_sec)
    for i in range(n):
        t = start + timedelta(seconds=i * step_sec)
        minutes = i * step_sec / 60.0
        bpm = 65 + 8 * math.sin(minutes / 37.0)
        if 180 <= minutes < 195 or 420 <= minutes < 450:
            bpm = 100 + 8 * math.sin(minutes / 3.0)
        out.append((t, round(bpm)))
    return out


def _bjj_hard_block(
    start: datetime, minutes: int = 90, step_sec: int = 2
) -> list[tuple[datetime, int]]:
    """90min oscillating between 75% and 92% HRR (~6min round+rest period) — a hard BJJ session."""
    out = []
    n = int(minutes * 60 / step_sec)
    for i in range(n):
        t = start + timedelta(seconds=i * step_sec)
        m = i * step_sec / 60.0
        frac = 0.5 * (1 - math.cos(2 * math.pi * m / 6.0))
        pct_hrr = 0.75 + frac * (0.92 - 0.75)
        bpm = REST_HR + pct_hrr * HRR
        out.append((t, round(bpm)))
    return out


def _hard_day_samples() -> list[tuple[datetime, int]]:
    """A rest day immediately followed by a 90min hard BJJ session."""
    rest = _rest_day_samples()
    hard = _bjj_hard_block(rest[-1][0] + timedelta(seconds=5))
    return rest + hard


# ── scale_to_21 band pins ──────────────────────────────────────────────────────


def test_scale_to_21_rest_day_lands_in_light_band():
    raw = banister_trimp(_rest_day_samples(), MAX_HR, REST_HR)
    scaled = scale_to_21(raw)
    assert 7.0 <= scaled <= 9.0


def test_scale_to_21_hard_bjj_day_lands_in_hard_band():
    raw = banister_trimp(_hard_day_samples(), MAX_HR, REST_HR)
    scaled = scale_to_21(raw)
    assert 15.0 <= scaled <= 17.0


def test_scale_to_21_never_exceeds_21():
    huge = [(datetime(2026, 1, 1) + timedelta(seconds=i), 179) for i in range(20000)]
    raw = banister_trimp(huge, MAX_HR, REST_HR)
    assert scale_to_21(raw) <= 21.0


# ── gap-clamp behaviour ─────────────────────────────────────────────────────────


def test_gap_clamp_bounds_a_long_dropout():
    """A 2h capture dropout must add no more than the 10s-worth of load the clamp allows — not the full
    2h of implied duration."""
    samples = [
        (datetime(2026, 1, 1, 6, 0, 0), 70),
        (datetime(2026, 1, 1, 8, 0, 0), 70),  # 2h later
    ]
    raw = banister_trimp(samples, MAX_HR, REST_HR)
    x = (70 - REST_HR) / HRR
    max_allowed = (10.0 / 60.0) * x * 0.64 * math.exp(1.92 * x)
    assert raw == max_allowed


def test_gap_clamp_short_gap_is_uncapped():
    """A normal <=10s gap contributes its actual duration, not the clamp ceiling."""
    samples = [
        (datetime(2026, 1, 1, 6, 0, 0), 70),
        (datetime(2026, 1, 1, 6, 0, 3), 70),  # 3s later
    ]
    raw = banister_trimp(samples, MAX_HR, REST_HR)
    x = (70 - REST_HR) / HRR
    expected = (3.0 / 60.0) * x * 0.64 * math.exp(1.92 * x)
    assert math.isclose(raw, expected, rel_tol=1e-9)


# ── monotonicity ────────────────────────────────────────────────────────────────


def test_more_time_at_higher_hrr_yields_more_load():
    low = [(datetime(2026, 1, 1) + timedelta(seconds=i), 100) for i in range(600)]
    high = [(datetime(2026, 1, 1) + timedelta(seconds=i), 160) for i in range(600)]
    assert banister_trimp(high, MAX_HR, REST_HR) > banister_trimp(low, MAX_HR, REST_HR)


def test_more_duration_at_same_intensity_yields_more_load():
    short = [(datetime(2026, 1, 1) + timedelta(seconds=i), 150) for i in range(300)]
    long_ = [(datetime(2026, 1, 1) + timedelta(seconds=i), 150) for i in range(600)]
    assert banister_trimp(long_, MAX_HR, REST_HR) > banister_trimp(
        short, MAX_HR, REST_HR
    )


# ── degenerate inputs ───────────────────────────────────────────────────────────


def test_empty_samples_is_zero():
    assert banister_trimp([], MAX_HR, REST_HR) == 0.0
    assert session_load([], MAX_HR, REST_HR) == 0.0


def test_max_hr_at_or_below_rest_hr_is_zero():
    samples = [(datetime(2026, 1, 1) + timedelta(seconds=i), 150) for i in range(100)]
    assert banister_trimp(samples, rest_hr=100.0, max_hr=100.0) == 0.0
    assert banister_trimp(samples, rest_hr=100.0, max_hr=90.0) == 0.0


def test_session_load_matches_banister_trimp():
    samples = _bjj_hard_block(datetime(2026, 1, 1, 18, 0, 0))
    assert session_load(samples, MAX_HR, REST_HR) == banister_trimp(
        samples, MAX_HR, REST_HR
    )


# ── hardness cutoffs + classification ────────────────────────────────────────────


def test_hardness_cutoffs_fallback_below_eight_samples():
    loads = [10.0, 20.0, 30.0]
    assert hardness_cutoffs(loads) == (
        cl._FALLBACK_MODERATE_CUTOFF,
        cl._FALLBACK_HARD_CUTOFF,
    )


def test_hardness_cutoffs_percentile_path_at_eight_samples():
    loads = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    moderate, hard = hardness_cutoffs(loads)
    assert (moderate, hard) != (cl._FALLBACK_MODERATE_CUTOFF, cl._FALLBACK_HARD_CUTOFF)
    assert moderate == cl._percentile(loads, 40)
    assert hard == cl._percentile(loads, 75)
    assert moderate < hard


def test_classify_hardness_labels():
    cutoffs = (10.0, 20.0)
    assert classify_hardness(25.0, cutoffs) == "HARD"
    assert classify_hardness(20.0, cutoffs) == "HARD"  # boundary is inclusive
    assert classify_hardness(15.0, cutoffs) == "MODERATE"
    assert classify_hardness(10.0, cutoffs) == "MODERATE"  # boundary is inclusive
    assert classify_hardness(5.0, cutoffs) == "EASY"


def test_classify_hardness_matches_fallback_hard_fixture():
    """The synthetic hard-BJJ session the fallback HARD_CUTOFF was anchored on must itself classify HARD."""
    samples = _bjj_hard_block(datetime(2026, 1, 1, 18, 0, 0))
    raw = session_load(samples, MAX_HR, REST_HR)
    cutoffs = hardness_cutoffs([])  # <8 -> fallback
    assert classify_hardness(raw, cutoffs) == "HARD"


# ── load_version threaded through daily_cardio_load ──────────────────────────────


def test_daily_cardio_load_carries_load_version(monkeypatch):
    rows = [{"ts": t.isoformat(), "bpm": bpm} for t, bpm in _rest_day_samples()]
    monkeypatch.setattr(
        WhoopRepository, "recent_hr", staticmethod(lambda *a, **k: rows)
    )
    out = whoop_analytics.daily_cardio_load(1, days=1, max_hr=180)
    assert out, "expected at least one day of cardio load"
    for day in out:
        assert day["load_version"] == cl.LOAD_VERSION
        assert "cardio_load" in day
        assert "raw_trimp" in day
