"""WHOOP workout matching, linking, and auto-creation logic."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from rivaflow.core.exceptions import NotFoundError

if TYPE_CHECKING:
    from rivaflow.core.services.whoop_service import WhoopService

logger = logging.getLogger(__name__)


def find_matching_workouts(
    self: WhoopService, user_id: int, session_id: int
) -> list[dict]:
    """Find WHOOP workouts that overlap with a training session."""
    session = self.session_repo.get_by_id(user_id, session_id)
    if not session:
        raise NotFoundError("Session not found")

    session_date = session.get("session_date")
    class_time = session.get("class_time")
    duration_mins = session.get("duration_mins", 60)

    if not class_time:
        return []

    # Parse session start datetime
    if isinstance(session_date, str):
        date_part = datetime.fromisoformat(session_date).date()
    else:
        date_part = session_date

    # Parse class_time (HH:MM format)
    try:
        time_parts = class_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    except (ValueError, IndexError):
        return []

    # class_time is in the user's local timezone, not UTC.
    # Convert to UTC using the user's profile timezone.
    import zoneinfo

    user_tz = UTC
    try:
        profile = self.profile_repo.get(user_id)
        tz_name = profile.get("timezone") if profile else None
        if tz_name and tz_name != "UTC":
            user_tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        logger.debug("Could not load user timezone, defaulting to UTC")

    local_dt = datetime(
        date_part.year,
        date_part.month,
        date_part.day,
        hour,
        minute,
        tzinfo=user_tz,
    )
    session_start = local_dt.astimezone(UTC)
    session_end = session_start + timedelta(minutes=duration_mins)

    # Expand search window +/- 2 hours
    search_start = (session_start - timedelta(hours=2)).isoformat()
    search_end = (session_end + timedelta(hours=2)).isoformat()

    # First try cache
    candidates = self.workout_cache_repo.get_by_user_and_time_range(
        user_id, search_start, search_end
    )

    # If empty, trigger sync then re-query
    if not candidates:
        try:
            self.sync_workouts(user_id, days_back=3)
            candidates = self.workout_cache_repo.get_by_user_and_time_range(
                user_id, search_start, search_end
            )
        except Exception:
            logger.warning(
                "Auto-sync failed during matching",
                exc_info=True,
            )
            return []

    # Calculate overlap
    return _calculate_overlap_matches(candidates, session_start, session_end)


def find_matching_workouts_by_params(
    self: WhoopService,
    user_id: int,
    session_date: str,
    class_time: str,
    duration_mins: int,
) -> list[dict]:
    """Find matching workouts without a saved session (for new sessions).

    Same algorithm as find_matching_workouts but takes params directly.
    """
    if not class_time:
        return []

    date_part = datetime.fromisoformat(session_date).date()

    try:
        time_parts = class_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    except (ValueError, IndexError):
        return []

    session_start = datetime(
        date_part.year,
        date_part.month,
        date_part.day,
        hour,
        minute,
        tzinfo=UTC,
    )
    session_end = session_start + timedelta(minutes=duration_mins)

    search_start = (session_start - timedelta(hours=2)).isoformat()
    search_end = (session_end + timedelta(hours=2)).isoformat()

    candidates = self.workout_cache_repo.get_by_user_and_time_range(
        user_id, search_start, search_end
    )

    if not candidates:
        try:
            self.sync_workouts(user_id, days_back=3)
            candidates = self.workout_cache_repo.get_by_user_and_time_range(
                user_id, search_start, search_end
            )
        except Exception:
            logger.warning(
                "Auto-sync failed during matching",
                exc_info=True,
            )
            return []

    return _calculate_overlap_matches(candidates, session_start, session_end)


def apply_workout_to_session(
    self: WhoopService,
    user_id: int,
    session_id: int,
    workout_cache_id: int,
) -> dict:
    """Apply cached WHOOP data to a session's WHOOP fields."""
    session = self.session_repo.get_by_id(user_id, session_id)
    if not session:
        raise NotFoundError("Session not found")

    # Get the cached workout
    from rivaflow.db.repositories.whoop_workout_cache_repo import (
        WhoopWorkoutCacheRepository,
    )

    workout = WhoopWorkoutCacheRepository.get_by_id_and_user(workout_cache_id, user_id)
    if not workout:
        raise NotFoundError("Workout not found in cache")

    # Update session WHOOP fields
    kj = workout.get("kilojoules")
    calories = workout.get("calories")
    if not calories and kj:
        calories = round(kj / 4.184)

    self.session_repo.update(
        user_id=user_id,
        session_id=session_id,
        whoop_strain=workout.get("strain"),
        whoop_calories=calories,
        whoop_avg_hr=workout.get("avg_heart_rate"),
        whoop_max_hr=workout.get("max_heart_rate"),
    )

    # Link cache to session
    self.workout_cache_repo.link_to_session(workout_cache_id, session_id)

    # Recalculate session score with new WHOOP data
    try:
        from rivaflow.core.services.session_scoring_service import (
            SessionScoringService,
        )

        SessionScoringService().score_session(user_id, session_id)
    except Exception:
        logger.warning(
            "Session scoring after WHOOP link failed",
            exc_info=True,
        )

    return self.session_repo.get_by_id(user_id, session_id)


