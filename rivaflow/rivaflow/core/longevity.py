"""P2 longevity layer (pure core): B14 passive VO2max, B15 cardiovascular-age PROXY.

Web-surfaced trend estimates from RHR + HRV + demographics (WHOOP_FUTURE_STATE_PLAN.md B14/B15), with the
red-team's honesty guards: VO2max is a BANDED RANGE (not a point), and cardio-age is explicitly a PROXY with
no alarming arrows — true arterial-stiffness age needs the locked PPG pulse-wave morphology.
"""

from __future__ import annotations

VO2_BAND = 3.5   # ± ml/kg/min — the honest uncertainty on a non-exercise estimate

# Rough age-expected VO2max for a trained-ish male (ml/kg/min), for the cardio-age PROXY only.
VO2_EXPECTED_AT_30 = 48.0
VO2_DECLINE_PER_YEAR = 0.4


def passive_vo2max(hr_max: float, hr_rest: float) -> dict:
    """Uth–Sørensen–Overgaard non-exercise estimate: VO2max ≈ 15.3 · (HRmax/HRrest). Presented as a BANDED
    range, never a single point (red-team requirement)."""
    if hr_rest <= 0 or hr_max <= 0 or hr_max <= hr_rest:
        return {"available": False, "reason": "Need a valid max-HR above resting HR."}
    point = 15.3 * (hr_max / hr_rest)
    return {
        "available": True,
        "vo2max_estimate": round(point, 1),
        "range": [round(point - VO2_BAND, 1), round(point + VO2_BAND, 1)],
        "method": "Uth HRmax/HRrest ratio (non-exercise)",
        "note": "Banded estimate from HR ratio — not a lab measurement; present as a range/trend.",
    }


def cardio_age_proxy(vo2max: float, age: float) -> dict:
    """A PROXY fitness-age from VO2max vs age-expected norms — NOT arterial-stiffness age (that needs locked
    PPG morphology). Deliberately caveated, no alarming arrow: a lower number is better, framed neutrally."""
    if vo2max <= 0:
        return {"available": False, "reason": "Need a VO2max estimate first."}
    expected_now = VO2_EXPECTED_AT_30 - VO2_DECLINE_PER_YEAR * (age - 30)
    # fitter-than-expected → younger proxy; each 0.4 ml/kg/min ≈ one year.
    fitness_age = age + (expected_now - vo2max) / VO2_DECLINE_PER_YEAR
    fitness_age = max(18.0, min(90.0, fitness_age))
    return {
        "available": True,
        "cardio_age_proxy": round(fitness_age, 1),
        "chronological_age": age,
        "is_proxy": True,
        "note": ("A PROXY from VO2max vs age norms — not clinical arterial-stiffness age (needs locked PPG). "
                 "A trend to watch gently, not a health verdict."),
    }
