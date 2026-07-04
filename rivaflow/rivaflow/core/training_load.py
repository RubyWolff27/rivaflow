"""P1 training-load layer (pure core): B7 ACWR, B8 Heart-Rate Recovery, B12 recovery-cost coupling.

Injury-prevention + coaching math for a masters grappler (WHOOP_FUTURE_STATE_PLAN.md B7/B8/B12), all from
HR + the daily cardio-load series. No mortality/prognostic framing — HRR is a within-person fitness trend.
"""

from __future__ import annotations

from statistics import mean

# Gabbett acute:chronic workload zones.
ACWR_UNDER = 0.8
ACWR_SWEET_HI = 1.3
ACWR_CAUTION_HI = 1.5


def acwr(daily_load: list[float], acute_days: int = 7, chronic_days: int = 28) -> dict:
    """Acute:Chronic Workload Ratio (Gabbett): last 7d mean load ÷ last 28d mean load. Flags the
    overreaching/injury window. Needs a full chronic window to be meaningful."""
    if len(daily_load) < chronic_days:
        return {
            "available": False,
            "reason": f"Need {chronic_days}d of load for a chronic baseline ({len(daily_load)} so far).",
        }
    acute = mean(daily_load[-acute_days:])
    chronic = mean(daily_load[-chronic_days:])
    ratio = acute / chronic if chronic > 0 else 0.0
    if ratio < ACWR_UNDER:
        zone, head = "undertraining", "Load below your chronic base — room to build."
    elif ratio <= ACWR_SWEET_HI:
        zone, head = "sweet-spot", "Load balanced against your base — keep it here."
    elif ratio <= ACWR_CAUTION_HI:
        zone, head = (
            "caution",
            "Ramping faster than your base — ease the next few days.",
        )
    else:
        zone, head = (
            "high-risk",
            "Load well above your base — the injury-risk window; back off.",
        )
    return {
        "available": True,
        "acute": round(acute, 1),
        "chronic": round(chronic, 1),
        "ratio": round(ratio, 2),
        "zone": zone,
        "headline": head,
    }


def heart_rate_recovery(
    hr_series: list[int], hz: float = 1.0, window_sec: int = 60
) -> dict:
    """Protocol HRR: bpm drop from the session peak to `window_sec` after it (Cole-style, within-person).
    A within-person FITNESS trend only — no mortality claim (that evidence is from standardised GXTs, not
    ad-hoc session ends). `clean` is False if the peak is too close to the end to measure the full window.
    """
    if len(hr_series) < 2:
        return {"available": False, "reason": "No HR in window."}
    peak_idx = max(range(len(hr_series)), key=lambda i: hr_series[i])
    peak = hr_series[peak_idx]
    after_idx = peak_idx + int(round(window_sec * hz))
    if after_idx >= len(hr_series):
        return {
            "available": False,
            "reason": "Peak too close to session end to measure full HRR window.",
            "peak": peak,
            "clean": False,
        }
    hrr = peak - hr_series[after_idx]
    return {
        "available": True,
        "peak": peak,
        "hr_after": hr_series[after_idx],
        "hrr_bpm": hrr,
        "window_sec": window_sec,
        "clean": True,
        "note": "Within-person fitness trend — not a mortality marker.",
    }


def recovery_cost(load_series: list[float], next_metric: list[float]) -> dict:
    """B12 — lagged coupling: prior-day load → next-day recovery metric (e.g. lnRMSSD). Pairs load[i] with
    next_metric[i+1] and fits a simple linear regression. Negative slope = load costs you next-day HRV.
    """
    pairs = [
        (load_series[i], next_metric[i + 1])
        for i in range(min(len(load_series), len(next_metric)) - 1)
    ]
    if len(pairs) < 5:
        return {
            "available": False,
            "reason": "Need more paired load/next-day days for a coupling estimate.",
        }
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return {
            "available": False,
            "reason": "No variance in load or recovery to couple.",
        }
    slope = sxy / sxx
    r = sxy / (sxx**0.5 * syy**0.5)
    direction = "costs" if slope < 0 else "supports"
    return {
        "available": True,
        "slope": round(slope, 4),
        "r": round(r, 2),
        "n": len(pairs),
        "headline": f"Each unit of prior-day load {direction} next-day recovery (slope {round(slope, 3)}).",
    }
