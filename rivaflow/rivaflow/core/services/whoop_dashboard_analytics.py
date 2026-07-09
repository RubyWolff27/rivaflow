"""Raw-derived replacements for the WHOOP dashboard analytics endpoints.

Bitter-Lesson audit, Wave 1b-cleanup. These back the web dashboard's WHOOP
Analytics tab, which previously called `WhoopAnalyticsEngine` — a
cancelled-subscription cloud engine that read the frozen recovery/workout
caches, so the tab showed stale/empty data.

Cardiovascular drift (weekly resting-HR trend) is fully derived from the raw HR
the phone streams to `/whoop/ingest`. The recovery/strain/sleep correlation
panels need either a per-day recovery score (readiness is a today rollup) or a
`sessions`<->`whoop_sessions` strain link we don't have yet, so they return
correctly-shaped **empty** payloads with an explanatory insight. The tab renders
each panel only when it has data, so those panels stay hidden — honest, not
broken — until a follow-up enriches them.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from rivaflow.core import whoop_analytics
from rivaflow.core.services.insights_math import _linear_slope

# Shown on panels that are intentionally not yet derived from raw data.
_PENDING_RECOVERY = (
    "Recovery-based correlation needs per-day recovery scoring — "
    "coming as the raw-derived model accrues history."
)
_PENDING_STRAIN = (
    "Per-session strain efficiency needs a session<->WHOOP-window link — "
    "coming in a later pass."
)


def _iso_week(day_str: str) -> str | None:
    try:
        return date.fromisoformat(day_str[:10]).strftime("%Y-W%U")
    except (ValueError, TypeError):
        return None


def cardiovascular_drift(user_id: int, days: int = 90) -> dict:
    """Weekly average resting-HR trend, derived from the raw HR stream.

    Matches the WhoopAnalyticsEngine.get_cardiovascular_drift contract so the
    dashboard's RHR-trend panel renders unchanged.
    """
    rows = whoop_analytics.daily_resting_hr(user_id, days=days)

    weekly: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        rhr = r.get("resting_hr")
        wk = _iso_week(str(r.get("day", "")))
        if rhr is None or wk is None:
            continue
        weekly[wk].append(float(rhr))

    if len(weekly) < 2:
        current = rows[-1].get("resting_hr") if rows else None
        return {
            "weekly_rhr": [],
            "slope": 0.0,
            "trend": "insufficient_data",
            "current_rhr": current,
            "baseline_rhr": current,
            "insight": "Need 2+ weeks of resting-HR data for a trend.",
        }

    weekly_avgs = [
        {
            "week": wk,
            "avg_rhr": round(statistics.mean(weekly[wk]), 1),
            "data_points": len(weekly[wk]),
        }
        for wk in sorted(weekly)
    ]
    slope = _linear_slope([w["avg_rhr"] for w in weekly_avgs])
    trend = "improving" if slope < -0.3 else "rising" if slope > 0.3 else "stable"
    current_rhr = weekly_avgs[-1]["avg_rhr"]
    baseline_rhr = weekly_avgs[0]["avg_rhr"]
    labels = {
        "improving": "declining (improving fitness)",
        "rising": "rising (possible fatigue)",
        "stable": "stable",
    }
    insight = (
        f"RHR trend: {labels[trend]}. Current: {current_rhr} bpm, "
        f"baseline: {baseline_rhr} bpm (slope: {slope:+.2f} bpm/week)."
    )
    return {
        "weekly_rhr": weekly_avgs,
        "slope": slope,
        "trend": trend,
        "current_rhr": current_rhr,
        "baseline_rhr": baseline_rhr,
        "insight": insight,
    }


def performance_correlation(user_id: int, days: int = 90) -> dict:
    """Recovery/HRV vs performance — pending per-day recovery scoring."""
    return {
        "recovery_correlation": {
            "scatter": [],
            "zones": {},
            "r_value": None,
            "optimal_zone": None,
            "insight": _PENDING_RECOVERY,
        },
        "hrv_predictor": {
            "scatter": [],
            "hrv_threshold": None,
            "r_value": None,
            "insight": _PENDING_RECOVERY,
        },
    }


def efficiency(user_id: int, days: int = 90) -> dict:
    """Strain efficiency + sleep analysis — pending session link / per-day recovery."""
    return {
        "strain_efficiency": {
            "top_sessions": [],
            "overall_efficiency": 0,
            "by_class_type": {},
            "by_gym": {},
            "insight": _PENDING_STRAIN,
        },
        "sleep_analysis": {
            "scatter": [],
            "total_sleep_r": None,
            "insight": _PENDING_RECOVERY,
        },
    }


def sleep_debt_tracker(user_id: int, days: int = 90) -> dict:
    """Weekly sleep debt vs training — pending a raw-sleep rebuild."""
    return {
        "weekly": [],
        "insight": "Weekly sleep-debt view is being rebuilt on raw sleep data.",
    }


def readiness_model(user_id: int, days: int = 90) -> dict:
    """Session outcomes by recovery zone — pending per-day recovery scoring."""
    return {"zones": {}, "insight": _PENDING_RECOVERY}
