"""Personalised sleep-window threshold (Wave 3.1) — learns each user's own asleep/awake HR separation
instead of assuming a fixed +12bpm band above the night's quietest bucket.

The fixed +12 (whoop_analytics._sleep_from_points, pre-Wave-3.1) was a GUESS: some people's nocturnal HR
dip is wider or narrower than others', and a bad threshold clips onset/offset or bridges awake time as
sleep. This module learns the offset from the user's OWN recent nights via a 2-class (Otsu) split of each
night's 5-min bucket-median histogram, aggregated across nights with the median — falling back to the
fixed floor when there isn't enough usable history.

Stdlib only (no numpy/scipy). Kept pure/testable: `personal_threshold_offset` takes precomputed (or
lazily-produced) per-night bucket-median dicts, not a user_id — the DB-backed wrapper is
`personal_threshold_for_user`. No import of whoop_analytics (which imports this module for `bucket_hr` and
the threshold) — avoids a cycle.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timedelta
from statistics import median, pvariance
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

FLOOR_VERSION = "sleep-min12-v0"
LEARNED_VERSION = "sleep-learned-v1"

MIN_NIGHTS = 14  # usable nights (adequate coverage + non-degenerate split) required to trust a learned offset
MIN_BUCKETS_PER_NIGHT = (
    60  # ~5h of 5-min buckets — the coverage floor for one night to count
)
OFFSET_MIN, OFFSET_MAX = (
    8.0,
    20.0,
)  # sane clamp band for a learned asleep-band offset (bpm)

# Otsu's between-class variance, normalized by the night's total variance (η). A genuinely bimodal night
# (real asleep/awake modes) separates cleanly and scores high; a single-mode (unimodal) night's "best"
# split is still whatever Otsu finds, but explains much less of the total spread — reject it as degenerate.
_OTSU_MIN_SEPARABILITY = 0.8

_LOOKBACK_NIGHTS = (
    30  # nights of raw HR the DB-backed wrapper scans to feed the learner
)
_THRESHOLD_CACHE_TTL_SEC = (
    6 * 60 * 60
)  # ~6h/process — the learner scans 30 nights of HR; mirrors
# whoop_profile's per-process TTL cache pattern (see core/whoop_profile.py) rather than recomputing per call.

_threshold_cache: dict[int, tuple[float, str, float]] = {}


def _clear_threshold_cache() -> None:
    """Test hook — reset the per-process learned-threshold cache between test cases."""
    _threshold_cache.clear()


def bucket_hr(
    pts: list[tuple[datetime, int]],
) -> tuple[dict[int, int], dict[int, datetime], dict[int, list[int]]]:
    """5-min-bucket bpm medians + each bucket's first-sample timestamp + each bucket's raw bpm list, from
    (ts, bpm) points (need not be pre-sorted). Shared by the sleep-window detector
    (whoop_analytics._sleep_from_points) and the personal-threshold learner below — the ONE place this
    bucketing math lives.
    """
    if not pts:
        return {}, {}, {}
    ordered = sorted(pts, key=lambda p: p[0])
    t0 = ordered[0][0]
    bucket_bpms: dict[int, list[int]] = defaultdict(list)
    bucket_time: dict[int, datetime] = {}
    for t, b in ordered:
        idx = int((t - t0).total_seconds() // 300)  # 5-minute bucket
        bucket_bpms[idx].append(b)
        bucket_time.setdefault(idx, t)
    med = {i: sorted(vs)[len(vs) // 2] for i, vs in bucket_bpms.items()}
    return med, bucket_time, dict(bucket_bpms)


def _otsu_split(values: list[int]) -> int | None:
    """Otsu's method over one night's bucket-median histogram: the integer bpm threshold splitting
    `values` into an 'asleep' low class and an 'awake/evening' high class by maximizing between-class
    variance. Returns None when the night is degenerate — too few samples, too narrow a range, or
    genuinely unimodal (see _OTSU_MIN_SEPARABILITY) — a lone-mode night's own noise, not two real
    populations.
    """
    if len(values) < 20:
        return None
    lo, hi = min(values), max(values)
    if hi - lo < 6:
        return None
    total_var = pvariance(values)
    if total_var <= 0:
        return None

    hist = [0] * (hi - lo + 1)
    for v in values:
        hist[v - lo] += 1
    total = len(values)
    total_sum = sum((i + lo) * c for i, c in enumerate(hist))

    weight_bg = 0
    sum_bg = 0.0
    best_between = -1.0
    best_t: int | None = None
    for i, c in enumerate(
        hist[:-1]
    ):  # threshold sits between bucket i and i+1; can't split above the top
        weight_bg += c
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += (i + lo) * c
        mean_bg = sum_bg / weight_bg
        mean_fg = (total_sum - sum_bg) / weight_fg
        between = (weight_bg / total) * (weight_fg / total) * (mean_bg - mean_fg) ** 2
        if between > best_between:
            best_between = between
            best_t = i + lo

    if best_t is None or best_between / total_var < _OTSU_MIN_SEPARABILITY:
        return None
    low_n = sum(c for i, c in enumerate(hist) if i + lo <= best_t)
    if low_n < total * 0.1 or (total - low_n) < total * 0.1:
        return None
    return best_t


def personal_threshold_offset(
    nightly_offsets_source: Callable[[], list[dict[int, int]]] | list[dict[int, int]],
) -> tuple[float, str]:
    """Learn the user's asleep-band offset from their own nights (stdlib only — no numpy/scipy).

    For each night with adequate HR coverage (>=MIN_BUCKETS_PER_NIGHT present bucket medians), split that
    night's bucket-median histogram into an asleep/low class and an awake-evening/high class via Otsu's
    method (see _otsu_split); that night's implied offset is the split point minus the night's OWN minimum
    bucket median. Aggregate across usable nights with the MEDIAN (robust to one off night), clamped to
    [OFFSET_MIN, OFFSET_MAX]. With fewer than MIN_NIGHTS usable nights (thin history, or every night's
    distribution too degenerate to split), falls back to the fixed floor offset (12.0).

    `nightly_offsets_source` is a callable or a precomputed list of per-night {bucket_idx: median_bpm}
    dicts (see bucket_hr) — kept as an argument rather than a DB call so this stays pure and unit-testable;
    the DB-backed wrapper is personal_threshold_for_user below.
    """
    nights = (
        nightly_offsets_source()
        if callable(nightly_offsets_source)
        else nightly_offsets_source
    )
    offsets: list[float] = []
    for night in nights:
        if len(night) < MIN_BUCKETS_PER_NIGHT:
            continue
        values = list(night.values())
        split = _otsu_split(values)
        if split is None:
            continue
        offsets.append(float(split - min(values)))
    if len(offsets) < MIN_NIGHTS:
        return 12.0, FLOOR_VERSION
    offset = max(OFFSET_MIN, min(OFFSET_MAX, median(offsets)))
    return offset, LEARNED_VERSION


def _parse_ts(ts: str) -> datetime:
    """Parse a stored ISO timestamp (handles trailing Z). Local copy of whoop_analytics._parse_ts — kept
    here rather than imported so this module has no import-time dependency on whoop_analytics, which
    imports this module (avoids a cycle)."""
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=ZoneInfo("UTC"))


def _night_bucket_medians(user_id: int, day: date, tz: ZoneInfo) -> dict[int, int]:
    """One night's (18:00 `day` -> 12:00 next day, local) 5-min bucket bpm medians — the same night window
    whoop_analytics._day_sleep uses. Reads raw HR only, never a stored sleep output: the learner cannot
    create a feedback loop through the rollups it feeds, even when a given night's own sleep was (or still
    is) computed using the FLOOR threshold — the learner reads the raw HR stream directly, not that result.
    """
    from rivaflow.db.repositories.whoop_repo import WhoopRepository

    start = datetime.combine(day, datetime.min.time(), tz).replace(hour=18)
    end = start + timedelta(
        hours=18
    )  # 18:00 -> next 12:00, matching _day_sleep's night window
    hr = WhoopRepository.hr_range(user_id, start.isoformat(), end.isoformat())
    pts = [
        (_parse_ts(str(h["ts"])), int(h["bpm"]))
        for h in hr
        if h.get("bpm") and h.get("ts")
    ]
    if not pts:
        return {}
    med, _, _ = bucket_hr(pts)
    return med


def personal_threshold_for_user(user_id: int) -> tuple[float, str]:
    """DB-backed personal_threshold_offset: the user's last ~30 nights of raw HR, bucketed via bucket_hr,
    fed to the pure learner above. Cached per-process (~6h TTL — see _THRESHOLD_CACHE_TTL_SEC) since the
    learner scans 30 nights of HR on every call otherwise. Never raises: any DB/lookup failure falls back
    to the fixed floor, same contract as whoop_profile.get_whoop_profile.
    """
    cached = _threshold_cache.get(user_id)
    now = time.monotonic()
    if cached is not None and now - cached[2] < _THRESHOLD_CACHE_TTL_SEC:
        return cached[0], cached[1]

    try:
        from rivaflow.core.whoop_profile import get_whoop_profile

        profile = get_whoop_profile(user_id)
        today = datetime.now(profile.tz).date()
        nights = [
            _night_bucket_medians(user_id, today - timedelta(days=n), profile.tz)
            for n in range(1, _LOOKBACK_NIGHTS + 1)
        ]
        offset, version = personal_threshold_offset(nights)
    except Exception:  # noqa: BLE001 — the learner must never break sleep detection
        logger.warning(
            "personal_threshold_for_user failed for user %s; using floor",
            user_id,
            exc_info=True,
        )
        offset, version = 12.0, FLOOR_VERSION

    _threshold_cache[user_id] = (offset, version, now)
    return offset, version
