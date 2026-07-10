"""B5 — Strain-policy fitting: measured dose-response (Wave 3.3).

``fit_strain_multipliers`` estimates a per-readiness-state StrainPolicy from THIS athlete's own history,
replacing the STATE_MULTIPLIER heuristic in strain_target.py with a measured answer to "how much load
(relative to chronic load) can this state absorb before next-day HRV is suppressed?" For each day at a
given state, the load/chronic ratio and the following day's lnRMSSD delta (vs a trailing baseline) form
one dose-response sample; a least-squares fit per state finds the ratio at which the fitted delta crosses
zero — the "recoverable dose" — and that ratio becomes the state's multiplier.

NOT auto-applied. ``prescribe_strain`` keeps using the heuristic ``StrainPolicy`` until
``apply_env_strain_policy`` is called with ``WHOOP_STRAIN_POLICY=fitted`` in the environment (see its
docstring). Per the red-team doctrine (WHOOP_FUTURE_STATE_PLAN.md): a week of data must not silently steer
training prescriptions.

Kept out of strain_target.py — which stays pure and DB-free like readiness.py — because this module reaches
into whoop_daily_agg for real history. ``_fit_multipliers_from_samples`` is the pure regression core (no DB,
no readiness fusion): it's the unit-test seam, fed either real samples assembled by ``fit_strain_multipliers``
or a synthetic fixture.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping
from datetime import date, timedelta
from typing import Any

from rivaflow.core.readiness import blend_readiness, zscore
from rivaflow.core.strain_target import (
    STATE_MULTIPLIER,
    STRAIN_CAP,
    StrainPolicy,
    get_strain_policy,
    set_strain_policy,
)

logger = logging.getLogger(__name__)

FIT_VERSION = "strain-fitted-v1"
MIN_STATE_DAYS = (
    8  # below this many qualifying days for a state, keep the heuristic value
)
MULT_CLAMP = (
    0.2,
    1.5,
)  # sane band a fitted multiplier is clamped into (see prescribe_strain's cap too)
CHRONIC_WINDOW = 7  # trailing days averaged for both the load ratio's denominator and the lnRMSSD baseline
MIN_CHRONIC_DAYS = 3  # mirrors whoop_analytics._chronic_load's own floor before a chronic estimate counts
_BAND_WIDTH_DEFAULT = (
    2.0  # kept in sync with strain_target.BAND_WIDTH; avoids a mutable-global read here
)

ENV_FLAG = "WHOOP_STRAIN_POLICY"


def _ols_zero_crossing(pairs: list[tuple[float, float]]) -> tuple[float | None, float]:
    """OLS regression of next-day lnRMSSD delta (y) on load/chronic ratio (x); returns
    ``(x where the fitted line crosses y=0, r-squared)``. The crossing is ``None`` when the fit is
    degenerate — every x identical (no slope is determinable) or the fitted slope is exactly zero (the
    line never crosses zero)."""
    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return None, 0.0
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    if ss_tot == 0:
        r2 = 1.0 if slope == 0 else 0.0
    else:
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in pairs)
        r2 = max(0.0, 1.0 - ss_res / ss_tot)

    if slope == 0:
        return None, r2
    return -intercept / slope, r2


def _fit_multipliers_from_samples(
    samples: dict[str, list[tuple[float, float]]],
    *,
    min_days: int = MIN_STATE_DAYS,
    clamp: tuple[float, float] = MULT_CLAMP,
    cap: float = STRAIN_CAP,
    band_width: float = _BAND_WIDTH_DEFAULT,
) -> tuple[StrainPolicy, dict[str, dict[str, Any]]]:
    """Pure regression core — DB-free, the unit-test seam. ``samples`` maps readiness state -> list of
    ``(load_ratio, next_day_ln_rmssd_delta)`` pairs, already assembled by ``fit_strain_multipliers`` (real
    data) or a test fixture (synthetic). Returns the fitted ``StrainPolicy`` — falling back to the
    heuristic multiplier for any state with too little data or a degenerate fit — plus a per-state report.
    """
    multipliers = dict(STATE_MULTIPLIER)
    report: dict[str, dict[str, Any]] = {}

    for state, heuristic_mult in STATE_MULTIPLIER.items():
        pairs = samples.get(state, [])
        n = len(pairs)
        if n < min_days:
            report[state] = {
                "n": n,
                "fitted": None,
                "used": heuristic_mult,
                "r2": None,
                "reason": "insufficient_data",
            }
            continue

        crossing, r2 = _ols_zero_crossing(pairs)
        if crossing is None:
            report[state] = {
                "n": n,
                "fitted": None,
                "used": heuristic_mult,
                "r2": round(r2, 3),
                "reason": "degenerate_fit",
            }
            continue

        clamped = round(max(clamp[0], min(clamp[1], crossing)), 3)
        multipliers[state] = clamped
        report[state] = {
            "n": n,
            "fitted": round(crossing, 3),
            "used": clamped,
            "r2": round(r2, 3),
            "reason": "fitted",
        }

    policy = StrainPolicy(
        version=FIT_VERSION, multipliers=multipliers, cap=cap, band_width=band_width
    )
    return policy, report


def _next_calendar_day(day: str) -> str:
    return (date.fromisoformat(day) + timedelta(days=1)).isoformat()


def _assemble_samples(
    rmssd_days: list[dict[str, Any]], cardio_days: list[dict[str, Any]]
) -> dict[str, list[tuple[float, float]]]:
    """Walk the overlapping (day, ln_rmssd) / (day, cardio_load) history and build per-state
    ``(load_ratio, next_day_delta)`` pairs.

    ``load_ratio`` = day i's cardio load / the trailing CHRONIC_WINDOW-day mean load (excluding day i,
    needs >= MIN_CHRONIC_DAYS prior days — mirrors ``whoop_analytics._chronic_load``'s own floor).
    ``next_day_delta`` = day i+1's lnRMSSD minus the trailing CHRONIC_WINDOW-day mean lnRMSSD through day i
    (the pre-dose baseline) — positive means next-day HRV held or rose, negative means it was suppressed.

    State labels reuse the same HRV-led ``zscore``/``blend_readiness`` the live B2 readiness verdict runs,
    walked day-by-day so each day is scored against only the data that would have been available at the
    time (no lookahead). This is a proxy for the full multi-signal readiness state (which also weighs
    nocturnal RHR, sleep and respiratory rate) — but HRV is the required, dominant-weighted signal in that
    blend (readiness.py: WEIGHTS["hrv"] = 0.50), and it's the one series this fit needs for the dose-
    response question, so an HRV-only walk is a faithful and DB-cheap proxy for state labelling here.

    A day is only used when the NEXT calendar day is also present (no gap-spanning deltas).
    """
    ln_by_day = {d["day"]: d["ln_rmssd"] for d in rmssd_days}
    load_by_day = {d["day"]: d["cardio_load"] for d in cardio_days}
    days = sorted(set(ln_by_day) & set(load_by_day))

    samples: dict[str, list[tuple[float, float]]] = {s: [] for s in STATE_MULTIPLIER}
    ln_series: list[float] = []
    for idx, day in enumerate(days):
        ln_series.append(ln_by_day[day])
        z = zscore(ln_series)
        state = blend_readiness({"hrv": z["z"] if z else None}).get("state")
        if state not in STATE_MULTIPLIER:
            continue

        prior_days = days[max(0, idx - CHRONIC_WINDOW) : idx]
        if len(prior_days) < MIN_CHRONIC_DAYS:
            continue
        chronic = sum(load_by_day[d] for d in prior_days) / len(prior_days)
        if chronic <= 0:
            continue
        ratio = load_by_day[day] / chronic

        if idx + 1 >= len(days) or days[idx + 1] != _next_calendar_day(day):
            continue  # no contiguous next-day reading — a delta here would span a gap

        baseline_window = ln_series[-CHRONIC_WINDOW:]
        baseline = sum(baseline_window) / len(baseline_window)
        delta = ln_by_day[days[idx + 1]] - baseline

        samples[state].append((ratio, delta))

    return samples


def fit_strain_multipliers(user_id: int, days: int = 90) -> dict[str, Any]:
    """Measured dose-response fit for ``user_id``'s own history (see module docstring). NOT applied
    automatically — see ``apply_env_strain_policy``. Falls back to the heuristic multiplier per state where
    that state has under ``MIN_STATE_DAYS`` qualifying days or the fit is degenerate.

    Returns ``{"policy": StrainPolicy(version="strain-fitted-v1", ...), "report": {state: {...}}}``.
    """
    from rivaflow.core.whoop_analytics import daily_cardio_load, daily_resting_rmssd

    rmssd_days = daily_resting_rmssd(user_id, days=days)
    cardio_days = daily_cardio_load(user_id, days=days)
    samples = _assemble_samples(rmssd_days, cardio_days)
    policy, report = _fit_multipliers_from_samples(samples)
    return {"policy": policy, "report": report}


def apply_env_strain_policy(
    user_id: int,
    *,
    fit_fn: Callable[[int], dict[str, Any]] = fit_strain_multipliers,
    env: Mapping[str, str] | None = None,
) -> StrainPolicy:
    """Read ``WHOOP_STRAIN_POLICY`` from ``env`` (defaults to ``os.environ``) and, when it equals
    ``"fitted"``, swap the active strain policy to ``fit_fn(user_id)``'s result via ``set_strain_policy``.
    Any other value — including unset — leaves the heuristic default in place untouched. Intended to be
    called once, on startup or before the day's first ``prescribe_strain`` call, by the wiring layer.

    A failure inside ``fit_fn`` (sparse data, a DB hiccup, whatever) is caught and logged, never raised —
    the active policy is left as it was (heuristic, if it was never swapped). Per the red-team doctrine: a
    bad fit must never crash the prescription path, and a week of data must never silently steer training.

    ``fit_fn`` is the injection seam unit tests use to swap in a fake fit instead of touching the DB.
    """
    active_env = os.environ if env is None else env
    if active_env.get(ENV_FLAG) != "fitted":
        return get_strain_policy()

    try:
        result = fit_fn(user_id)
        set_strain_policy(result["policy"])
    except Exception:
        logger.exception(
            "WHOOP_STRAIN_POLICY=fitted fit failed for user %s — keeping the current strain policy",
            user_id,
        )
    return get_strain_policy()
