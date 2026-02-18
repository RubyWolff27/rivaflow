"""WHOOP data sync methods -- recovery and workout fetching/caching."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rivaflow.core.services.whoop_service import WhoopService

logger = logging.getLogger(__name__)


def sync_workouts(self: WhoopService, user_id: int, days_back: int = 7) -> dict:
    """Fetch workouts from WHOOP API and cache them locally."""
    access_token = self.get_valid_access_token(user_id)

    start = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
    end = datetime.now(UTC).isoformat()

    all_workouts = []
    next_token = None

    # Paginate through results
    while True:
        data = self.client.get_workouts(
            access_token,
            start=start,
            end=end,
            next_token=next_token,
        )
        records = data.get("records", [])
        all_workouts.extend(records)

        next_token = data.get("next_token")
        if not next_token or len(records) == 0:
            break

    # Upsert into cache
    created = 0
    updated = 0
    for workout in all_workouts:
        score = workout.get("score", {}) or {}
        whoop_workout_id = str(workout.get("id", ""))
        existing = None

        # Check if this is an update
        try:
            from rivaflow.db.repositories.whoop_workout_cache_repo import (
                WhoopWorkoutCacheRepository,
            )

            existing = WhoopWorkoutCacheRepository.exists_by_whoop_id(
                user_id, whoop_workout_id
            )
        except Exception:
            pass

        kj = score.get("kilojoule")
        calories = round(kj / 4.184) if kj else None

        zone_durations = score.get("zone_duration")

        self.workout_cache_repo.upsert(
            user_id=user_id,
            whoop_workout_id=whoop_workout_id,
            start_time=workout.get("start", ""),
            end_time=workout.get("end", ""),
            sport_id=workout.get("sport_id"),
            sport_name=workout.get("sport_name"),
            timezone_offset=workout.get("timezone_offset"),
            strain=score.get("strain"),
            avg_heart_rate=score.get("average_heart_rate"),
            max_heart_rate=score.get("max_heart_rate"),
            kilojoules=kj,
            calories=calories,
            score_state=workout.get("score_state"),
            zone_durations=zone_durations,
            raw_data=workout,
        )

        if existing:
            updated += 1
        else:
            created += 1

    self.connection_repo.update_last_synced(user_id)

    # Log sport breakdown for debugging
    sport_counts: dict[str, int] = {}
    for w in all_workouts:
        key = f"{w.get('sport_id')}:{w.get('sport_name', '?')}"
        sport_counts[key] = sport_counts.get(key, 0) + 1
    logger.info(
        "Sync user=%s fetched=%d created=%d updated=%d sports=%s",
        user_id,
        len(all_workouts),
        created,
        updated,
        sport_counts,
    )

    # Auto-create sessions for BJJ workouts if enabled
    try:
        auto_created = self.auto_create_sessions_for_workouts(user_id)
    except Exception:
        logger.warning("Auto-create sessions failed", exc_info=True)
        auto_created = []

    # Fix timezone on existing auto-created sessions
    tz_fixed = 0
    try:
        tz_fixed = self.backfill_session_timezones(user_id)
    except Exception:
        logger.warning("Timezone backfill failed", exc_info=True)

    return {
        "total_fetched": len(all_workouts),
        "created": created,
        "updated": updated,
        "auto_sessions_created": len(auto_created),
        "tz_fixed": tz_fixed,
    }


def sync_recovery(self: WhoopService, user_id: int, days_back: int = 7) -> dict:
    """Fetch recovery/sleep data from WHOOP and cache locally."""
    access_token = self.get_valid_access_token(user_id)

    start = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
    end = datetime.now(UTC).isoformat()

    all_cycles = []
    next_token = None

    # Paginate through cycles
    while True:
        data = self.client.get_cycles(
            access_token,
            start=start,
            end=end,
            next_token=next_token,
        )
        records = data.get("records", [])
        all_cycles.extend(records)
        next_token = data.get("next_token")
        if not next_token or len(records) == 0:
            break

    # Fetch recovery data (separate endpoint)
    all_recovery = []
    next_token = None
    while True:
        data = self.client.get_recovery(
            access_token,
            start=start,
            end=end,
            next_token=next_token,
        )
        records = data.get("records", [])
        all_recovery.extend(records)
        next_token = data.get("next_token")
        if not next_token or len(records) == 0:
            break

    # Fetch sleep data
    all_sleep = []
    next_token = None
    while True:
        data = self.client.get_sleep(
            access_token,
            start=start,
            end=end,
            next_token=next_token,
        )
        records = data.get("records", [])
        all_sleep.extend(records)
        next_token = data.get("next_token")
        if not next_token or len(records) == 0:
            break

    # Build lookup maps
    recovery_by_cycle = {str(r.get("cycle_id")): r for r in all_recovery}
    sleep_by_cycle = {str(s.get("cycle_id", s.get("id"))): s for s in all_sleep}

    created = 0
    updated = 0

    for cycle in all_cycles:
        cycle_id = str(cycle.get("id", ""))
        cycle_start = cycle.get("start", "")
        cycle_end = cycle.get("end")

        recovery = recovery_by_cycle.get(cycle_id, {})
        rec_score = recovery.get("score", {}) or {}
        sleep = sleep_by_cycle.get(cycle_id, {})
        sleep_score = sleep.get("score", {}) or {}

        # Check if exists for tracking created vs updated
        existing = None
        try:
            from rivaflow.db.repositories.whoop_recovery_cache_repo import (
                WhoopRecoveryCacheRepository,
            )

            existing = WhoopRecoveryCacheRepository.exists_by_cycle_id(
                user_id, cycle_id
            )
        except Exception:
            pass

        self.recovery_cache_repo.upsert(
            user_id=user_id,
            whoop_cycle_id=cycle_id,
            recovery_score=rec_score.get("recovery_score"),
            resting_hr=rec_score.get("resting_heart_rate"),
            hrv_ms=rec_score.get("hrv_rmssd_milli"),
            spo2=rec_score.get("spo2_percentage"),
            skin_temp=rec_score.get("skin_temp_celsius"),
            sleep_performance=sleep_score.get("sleep_performance_percentage"),
            sleep_duration_ms=sleep_score.get("total_in_bed_time_milli"),
            sleep_need_ms=sleep_score.get("sleep_needed_baseline_milli"),
            sleep_debt_ms=sleep_score.get("sleep_debt_milli"),
            light_sleep_ms=sleep_score.get("total_light_sleep_time_milli"),
            slow_wave_ms=sleep_score.get("total_slow_wave_sleep_time_milli"),
            rem_sleep_ms=sleep_score.get("total_rem_sleep_time_milli"),
            awake_ms=sleep_score.get("total_awake_time_milli"),
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            raw_data={
                "cycle": cycle,
                "recovery": recovery,
                "sleep": sleep,
            },
        )

        if existing:
            updated += 1
        else:
            created += 1

    self.connection_repo.update_last_synced(user_id)

    return {
        "total_fetched": len(all_cycles),
        "created": created,
        "updated": updated,
    }


def get_latest_recovery(self: WhoopService, user_id: int) -> dict | None:
    """Get latest recovery data, syncing if cache is stale (>4hrs)."""
    latest = self.recovery_cache_repo.get_latest(user_id)

    if latest:
        synced_at = latest.get("synced_at", "")
        if isinstance(synced_at, str) and synced_at:
            try:
                synced_dt = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
                if synced_dt.tzinfo is None:
                    synced_dt = synced_dt.replace(tzinfo=UTC)
                if synced_dt > datetime.now(UTC) - timedelta(hours=4):
                    return latest
            except (ValueError, TypeError):
                pass

    # Cache empty or stale -- sync recent data
    try:
        self.sync_recovery(user_id, days_back=2)
    except Exception:
        logger.warning("Auto recovery sync failed", exc_info=True)

    return self.recovery_cache_repo.get_latest(user_id)


def apply_recovery_to_readiness(
    self: WhoopService, user_id: int, check_date: str
) -> dict | None:
    """Map WHOOP recovery to readiness auto-fill values.

    Returns suggested readiness fields or None if no data available.
    Does NOT auto-save -- the frontend controls when to save.
    """
    from datetime import date as date_cls

    target = date_cls.fromisoformat(check_date)
    day_before = (target - timedelta(days=1)).isoformat()

    records = self.recovery_cache_repo.get_by_date_range(
        user_id, day_before, check_date + "T23:59:59"
    )
    if not records:
        # Try syncing recent data
        try:
            self.sync_recovery(user_id, days_back=2)
            records = self.recovery_cache_repo.get_by_date_range(
                user_id, day_before, check_date + "T23:59:59"
            )
        except Exception:
            logger.warning("Recovery sync for auto-fill failed")
            return None

    if not records:
        return None

    # Use most recent record
    rec = records[0]
    score = rec.get("recovery_score")
    if score is None:
        return None

    # Map WHOOP recovery % to RivaFlow 1-5 scales
    if score >= 90:
        sleep_val, energy_val = 5, 5
    elif score >= 67:
        sleep_val, energy_val = 4, 4
    elif score >= 50:
        sleep_val, energy_val = 3, 3
    elif score >= 34:
        sleep_val, energy_val = 2, 2
    else:
        sleep_val, energy_val = 1, 1

    return {
        "sleep": sleep_val,
        "energy": energy_val,
        "hrv_ms": rec.get("hrv_ms"),
        "resting_hr": rec.get("resting_hr"),
        "spo2": rec.get("spo2"),
        "whoop_recovery_score": score,
        "whoop_sleep_score": rec.get("sleep_performance"),
        "data_source": "whoop",
    }


def auto_fill_readiness_from_recovery(self: WhoopService, user_id: int) -> dict | None:
    """Auto-fill today's readiness from WHOOP recovery data.

    Only runs if the user has the toggle enabled and no manual entry
    exists for today.
    """
    conn = self.connection_repo.get_by_user_id(user_id)
    if not conn or not conn.get("auto_fill_readiness"):
        return None

    from datetime import date as date_cls

    from rivaflow.core.services.readiness_service import (
        ReadinessService,
    )

    today = date_cls.today().isoformat()
    fill_data = self.apply_recovery_to_readiness(user_id, today)
    if not fill_data:
        return None

    # Check if a manual entry already exists for today
    from rivaflow.db.repositories.readiness_repo import (
        ReadinessRepository,
    )

    existing = ReadinessRepository.get_by_date(user_id, date_cls.today())
    if existing and existing.get("data_source") != "whoop":
        return None  # User has a manual entry, don't overwrite

    ReadinessService().log_readiness(
        user_id=user_id,
        check_date=date_cls.today(),
        sleep=fill_data["sleep"],
        stress=3,
        soreness=3,
        energy=fill_data["energy"],
        hrv_ms=fill_data.get("hrv_ms"),
        resting_hr=fill_data.get("resting_hr"),
        spo2=fill_data.get("spo2"),
        whoop_recovery_score=fill_data.get("whoop_recovery_score"),
        whoop_sleep_score=fill_data.get("whoop_sleep_score"),
        data_source="whoop",
    )
    return fill_data


def backfill_session_timezones(self: WhoopService, user_id: int) -> int:
    """Fix UTC times on existing auto-created sessions.

    Looks up linked WHOOP workouts, applies timezone_offset to
    recalculate class_time and session_date. Returns count fixed.
    """
    from rivaflow.core.services.whoop_service import (
        _parse_tz_offset,
    )
    from rivaflow.db.repositories.whoop_workout_cache_repo import (
        WhoopWorkoutCacheRepository,
    )

    fixed = 0
    rows = WhoopWorkoutCacheRepository.get_linked_sessions_with_tz(user_id)

    for row_d in rows:
        local_tz = _parse_tz_offset(row_d["timezone_offset"])
        if not local_tz or not row_d["start_time"]:
            continue
        try:
            start_str = str(row_d["start_time"])
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            local_dt = start_dt.astimezone(local_tz)
            new_date = local_dt.date().isoformat()
            new_time = local_dt.strftime("%H:%M")
            self.session_repo.update(
                user_id=user_id,
                session_id=row_d["session_id"],
                session_date=new_date,
                class_time=new_time,
            )
            fixed += 1
        except Exception:
            logger.debug(
                "Timezone backfill failed for session %s",
                row_d["session_id"],
                exc_info=True,
            )
    if fixed:
        logger.info("Timezone backfill: user=%s fixed=%d", user_id, fixed)
    return fixed
