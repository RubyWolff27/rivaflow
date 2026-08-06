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

# Shown on panels that are intentionally not yet derived from raw data.
_PENDING_RECOVERY = (
    "Recovery-based correlation needs per-day recovery scoring — "
    "coming as the raw-derived model accrues history."
)
_PENDING_STRAIN = (
    "Per-session strain efficiency needs a session<->WHOOP-window link — "
    "coming in a later pass."
)


def cardiovascular_drift(user_id: int, days: int = 90) -> dict:
    """Weekly resting-HR trend — empty since the raw BLE feed retired (Wave 1c).

    Keeps the WhoopAnalyticsEngine.get_cardiovascular_drift contract so the
    dashboard panel hides itself, exactly like the other pending panels. Wave 2
    repoints this to the Fitbit Air / Google Health resting-HR series.
    """
    return {
        "weekly_rhr": [],
        "slope": 0.0,
        "trend": "insufficient_data",
        "current_rhr": None,
        "baseline_rhr": None,
        "insight": "Resting-HR trend is being rebuilt on Fitbit Air data.",
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
