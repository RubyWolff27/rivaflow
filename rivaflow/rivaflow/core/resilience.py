"""B16 — Resilience & Cumulative Stress (pure core).

Slow-burn burnout warning (WHOOP_FUTURE_STATE_PLAN.md B16): 14-day bounce-back capacity + a 31-day chronic
stress scan (Oura-style), from the daily lnRMSSD series and per-day strain flags. Trends, not verdicts.
"""

from __future__ import annotations

from statistics import mean, pstdev

RESILIENCE_LEVELS = ["Limited", "Adequate", "Solid", "Strong", "Exceptional"]


def resilience(recent_lnrmssd: list[float], baseline_lnrmssd: list[float]) -> dict:
    """Bounce-back capacity over the recent (≈14d) window vs a longer baseline. High = recent HRV sits at/above
    baseline AND is stable (low variability). Maps to the 5 Oura levels."""
    if len(recent_lnrmssd) < 5 or len(baseline_lnrmssd) < 7:
        return {"available": False, "reason": "Need ~2 weeks recent + a longer baseline for resilience."}
    b_mean = mean(baseline_lnrmssd)
    b_sd = pstdev(baseline_lnrmssd) or 1.0
    level_z = (mean(recent_lnrmssd) - b_mean) / b_sd            # where recent sits vs baseline
    stability = 1.0 - min(1.0, (pstdev(recent_lnrmssd) / (b_sd or 1.0)))   # 1 = very stable
    score = max(0, min(100, round(50 + level_z * 20 + stability * 20)))
    idx = min(4, max(0, score // 20))
    return {"available": True, "score": score, "level": RESILIENCE_LEVELS[idx],
            "level_vs_baseline_z": round(level_z, 2), "stability": round(stability, 2),
            "headline": f"Resilience {RESILIENCE_LEVELS[idx]} — bounce-back capacity over the last two weeks."}


def cumulative_stress(strained_flags: list[bool], window: int = 31) -> dict:
    """31-day chronic-stress scan: how many of the last `window` days were strained (amber/red or suppressed
    HRV). A rising count is the burnout early-warning daily scores normalise away."""
    if not strained_flags:
        return {"available": False, "reason": "No daily stress flags yet."}
    recent = strained_flags[-window:]
    load = sum(1 for f in recent if f)
    pct = 100.0 * load / len(recent)
    if pct < 20:
        band, head = "low", "Low chronic stress load."
    elif pct < 40:
        band, head = "moderate", "Moderate chronic load — keep an eye on recovery."
    else:
        band, head = "high", "High chronic stress load over the month — plan a deload."
    return {"available": True, "strained_days": load, "days": len(recent),
            "pct": round(pct, 1), "band": band, "headline": head}
