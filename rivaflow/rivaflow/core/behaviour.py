"""B11 — Behaviour / Journal correlation (pure core).

The WHOOP-Journal killer feature (WHOOP_FUTURE_STATE_PLAN.md B11): for a tagged behaviour (alcohol, late
training, Sabbath rest), compare yes-nights vs no-nights on a recovery metric and report the effect size, so
Ruby sees how each habit actually moves HIS numbers. Needs a light tagging path (that plumbing is future
work); this is the statistics it will feed.
"""

from __future__ import annotations

from statistics import mean, pstdev


def cohens_d(a: list[float], b: list[float]) -> float | None:
    """Standardised mean difference (a − b) with pooled SD. None if either group is too small or has no spread."""
    if len(a) < 2 or len(b) < 2:
        return None
    na, nb = len(a), len(b)
    va, vb = pstdev(a) ** 2, pstdev(b) ** 2
    pooled = (((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)) ** 0.5
    if pooled == 0:
        return None
    return float((mean(a) - mean(b)) / pooled)


def _magnitude(d: float) -> str:
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    if ad < 0.5:
        return "small"
    if ad < 0.8:
        return "medium"
    return "large"


def behaviour_effect(tag: str, metric: str, yes_values: list[float], no_values: list[float]) -> dict:
    """Effect of a tagged behaviour on a metric: yes-nights vs no-nights means + Cohen's d. Positive delta
    means the behaviour is associated with a HIGHER metric value."""
    d = cohens_d(yes_values, no_values)
    if d is None:
        return {"available": False, "tag": tag, "metric": metric,
                "reason": "Need ≥2 nights each with and without the tag (and some spread)."}
    ym, nm = mean(yes_values), mean(no_values)
    delta = ym - nm
    mag = _magnitude(d)
    direction = "higher" if delta >= 0 else "lower"
    return {
        "available": True,
        "tag": tag,
        "metric": metric,
        "yes_mean": round(ym, 2),
        "no_mean": round(nm, 2),
        "delta": round(delta, 2),
        "cohens_d": round(d, 2),
        "magnitude": mag,
        "n_yes": len(yes_values),
        "n_no": len(no_values),
        "headline": f"On {tag} nights your {metric} is {mag} {direction} ({round(delta, 2):+}).",
    }