def auto_create_sessions_for_workouts(self: WhoopService, user_id: int) -> list[int]:
    """Auto-create sessions from unlinked BJJ WHOOP workouts.

    Returns list of created session IDs.
    """
    from rivaflow.core.services.whoop_service import (
        _parse_tz_offset,
    )

    conn = self.connection_repo.get_by_user_id(user_id)
    if not conn or not conn.get("auto_create_sessions"):
        logger.info(
            "Auto-create skipped: user=%s auto_create=%s",
            user_id,
            conn.get("auto_create_sessions") if conn else "no_conn",
        )
        return []

    # Load profile for defaults
    profile = self.profile_repo.get(user_id)
    default_gym = "(Set in Profile)"
    default_class_type = "no-gi"
    if profile:
        default_gym = profile.get("default_gym") or default_gym
        default_class_type = profile.get("primary_training_type") or default_class_type

    unlinked = self.workout_cache_repo.get_unlinked_workouts(user_id)
    logger.info(
        "Auto-create: user=%s unlinked=%d sports=%s",
        user_id,
        len(unlinked),
        [w.get("sport_name") for w in unlinked],
    )
    created_ids = []

    for workout in unlinked:
        try:
            start_str = str(workout.get("start_time", ""))
            end_str = str(workout.get("end_time", ""))
            if not start_str or not end_str:
                continue

            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

            # Convert to local time using WHOOP timezone offset
            local_tz = _parse_tz_offset(workout.get("timezone_offset"))
            if local_tz:
                start_dt = start_dt.astimezone(local_tz)
                end_dt = end_dt.astimezone(local_tz)

            session_date = start_dt.date()
            class_time = start_dt.strftime("%H:%M")
            duration_secs = (end_dt - start_dt).total_seconds()
            duration_mins = max(1, round(duration_secs / 60))

            kj = workout.get("kilojoules")
            calories = workout.get("calories")
            if not calories and kj:
                calories = round(kj / 4.184)

            strain = workout.get("strain")
            if strain is not None:
                strain = round(strain, 1)

            session_id = self.session_repo.create(
                user_id=user_id,
                session_date=session_date,
                class_type=default_class_type,
                gym_name=default_gym,
                class_time=class_time,
                duration_mins=duration_mins,
                whoop_strain=strain,
                whoop_calories=calories,
                whoop_avg_hr=workout.get("avg_heart_rate"),
                whoop_max_hr=workout.get("max_heart_rate"),
                source="whoop",
                needs_review=True,
            )

            self.workout_cache_repo.link_to_session(workout["id"], session_id)
            created_ids.append(session_id)

            # Best-effort scoring of auto-created session
            try:
                from rivaflow.core.services.session_scoring_service import (
                    SessionScoringService,
                )

                SessionScoringService().score_session(user_id, session_id)
            except Exception:
                logger.warning(
                    "Scoring auto-created session %s failed",
                    session_id,
                    exc_info=True,
                )
        except Exception:
            logger.warning(
                "Failed to auto-create session for workout %s",
                workout.get("id"),
                exc_info=True,
            )

    return created_ids


# ─────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────


def _calculate_overlap_matches(
    candidates: list[dict],
    session_start: datetime,
    session_end: datetime,
) -> list[dict]:
    """Score candidates by time-overlap and return those >= 30%."""
    matches = []
    session_duration = (session_end - session_start).total_seconds()
    if session_duration <= 0:
        session_duration = 3600  # fallback 1 hour

    for workout in candidates:
        try:
            w_start = datetime.fromisoformat(
                str(workout["start_time"]).replace("Z", "+00:00")
            )
            w_end = datetime.fromisoformat(
                str(workout["end_time"]).replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            continue

        if w_start.tzinfo is None:
            w_start = w_start.replace(tzinfo=UTC)
        if w_end.tzinfo is None:
            w_end = w_end.replace(tzinfo=UTC)

        overlap_start = max(session_start, w_start)
        overlap_end = min(session_end, w_end)
        overlap_secs = max(0, (overlap_end - overlap_start).total_seconds())
        workout_duration = (w_end - w_start).total_seconds()
        min_duration = min(session_duration, workout_duration)
        if min_duration <= 0:
            min_duration = session_duration

        overlap_pct = (overlap_secs / min_duration) * 100

        if overlap_pct >= 30:
            workout["overlap_pct"] = round(overlap_pct, 1)
            matches.append(workout)

    matches.sort(key=lambda w: w.get("overlap_pct", 0), reverse=True)
    return matches
