"""P1 sleep layer (pure core): B9 Sleep Need + Debt, B10 Sleep Regularity.

Personalised to Ruby's >9h DNA sleep-need (WHOOP_FUTURE_STATE_PLAN.md B9/B10). All from the HR-based sleep
windows we already estimate — need/debt accrual + onset/offset consistency, no locked sensor required.
"""

from __future__ import annotations

from math import cos, log, pi, sin, sqrt
from statistics import mean

NEED_HOURS = 9.0  # Ruby's DNA sleep-need (>9h), not the generic 8h
DEBT_WINDOW = 7  # rolling week of shortfall

QUALITY_VERSION = "sleep-quality-v1"

# Composed sleep-quality weights (Wave 3.5) — duration-vs-need dominates; coverage/fragmentation and onset
# timing are secondary signals. Always sum to 1.0 (see sleep_quality's cold-start redistribution).
_QUALITY_DURATION_WEIGHT = 0.6
_QUALITY_COVERAGE_WEIGHT = 0.25
_QUALITY_REGULARITY_WEIGHT = 0.15

_QUALITY_FRAGMENTED_PENALTY = (
    20.0  # points off the coverage component when the night was fragmented
)
# (whoop_analytics._sleep_from_points flags fragmented when coverage_pct < 60)

_QUALITY_REGULARITY_MIN_NIGHTS = (
    4  # fewer usable onsets than this → cold start: redistribute this
)
# component's weight into duration rather than score against a noisy 1-3 point spread
_REGULARITY_TOLERANCE_LO_MIN = (
    60.0  # onset circular-SD <= this → full regularity score (100)
)
_REGULARITY_TOLERANCE_HI_MIN = 90.0  # onset circular-SD >= this → zero regularity score


def sleep_debt(
    durations: list[float], need: float = NEED_HOURS, window: int = DEBT_WINDOW
) -> dict:
    """Accrued sleep debt = sum of nightly shortfalls vs need over the recent window. Positive debt means
    under-slept vs his >9h need."""
    if not durations:
        return {"available": False, "reason": "No sleep history yet."}
    recent = durations[-window:]
    debt = sum(max(0.0, need - d) for d in recent)
    avg = mean(recent)
    last_short = max(0.0, need - durations[-1])
    return {
        "available": True,
        "need_hours": need,
        "recent_avg_hours": round(avg, 1),
        "debt_hours": round(debt, 1),
        "nights": len(recent),
        "tonight_recommended_hours": round(
            need + min(2.0, last_short), 1
        ),  # repay a little, capped
        "headline": (
            f"{round(debt, 1)}h sleep debt over {len(recent)} nights vs your {need:g}h need."
            if debt > 0.5
            else f"On top of your {need:g}h need — no meaningful debt."
        ),
    }


def _circular_sd_hours(hours: list[float]) -> float:
    """Circular SD (in hours) of times-of-day — 23:30 and 00:30 are 1h apart, not 23h. Returns 0 for a
    single point; large for scattered times."""
    angles = [h / 24.0 * 2 * pi for h in hours]
    c = mean([cos(a) for a in angles])
    s = mean([sin(a) for a in angles])
    r = sqrt(c * c + s * s)
    if r >= 1.0:
        return 0.0
    if r <= 1e-9:
        return 24.0 / 4  # maximally dispersed → quarter-day-ish
    circ_sd_rad = sqrt(-2.0 * log(r))
    return circ_sd_rad * 24.0 / (2 * pi)


def sleep_regularity(onset_hours: list[float]) -> dict:
    """B10 — onset consistency. Lower circular SD of bed times = more regular. Score 0–100 (100 = perfectly
    regular); a 2h onset SD maps to ~0. Cheap, reproducible from the sleep-window start alone.
    """
    if len(onset_hours) < 3:
        return {
            "available": False,
            "reason": "Need at least 3 nights for a regularity estimate.",
        }
    sd_h = _circular_sd_hours(onset_hours)
    score = max(0, min(100, round(100 * (1 - sd_h / 2.0))))  # 0h SD → 100; >=2h SD → 0
    if score >= 80:
        head = "Very regular bedtimes — protective for recovery."
    elif score >= 50:
        head = "Fairly regular — tightening bedtime would help."
    else:
        head = "Irregular bedtimes — the biggest cheap win for your sleep."
    return {
        "available": True,
        "onset_sd_hours": round(sd_h, 2),
        "score": score,
        "nights": len(onset_hours),
        "headline": head,
    }


