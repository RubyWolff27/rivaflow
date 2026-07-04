"""P1 sleep layer (pure core): B9 Sleep Need + Debt, B10 Sleep Regularity.

Personalised to Ruby's >9h DNA sleep-need (WHOOP_FUTURE_STATE_PLAN.md B9/B10). All from the HR-based sleep
windows we already estimate — need/debt accrual + onset/offset consistency, no locked sensor required.
"""

from __future__ import annotations

from math import cos, log, pi, sin, sqrt
from statistics import mean

NEED_HOURS = 9.0  # Ruby's DNA sleep-need (>9h), not the generic 8h
DEBT_WINDOW = 7  # rolling week of shortfall


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
            f"{round(debt, 1)}h sleep debt over {len(recent)} nights vs your {need}h need."
            if debt > 0.5
            else f"On top of your {need}h need — no meaningful debt."
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
