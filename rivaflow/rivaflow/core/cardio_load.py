"""Cardio load — Banister TRIMP (Wave 3.2).

The ONE place zone-weight/TRIMP math lives. Before this module, `whoop_analytics.daily_cardio_load`
and `whoop_cockpit.session_load_hardness` each carried their own ad-hoc 5-zone step-weight table
(1/2/4/8/16 per zone), and the two had already drifted apart. Both now import from here instead.

Male Banister TRIMP (Banister 1991): minutes at heart-rate-reserve intensity x = (bpm-rest)/(max-rest),
weighted by the exponential curve 0.64·e^(1.92·x) — a continuous relative-intensity weighting that
doesn't cliff at zone boundaries the way the old step table did.
"""

from __future__ import annotations

from datetime import datetime
from math import exp, log1p

LOAD_VERSION = "banister-v1"

# A capture dropout (strap off-wrist / charging) contributes at most this many seconds of load rather
# than either the full (possibly hours-long) gap or nothing — same 10s convention the pre-Wave-3.2
# daily_cardio_load used, but clamped instead of dropped so a dropout can't create a hard discontinuity
# right at the 10s boundary.
_GAP_CLAMP_SEC = 10.0

_MALE_K = 0.64
_MALE_E = 1.92

# scale_to_21: min(21, A·log1p(raw/B)), constants re-fit to raw Banister units (see
# tests/unit/test_cardio_load.py for the synthetic fixtures + the bands they're pinned to: a rest-day
# all-day wear ≈ 7-9, a rest day + hard 90min BJJ session ≈ 15-17 — matching the feel of the pre-Wave-3.2
# zone-weight scale).
_SCALE_A = 6.28
_SCALE_B = 29.5

# Fallback hardness cutoffs (raw Banister TRIMP units) when there are <8 stored sessions to derive
# percentiles from — see hardness_cutoffs(). Anchored on the synthetic hard-BJJ 90min session fixture's
# raw load (~242.6, tests/unit/test_cardio_load.py): a session at or above the fixture's own load is "the
# fixture itself", so HARD_CUTOFF is set at 90% of it (any hard-effort session close to that shape still
# qualifies). MODERATE_CUTOFF is 40% of HARD_CUTOFF — chosen because the exponential HRR weighting means a
# genuinely moderate/technical session (lower average intensity, no sustained high-HRR intervals) lands
# well under half of a hard session's raw load, not linearly at half.
_FALLBACK_HARD_CUTOFF = 218.3
_FALLBACK_MODERATE_CUTOFF = 87.3


def banister_trimp(
    samples: list[tuple[datetime, int]], max_hr: float, rest_hr: float
) -> float:
    """Raw (unscaled) Banister TRIMP over a (ts, bpm) stream: minutes-at-intensity weighted by the
    exponential HRR curve. Each sample is weighted by actual seconds since the previous sample,
    gap-clamped (see _GAP_CLAMP_SEC) so a multi-hour capture dropout can't inject hours of phantom load.
    Degenerate max_hr<=rest_hr (no valid HRR range to place bpm within) → 0.0. Empty input → 0.0.
    """
    if not samples or max_hr <= rest_hr:
        return 0.0
    hrr = max_hr - rest_hr
    ordered = sorted(samples, key=lambda p: p[0])
    total = 0.0
    prev_ts: datetime | None = None
    for ts, bpm in ordered:
        if prev_ts is not None:
            gap = (ts - prev_ts).total_seconds()
            if gap > 0:
                dur_min = min(gap, _GAP_CLAMP_SEC) / 60.0
                x = max(0.0, min(1.0, (bpm - rest_hr) / hrr))
                total += dur_min * x * _MALE_K * exp(_MALE_E * x)
        prev_ts = ts
    return total


def session_load(
    samples: list[tuple[datetime, int]], max_hr: float, rest_hr: float
) -> float:
    """Raw Banister TRIMP for one workout window — same math as banister_trimp, with no 0-21 display
    scaling applied (that's scale_to_21, kept separate so hardness classification can work in raw units).
    """
    return banister_trimp(samples, max_hr, rest_hr)


def scale_to_21(raw: float) -> float:
    """Map a raw Banister TRIMP total onto the WHOOP-strain-feel 0-21 display band."""
    return round(min(21.0, _SCALE_A * log1p(raw / _SCALE_B)), 1)


def hardness_cutoffs(recent_session_loads: list[float]) -> tuple[float, float]:
    """(moderate_cutoff, hard_cutoff) in raw Banister TRIMP units. With >=8 recent session loads, use this
    person's own P40/P75 — a session below the 40th percentile of their own recent efforts is EASY, at or
    above the 75th is HARD, in between is MODERATE. Data-driven and self-relative rather than a fixed
    absolute band, since raw TRIMP scale depends on session duration and this person's HRR range. Below 8
    samples there isn't enough history for percentiles to be stable, so fall back to cutoffs anchored on
    the synthetic hard-BJJ fixture (see the module docstring constants).
    """
    if len(recent_session_loads) >= 8:
        return _percentile(recent_session_loads, 40), _percentile(
            recent_session_loads, 75
        )
    return _FALLBACK_MODERATE_CUTOFF, _FALLBACK_HARD_CUTOFF


def _percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (no numpy dependency)."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (pct / 100.0) * (len(ordered) - 1)
    lo, hi = int(rank), min(int(rank) + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * frac


def classify_hardness(load: float, cutoffs: tuple[float, float]) -> str:
    """Raw TRIMP load → 'EASY'/'MODERATE'/'HARD' (labels match the cockpit's existing badge classes)."""
    moderate_cutoff, hard_cutoff = cutoffs
    if load >= hard_cutoff:
        return "HARD"
    if load >= moderate_cutoff:
        return "MODERATE"
    return "EASY"