def _duration_component(duration_hours: float, need: float) -> float:
    """Duration-vs-need score (0-100), clamped — the EXACT pre-Wave-3.5 quality_score formula
    (whoop_analytics.whoop_summary), just driven by the caller's own sleep need instead of the hardcoded
    9.0h. This is the dominant component of the composed score below."""
    if need <= 0:
        return 0.0
    return max(0.0, min(100.0, (duration_hours / need) * 100.0))


def _coverage_component(coverage_pct: float | None, fragmented: bool) -> float | None:
    """Coverage/fragmentation score (0-100) from the sleep window's own coverage_pct
    (whoop_analytics._sleep_from_points), penalised when the night was flagged fragmented. None when the
    caller has no coverage_pct (older/cold-start callers) — the composition redistributes its weight.
    """
    if coverage_pct is None:
        return None
    score = float(coverage_pct)
    if fragmented:
        score -= _QUALITY_FRAGMENTED_PENALTY
    return max(0.0, min(100.0, score))


def _regularity_component(onset_hours: list[float]) -> float | None:
    """Timing-regularity score (0-100) from onset-time spread (circular SD, reusing _circular_sd_hours —
    the same math B10's sleep_regularity uses) over the caller's recent nights: full marks at <=60min
    spread, zero at >=90min, linear between. None (cold start) below _QUALITY_REGULARITY_MIN_NIGHTS usable
    onsets — too few points to trust a spread estimate."""
    if len(onset_hours) < _QUALITY_REGULARITY_MIN_NIGHTS:
        return None
    spread_min = _circular_sd_hours(onset_hours) * 60.0
    if spread_min <= _REGULARITY_TOLERANCE_LO_MIN:
        return 100.0
    if spread_min >= _REGULARITY_TOLERANCE_HI_MIN:
        return 0.0
    span = _REGULARITY_TOLERANCE_HI_MIN - _REGULARITY_TOLERANCE_LO_MIN
    return 100.0 * (1.0 - (spread_min - _REGULARITY_TOLERANCE_LO_MIN) / span)


def sleep_quality(
    duration_hours: float,
    need: float,
    *,
    coverage_pct: float | None = None,
    fragmented: bool = False,
    onset_hours: list[float] | None = None,
) -> dict:
    """Wave 3.5 — composed sleep quality: a weighted blend of duration-vs-need (dominant), coverage/
    fragmentation, and onset-timing regularity, each 0-100 (see the three _*_component helpers above).
    Cold start (fewer than _QUALITY_REGULARITY_MIN_NIGHTS onsets, or no coverage_pct supplied)
    redistributes that component's weight into duration rather than scoring against thin/absent data, so
    the blend weights always sum to 1.0.

    The composed score differs from the old duration-only quality_score BY DESIGN (that's the upgrade) —
    equivalence is only guaranteed for the duration COMPONENT itself (see _duration_component), not the
    final blended score.
    """
    duration = _duration_component(duration_hours, need)
    coverage = _coverage_component(coverage_pct, fragmented)
    regularity = _regularity_component(onset_hours or [])

    w_duration = _QUALITY_DURATION_WEIGHT
    w_coverage = _QUALITY_COVERAGE_WEIGHT
    w_regularity = _QUALITY_REGULARITY_WEIGHT
    if coverage is None:
        w_duration += w_coverage
        w_coverage = 0.0
    if regularity is None:
        w_duration += w_regularity
        w_regularity = 0.0

    score = w_duration * duration
    if coverage is not None:
        score += w_coverage * coverage
    if regularity is not None:
        score += w_regularity * regularity

    return {
        "score": max(0, min(100, round(score))),
        "quality_version": QUALITY_VERSION,
        "components": {
            "duration": round(duration, 1),
            "coverage": round(coverage, 1) if coverage is not None else None,
            "regularity": round(regularity, 1) if regularity is not None else None,
        },
    }
