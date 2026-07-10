"""Wave 3.1 — personalised sleep-window threshold (pure; no DB, no network).

Two things are pinned here: `sleep_window.personal_threshold_offset` (the pure Otsu-based learner —
synthetic bimodal/unimodal nights, thin-coverage nights, too-few-nights, and clamping) and
`whoop_analytics._sleep_from_points` (that the FLOOR default path is byte-identical to the pre-Wave-3.1
fixed +12bpm behaviour, and that both paths now carry a detector_version).
"""

from __future__ import annotations

import random
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean

import rivaflow.core.sleep_window as sw
from rivaflow.core import whoop_analytics

# ── Synthetic per-night bucket-median fixtures ──────────────────────────────────


def _bimodal_night(
    seed: int,
    asleep_mean: float = 52,
    asleep_sd: float = 3,
    awake_mean: float = 68,
    awake_sd: float = 5,
    asleep_buckets: int = 96,
    awake_buckets: int = 24,
) -> dict[int, int]:
    """One synthetic night's bucket-median dict: evening-awake, then asleep, then morning-awake — a real
    night's two-population shape, without needing to synthesize raw HR points."""
    rng = random.Random(seed)
    values: dict[int, int] = {}
    idx = 0
    for _ in range(awake_buckets):
        values[idx] = round(rng.gauss(awake_mean, awake_sd))
        idx += 1
    for _ in range(asleep_buckets):
        values[idx] = round(rng.gauss(asleep_mean, asleep_sd))
        idx += 1
    for _ in range(awake_buckets):
        values[idx] = round(rng.gauss(awake_mean, awake_sd))
        idx += 1
    return values


def _unimodal_night(
    seed: int, mean_bpm: float = 60, sd: float = 4, buckets: int = 144
) -> dict[int, int]:
    """One degenerate night: a single population (no real asleep/awake separation) — should be skipped."""
    rng = random.Random(seed)
    return {i: round(rng.gauss(mean_bpm, sd)) for i in range(buckets)}


# ── (a) bimodal nights -> learned offset between the modes ─────────────────────


def test_personal_threshold_offset_bimodal_nights_learns_between_modes():
    nights = [_bimodal_night(seed=i) for i in range(20)]
    offset, version = sw.personal_threshold_offset(nights)
    assert version == sw.LEARNED_VERSION
    # asleep ~52, awake ~68 -> the learned per-night (split - night_min) should land clearly between the
    # fixed floor (12) and the full mode separation (~16), not collapse to either extreme.
    assert 10.0 <= offset <= 18.0


# ── (b) <14 usable nights -> FLOOR ──────────────────────────────────────────────


def test_personal_threshold_offset_too_few_nights_falls_back_to_floor():
    nights = [_bimodal_night(seed=i) for i in range(10)]  # < MIN_NIGHTS
    offset, version = sw.personal_threshold_offset(nights)
    assert (offset, version) == (12.0, sw.FLOOR_VERSION)


# ── (c) unimodal/degenerate nights are skipped -> too few remain -> FLOOR ───────


def test_personal_threshold_offset_unimodal_nights_are_skipped():
    nights = [_unimodal_night(seed=i) for i in range(20)]
    offset, version = sw.personal_threshold_offset(nights)
    assert (offset, version) == (12.0, sw.FLOOR_VERSION)


def test_personal_threshold_offset_mixed_nights_only_bimodal_count():
    # 10 usable (bimodal) + 10 skipped (unimodal) = 10 usable, still < MIN_NIGHTS -> FLOOR.
    nights = [_bimodal_night(seed=i) for i in range(10)] + [
        _unimodal_night(seed=i) for i in range(10, 20)
    ]
    offset, version = sw.personal_threshold_offset(nights)
    assert (offset, version) == (12.0, sw.FLOOR_VERSION)


def test_personal_threshold_offset_enough_bimodal_among_unimodal_still_learns():
    # Not every bimodal fixture night clears the separability bar (sampling noise near the boundary), so
    # 24 bimodal nights (empirically ~19 usable, well over MIN_NIGHTS) plus 6 skipped unimodal nights.
    nights = [_bimodal_night(seed=i) for i in range(24)] + [
        _unimodal_night(seed=i) for i in range(24, 30)
    ]
    offset, version = sw.personal_threshold_offset(nights)
    assert version == sw.LEARNED_VERSION


def test_personal_threshold_offset_thin_coverage_nights_are_skipped():
    # Each night has far fewer than MIN_BUCKETS_PER_NIGHT present buckets -> all skipped -> FLOOR.
    nights = [dict(list(_bimodal_night(seed=i).items())[:30]) for i in range(20)]
    offset, version = sw.personal_threshold_offset(nights)
    assert (offset, version) == (12.0, sw.FLOOR_VERSION)


# ── (d) clamping to [OFFSET_MIN, OFFSET_MAX] ────────────────────────────────────


def test_personal_threshold_offset_clamps_to_max(monkeypatch):
    # Force every night's Otsu split to imply a huge offset, isolating the clamp from Otsu's own math.
    monkeypatch.setattr(sw, "_otsu_split", lambda values: min(values) + 999)
    nights = [{i: 55 for i in range(70)} for _ in range(20)]
    offset, version = sw.personal_threshold_offset(nights)
    assert offset == sw.OFFSET_MAX
    assert version == sw.LEARNED_VERSION


def test_personal_threshold_offset_clamps_to_min(monkeypatch):
    monkeypatch.setattr(sw, "_otsu_split", lambda values: min(values) + 1)
    nights = [{i: 55 for i in range(70)} for _ in range(20)]
    offset, version = sw.personal_threshold_offset(nights)
    assert offset == sw.OFFSET_MIN
    assert version == sw.LEARNED_VERSION


