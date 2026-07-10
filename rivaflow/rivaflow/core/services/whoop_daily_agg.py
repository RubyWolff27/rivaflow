"""whoop_daily_agg — append-only per-day rollup service (Wave 3.4).

whoop_summary() re-scanned weeks of raw whoop_hr/whoop_rr on EVERY call — each of daily_resting_rmssd,
daily_resting_hr, nightly_sleep_history, and daily_cardio_load independently fetched and re-derived its
full N-day window's HRV/resting-HR/sleep/cardio-load every time, and compute_readiness + prevention_watch
each call several of them again over their own (overlapping) windows. A day's true value never changes
once the day is over — except the phone's offline spool and historical drains can land whoop_hr/whoop_rr
rows for a day DAYS after it first looked complete, so "over" isn't quite "never changes again" either.

This module is the fix: compute_day() derives ONE day's full metrics set straight from raw, reusing the
exact per-day math already in whoop_analytics (_day_rmssd / _day_resting_hr / _day_sleep / _day_cardio —
the ONE place that math lives, no duplication here). get_range() is what whoop_analytics' four series
functions now call: serve a historical day from whoop_daily_agg when it's fresh, recompute + persist it
when it's missing, on a deriver-version bump, or when its raw HR+RR count has grown since it was rolled up
(the late-data case) — and always compute TODAY live, never persisted, since it's still accruing.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from rivaflow.core import whoop_analytics
from rivaflow.core.cardio_load import LOAD_VERSION
from rivaflow.core.whoop_profile import get_whoop_profile
from rivaflow.db.repositories.whoop_repo import WhoopRepository

logger = logging.getLogger(__name__)

# Bumps whenever compute_day's math changes — directly, or transitively via cardio_load.LOAD_VERSION (a
# load-math upgrade must invalidate every stored cardio rollup too). A version mismatch on a stored row
# forces a recompute, same idea as whoop_cockpit's deriver_version (see whoop_analytics.build_cockpit_snapshot).
DERIVER_VERSION = f"daily-agg-v1+{LOAD_VERSION}"

# Cold-start / off-wrist fallback rest-HR for a day whose own resting-HR reading isn't available — mirrors
# whoop_analytics._DEFAULT_REST_HR. compute_day is deliberately day-isolated (a persisted rollup can't
# depend on which window size some future caller happens to ask for), so unlike the pre-Wave-3.4
# daily_cardio_load it does NOT borrow a neighbouring day's resting-HR; see compute_day's docstring.
_DEFAULT_REST_HR = 60.0

_METRIC_KEYS = ("rmssd", "resting_hr", "sleep", "cardio")


def _day_bounds_iso(day: str, tz) -> tuple[str, str]:
    """[start, end] ISO bounds (inclusive) for `day`'s local calendar window [00:00, 24:00) — the shared
    window definition compute_day and the raw-count staleness check both use."""
    d = date.fromisoformat(day)
    start = datetime.combine(d, datetime.min.time(), tz)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return start.isoformat(), end.isoformat()


def compute_day(user_id: int, day: str, *, max_hr: float | None = None) -> dict:
    """One local calendar day's full rollup, straight from raw whoop_hr/whoop_rr — the expensive path
    get_range() below calls ONCE per (missing or stale) day and then persists, instead of every series
    function re-deriving it on every call. Reuses the per-day math whoop_analytics already has
    (_day_rmssd / _day_resting_hr / _day_sleep / _day_cardio) — no duplicated math.

    `sample_count` = whoop_hr rows + whoop_rr rows in `day`'s local calendar window [00:00, 24:00) — the
    staleness signal get_range() uses to catch late-arriving data (the phone's offline spool / a
    historical drain can land rows for a day well after it first looked complete). Sleep's OWN window
    (18:00 `day` -> 12:00 the next day) straddles into the next calendar day, so a late row landing after
    midnight bumps the NEXT day's sample_count rather than this one's — an accepted approximation; the
    next day's own rollup gets re-checked on its own account regardless, so the same late-arriving event
    is never silently lost, just occasionally attributed to the neighbouring day's recheck instead.

    cardio's rest_hr uses THIS day's own resting-HR reading when available, else _DEFAULT_REST_HR — a
    day-isolated rule, not the multi-day "borrow the nearest prior day within the caller's window" rule
    the pre-Wave-3.4 daily_cardio_load used (whoop_analytics._rest_hr_lookup), since a persisted rollup
    can't depend on a future caller's window size. This only differs from the old behaviour on a day that
    itself has <60 resting-HR samples (rare — continuous wear).

    `max_hr` defaults to the cheap whoop_analytics.MAX_HR fallback (not a fresh calibration scan) so a
    standalone call — or an incidental cardio sub-computation triggered by an rmssd/resting_hr/sleep
    request — never surprises the caller with an expensive 90-day HR scan; get_range() overrides this with
    the real calibrated value specifically when the caller asked for the "cardio" metric itself.
    """
    profile = get_whoop_profile(user_id)
    tz = profile.tz
    d = date.fromisoformat(day)
    start = datetime.combine(d, datetime.min.time(), tz)
    end = start + timedelta(days=1) - timedelta(microseconds=1)

    hr_rows = WhoopRepository.hr_range(user_id, start.isoformat(), end.isoformat())
    rr_rows = WhoopRepository.rr_range_between(
        user_id, start.isoformat(), end.isoformat()
    )
    bpms = [int(h["bpm"]) for h in hr_rows if h.get("bpm")]
    rr_vals = [int(r["rr_ms"]) for r in rr_rows if r.get("rr_ms")]

    rmssd_metric = whoop_analytics._day_rmssd(rr_vals, len(bpms))
    resting_hr_metric = whoop_analytics._day_resting_hr(bpms)
    sleep_metric = whoop_analytics._day_sleep(user_id, d, tz)

    mx = max_hr if max_hr is not None else whoop_analytics.MAX_HR
    rest_hr = (
        float(resting_hr_metric["resting_hr"])
        if resting_hr_metric
        else _DEFAULT_REST_HR
    )
    samples = sorted(
        (
            (whoop_analytics._parse_ts(str(h["ts"])), int(h["bpm"]))
            for h in hr_rows
            if h.get("bpm")
        ),
        key=lambda p: p[0],
    )
    cardio_metric = whoop_analytics._day_cardio(samples, mx, rest_hr)

    metrics: dict = {
        "day": day,
        "rmssd": rmssd_metric,
        "resting_hr": resting_hr_metric,
        "sleep": sleep_metric,
        "cardio": cardio_metric,
    }
    metrics["sample_count"] = len(hr_rows) + len(rr_rows)
    metrics["complete"] = all(metrics[k] is not None for k in _METRIC_KEYS)
    return metrics


def _rollup_for_day(user_id: int, day: str, tz, *, max_hr: float | None) -> dict | None:
    """Serve `day` from whoop_daily_agg when it's fresh (deriver version AND raw count both match); else
    recompute + upsert. The count check is two cheap COUNT(*) queries (index range scan, no row
    materialization) — this is what catches the late-arriving-data case (see compute_day's docstring). A
    day whose window has never captured anything (count 0) returns None WITHOUT writing a row — matches
    the pre-rollup series functions, where a day with no data just never appears in the output.
    """
    start_iso, end_iso = _day_bounds_iso(day, tz)
    current_count = WhoopRepository.hr_count_range(
        user_id, start_iso, end_iso
    ) + WhoopRepository.rr_count_range(user_id, start_iso, end_iso)

    stored = WhoopRepository.get_daily_agg(user_id, day)
    if (
        stored is not None
        and stored.get("deriver_version") == DERIVER_VERSION
        and int(stored.get("sample_count") or 0) == current_count
    ):
        cached: dict = json.loads(stored["metrics_json"])
        return cached

    if current_count == 0:
        return None

    computed = compute_day(user_id, day, max_hr=max_hr)
    WhoopRepository.upsert_daily_agg(
        user_id,
        day,
        json.dumps(computed, default=str),
        DERIVER_VERSION,
        computed["sample_count"],
        computed["complete"],
    )
    return computed


def get_range(
    user_id: int, days: int, metric: str, *, max_hr: float | None = None
) -> list[dict]:
    """The per-day series for one metric ('rmssd' | 'resting_hr' | 'sleep' | 'cardio') over the last `days`
    (for 'sleep', the last `days` NIGHTS — matching nightly_sleep_history's own convention, which never
    included the still-in-progress current night either). Historical days are served from whoop_daily_agg
    (see _rollup_for_day); TODAY (profile-local) is always computed live via compute_day and never
    persisted, since it's still accruing.

    Output shape per day matches exactly what the pre-rollup series function it replaces produced — a day
    with no captured data is simply absent, and 'sleep' entries carry no 'day' key (matching
    nightly_sleep_history's own shape; every other metric prepends {"day": ...}).
    """
    if metric not in _METRIC_KEYS:
        raise ValueError(f"unknown whoop_daily_agg metric {metric!r}")
    profile = get_whoop_profile(user_id)
    tz = profile.tz
    today = datetime.now(tz).date()

    if metric == "sleep":
        day_list = [today - timedelta(days=n) for n in range(days, 0, -1)]
    else:
        day_list = [today - timedelta(days=n) for n in range(days - 1, -1, -1)]

    # "cardio" is what daily_cardio_load itself returns — resolve the REAL calibrated max-HR (same default
    # daily_cardio_load always used) so its own values are unchanged. Any OTHER metric's request only feeds
    # compute_day's incidental cardio sub-value (nobody asked for it), so it stays cheap by default —
    # see compute_day's docstring.
    if metric == "cardio":
        mx = (
            max_hr
            if max_hr is not None
            else whoop_analytics.user_max_hr(user_id)["max_hr"]
        )
    else:
        mx = max_hr if max_hr is not None else whoop_analytics.MAX_HR

    out: list[dict] = []
    for d in day_list:
        day = d.isoformat()
        computed = (
            compute_day(user_id, day, max_hr=mx)
            if d == today
            else _rollup_for_day(user_id, day, tz, max_hr=mx)
        )
        if computed is None:
            continue
        val = computed[metric]
        if val is None:
            continue
        out.append(val if metric == "sleep" else {"day": day, **val})
    return out
