"""Raw-derived biometrics provider — the single seam that replaced the
cancelled WHOOP-cloud recovery cache (Bitter-Lesson audit, Wave 1b).

Grapple coaching, suggestions and insights used to read recovery/HRV from
`whoop_recovery_cache` — a cloud-API table that went static when Ruby cancelled
the WHOOP subscription, gated behind a `whoop_connections` row that no longer
matches the live BLE user, so every consumer silently returned empty.

They now read from here instead: recent recovery/HRV/resting-HR/sleep derived
from the raw HR+RR the phone streams to `/whoop/ingest`, via the self-hosted
`whoop_analytics` engine. Records keep the old cache shape so consumers need
only swap the source and drop the dead connection gate.

Honest ceiling: `spo2`, `rem_sleep_ms`, `slow_wave_ms` stay `None` — they need
the un-cracked R22/K21 decode. Consumers already skip `None` fields.
"""

from __future__ import annotations

import logging

from rivaflow.core import whoop_analytics

logger = logging.getLogger(__name__)

# Fields a consumer may read off a record but which we cannot derive from HR+RR.
_LOCKED_FIELDS = {"spo2": None, "rem_sleep_ms": None, "slow_wave_ms": None}


def recovery_series(user_id: int, days: int = 7) -> list[dict]:
    """Recent per-day recovery records, oldest→newest, in the recovery-cache shape.

    Each record carries `date`, `hrv_ms`, `resting_hr` (raw-derived per day) plus
    the locked fields as `None`. The most recent record additionally carries the
    full readiness snapshot — `recovery_score` (today's readiness score),
    `sleep_performance`, `sleep_duration_ms` — since those are a today rollup.

    Returns `[]` when there is not enough raw data yet (consumers treat an empty
    series exactly as they treated an empty cache).
    """
    rmssd_days = whoop_analytics.daily_resting_rmssd(user_id, days=days)
    rhr_by_day = {
        r["day"]: r.get("resting_hr")
        for r in whoop_analytics.daily_resting_hr(user_id, days=days)
    }

    records: list[dict] = []
    for r in rmssd_days:
        records.append(
            {
                "date": r.get("day"),
                "recovery_score": None,
                "hrv_ms": r.get("rmssd"),
                "resting_hr": rhr_by_day.get(r.get("day")),
                "sleep_performance": None,
                "sleep_duration_ms": None,
                **_LOCKED_FIELDS,
            }
        )

    if not records:
        return records

    # Attach today's readiness snapshot to the newest record.
    latest = records[-1]
    summary = whoop_analytics.whoop_summary(user_id)
    readiness = summary.get("readiness") or {}
    latest["recovery_score"] = readiness.get("score")

    hrv_today = summary.get("hrv_today") or {}
    if latest["hrv_ms"] is None:
        latest["hrv_ms"] = hrv_today.get("rmssd")
    rhr_today = summary.get("resting_hr_today") or {}
    if latest["resting_hr"] is None:
        latest["resting_hr"] = rhr_today.get("resting_hr")

    sleep = summary.get("sleep") or {}
    dur_h = sleep.get("duration_hours")
    if dur_h is not None:
        latest["sleep_duration_ms"] = round(dur_h * 3_600_000)
        latest["sleep_performance"] = sleep.get("quality_score")

    return records


def latest_recovery(user_id: int) -> dict | None:
    """The most recent recovery record, or None when there is no raw data yet."""
    series = recovery_series(user_id, days=7)
    return series[-1] if series else None
