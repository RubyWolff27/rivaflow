"""Wave 3.1 — personalised sleep-window threshold (pure; no DB, no network).

Pins `sleep_window.personal_threshold_offset` (the pure Otsu-based learner — synthetic
bimodal/unimodal nights, thin-coverage nights, too-few-nights, and clamping). The
`_sleep_from_points` reference tests left with whoop_analytics in v2 Wave 1c.
"""

from __future__ import annotations

import random

import rivaflow.core.sleep_window as sw

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