# ── nightly_offsets_source accepts a callable, not just a list ─────────────────


def test_personal_threshold_offset_accepts_callable_source():
    nights = [_bimodal_night(seed=i) for i in range(20)]
    offset_list, version_list = sw.personal_threshold_offset(nights)
    offset_callable, version_callable = sw.personal_threshold_offset(lambda: nights)
    assert (offset_list, version_list) == (offset_callable, version_callable)


# ── (e)/(f) _sleep_from_points: FLOOR path is byte-identical to pre-Wave-3.1 ────


def _synthetic_night_points(seed: int = 1) -> list[tuple[datetime, int]]:
    """~12h of 1-min-sampled HR: 2h evening-awake ~70bpm, 8h asleep ~50bpm, 2h morning-awake ~70bpm — a
    clean single sleep window for _best_sleep_window to pick out."""
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, 22, 0, 0)
    pts: list[tuple[datetime, int]] = []
    t = start
    for _ in range(120):
        pts.append((t, round(rng.gauss(70, 3))))
        t += timedelta(minutes=1)
    for _ in range(480):
        pts.append((t, round(rng.gauss(50, 3))))
        t += timedelta(minutes=1)
    for _ in range(120):
        pts.append((t, round(rng.gauss(70, 3))))
        t += timedelta(minutes=1)
    return pts


def _reference_sleep_from_points(pts: list[tuple[datetime, int]]) -> dict:
    """Pinned, independently-written copy of the pre-Wave-3.1 `_sleep_from_points` body (fixed +12bpm
    threshold, inline bucketing) — an independent reference to catch any behavioural drift introduced by
    factoring the bucketing into sleep_window.bucket_hr and threading a personalised threshold through.
    """
    if len(pts) < 120:
        return {
            "available": False,
            "reason": "Not enough overnight HR captured for a sleep estimate yet.",
        }
    pts = sorted(pts, key=lambda p: p[0])
    t0 = pts[0][0]
    bucket_bpms: dict[int, list[int]] = defaultdict(list)
    bucket_time: dict[int, datetime] = {}
    for t, b in pts:
        idx = int((t - t0).total_seconds() // 300)
        bucket_bpms[idx].append(b)
        bucket_time.setdefault(idx, t)
    order = sorted(bucket_bpms)
    med = {i: sorted(bucket_bpms[i])[len(bucket_bpms[i]) // 2] for i in order}
    threshold = min(med.values()) + 12
    win = whoop_analytics._best_sleep_window(med, threshold)
    if win is None:
        return {
            "available": False,
            "reason": "No sustained overnight low-HR sleep window detected.",
        }
    s_idx, e_idx, low_count = win
    start_t, end_t = bucket_time[s_idx], bucket_time[e_idx]
    duration_hours = (end_t - start_t).total_seconds() / 3600
    span_buckets = e_idx - s_idx + 1
    coverage_pct = round(100 * low_count / span_buckets) if span_buckets else 0
    fragmented = coverage_pct < 60
    sleep_bpms = [
        b
        for i in order
        if s_idx <= i <= e_idx and med[i] <= threshold
        for b in bucket_bpms[i]
    ]
    return {
        "available": True,
        "sleep_start": start_t.isoformat(),
        "sleep_end": end_t.isoformat(),
        "duration_hours": round(duration_hours, 1),
        "avg_sleeping_hr": round(mean(sleep_bpms)) if sleep_bpms else None,
        "min_hr": min(sleep_bpms) if sleep_bpms else None,
        "coverage_pct": coverage_pct,
        "fragmented": fragmented,
        "source": "hr_bucketed_window",
        "method": "HR-based sleep window (bridges capture gaps, breaks on sustained wake; not staging).",
    }


def test_sleep_from_points_floor_default_matches_pre_wave31_reference():
    pts = _synthetic_night_points()
    got = whoop_analytics._sleep_from_points(list(pts))
    expected = _reference_sleep_from_points(list(pts))
    got_without_version = {k: v for k, v in got.items() if k != "detector_version"}
    assert got["available"] is True  # sanity: fixture actually detects a window
    assert got_without_version == expected


def test_sleep_from_points_short_circuit_matches_reference():
    pts = _synthetic_night_points()[
        :100
    ]  # < 120 points -> the early "not enough HR" branch
    got = whoop_analytics._sleep_from_points(list(pts))
    expected = _reference_sleep_from_points(list(pts))
    assert got == expected  # no detector_version on the unavailable short-circuit


def test_sleep_from_points_floor_path_carries_floor_detector_version():
    pts = _synthetic_night_points()
    got = whoop_analytics._sleep_from_points(list(pts))
    assert got["detector_version"] == sw.FLOOR_VERSION


def test_sleep_from_points_learned_path_carries_learned_detector_version():
    pts = _synthetic_night_points()
    got = whoop_analytics._sleep_from_points(
        list(pts), threshold_offset=15.0, detector_version=sw.LEARNED_VERSION
    )
    assert got["available"] is True
    assert got["detector_version"] == sw.LEARNED_VERSION


def test_sleep_from_points_different_offset_changes_shape_not_keys():
    pts = _synthetic_night_points()
    floor = whoop_analytics._sleep_from_points(list(pts))
    learned = whoop_analytics._sleep_from_points(
        list(pts), threshold_offset=15.0, detector_version=sw.LEARNED_VERSION
    )
    assert set(floor) == set(learned)  # additive-only: same output shape on both paths
