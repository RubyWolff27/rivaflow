"""Business logic for WHOOP integration — OAuth, sync, and matching."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from datetime import timezone as tz

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.whoop_client import WHOOP_SCOPES, WhoopClient
from rivaflow.core.utils.encryption import decrypt_token, encrypt_token
from rivaflow.db.repositories.profile_repo import ProfileRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.whoop_connection_repo import (
    WhoopConnectionRepository,
)
from rivaflow.db.repositories.whoop_oauth_state_repo import (
    WhoopOAuthStateRepository,
)
from rivaflow.db.repositories.whoop_recovery_cache_repo import (
    WhoopRecoveryCacheRepository,
)
from rivaflow.db.repositories.whoop_workout_cache_repo import (
    WhoopWorkoutCacheRepository,
)

logger = logging.getLogger(__name__)


def _parse_tz_offset(offset_str: str | None) -> tz | None:
    """Parse a timezone offset string like '+11:00' into a timezone."""
    if not offset_str:
        return None
    try:
        sign = 1 if offset_str.startswith("+") else -1
        parts = offset_str.lstrip("+-").split(":")
        hours = int(parts[0])
        mins = int(parts[1]) if len(parts) > 1 else 0
        return tz(timedelta(hours=sign * hours, minutes=sign * mins))
    except (ValueError, IndexError):
        return None


class WhoopService:
    """Central service for WHOOP integration logic."""

    def __init__(self):
        self.connection_repo = WhoopConnectionRepository()
        self.state_repo = WhoopOAuthStateRepository()
        self.workout_cache_repo = WhoopWorkoutCacheRepository()
        self.recovery_cache_repo = WhoopRecoveryCacheRepository()
        self.session_repo = SessionRepository()
        self.profile_repo = ProfileRepository()
        self.client = WhoopClient()

    # =========================================================================
    # OAuth
    # =========================================================================

    def initiate_oauth(self, user_id: int) -> str:
        """Generate a state token, persist it, and return the auth URL."""
        state_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()

        self.state_repo.create(user_id, state_token, expires_at)
        self.state_repo.cleanup_expired()

        return self.client.get_authorization_url(state_token)

    def handle_callback(self, code: str, state: str) -> dict:
        """Process the OAuth callback: validate state, exchange code, store."""
        state_row = self.state_repo.validate_and_consume(state)
        if not state_row:
            raise ValidationError("Invalid or expired OAuth state token")

        user_id = state_row["user_id"]

        # Exchange code for tokens
        token_data = self.client.exchange_code(code)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_in)
        ).isoformat()
        scopes = token_data.get("scope", "")

        # Get WHOOP user profile
        profile = self.client.get_profile(access_token)
        whoop_user_id = str(profile.get("user_id", ""))

        # Encrypt and store
        self.connection_repo.upsert(
            user_id=user_id,
            access_token_encrypted=encrypt_token(access_token),
            refresh_token_encrypted=encrypt_token(refresh_token),
            token_expires_at=token_expires_at,
            whoop_user_id=whoop_user_id,
            scopes=scopes,
        )

        return {
            "user_id": user_id,
            "whoop_user_id": whoop_user_id,
            "connected": True,
        }

    def get_valid_access_token(self, user_id: int) -> str:
        """Return a valid (possibly refreshed) access token for the user."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn:
            raise NotFoundError("WHOOP not connected")

        access_token = decrypt_token(conn["access_token_encrypted"])
        expires_at_str = conn["token_expires_at"]

        # Parse expiry
        if isinstance(expires_at_str, str):
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        else:
            expires_at = expires_at_str

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        # Refresh if within 5-minute buffer
        if expires_at < datetime.now(UTC) + timedelta(minutes=5):
            refresh_token = decrypt_token(conn["refresh_token_encrypted"])
            token_data = self.client.refresh_tokens(refresh_token)

            new_access = token_data["access_token"]
            new_refresh = token_data.get("refresh_token", refresh_token)
            new_expires = (
                datetime.now(UTC)
                + timedelta(seconds=token_data.get("expires_in", 3600))
            ).isoformat()

            self.connection_repo.update_tokens(
                user_id,
                encrypt_token(new_access),
                encrypt_token(new_refresh),
                new_expires,
            )
            return new_access

        return access_token

    # =========================================================================
    # Sync
    # =========================================================================

    def sync_workouts(self, user_id: int, days_back: int = 7) -> dict:
        """Fetch workouts from WHOOP API and cache them locally."""
        access_token = self.get_valid_access_token(user_id)

        start = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
        end = datetime.now(UTC).isoformat()

        all_workouts = []
        next_token = None

        # Paginate through results
        while True:
            data = self.client.get_workouts(
                access_token, start=start, end=end, next_token=next_token
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
                from rivaflow.db.database import convert_query, get_connection

                with get_connection() as conn_db:
                    cursor = conn_db.cursor()
                    cursor.execute(
                        convert_query("""
                            SELECT id FROM whoop_workout_cache
                            WHERE user_id = ? AND whoop_workout_id = ?
                            """),
                        (user_id, whoop_workout_id),
                    )
                    existing = cursor.fetchone()
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

    # =========================================================================
    # Recovery sync
    # =========================================================================

    def sync_recovery(self, user_id: int, days_back: int = 7) -> dict:
        """Fetch recovery/sleep data from WHOOP and cache locally."""
        access_token = self.get_valid_access_token(user_id)

        start = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
        end = datetime.now(UTC).isoformat()

        all_cycles = []
        next_token = None

        # Paginate through cycles
        while True:
            data = self.client.get_cycles(
                access_token, start=start, end=end, next_token=next_token
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
                access_token, start=start, end=end, next_token=next_token
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
                access_token, start=start, end=end, next_token=next_token
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
                from rivaflow.db.database import convert_query, get_connection

                with get_connection() as conn_db:
                    cursor = conn_db.cursor()
                    cursor.execute(
                        convert_query(
                            "SELECT id FROM whoop_recovery_cache "
                            "WHERE user_id = ? AND whoop_cycle_id = ?"
                        ),
                        (user_id, cycle_id),
                    )
                    existing = cursor.fetchone()
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

    def get_latest_recovery(self, user_id: int) -> dict | None:
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

        # Cache empty or stale — sync recent data
        try:
            self.sync_recovery(user_id, days_back=2)
        except Exception:
            logger.warning("Auto recovery sync failed", exc_info=True)

        return self.recovery_cache_repo.get_latest(user_id)

    def apply_recovery_to_readiness(self, user_id: int, check_date: str) -> dict | None:
        """Map WHOOP recovery to readiness auto-fill values.

        Returns suggested readiness fields or None if no data available.
        Does NOT auto-save — the frontend controls when to save.
        """
        # Look for recovery matching the check_date or the day before
        # (WHOOP cycles are overnight, so today's recovery is from
        # last night's sleep)
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

    def check_scope_compatibility(self, user_id: int) -> dict:
        """Compare stored scopes with current required scopes."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn:
            return {
                "current_scopes": [],
                "required_scopes": WHOOP_SCOPES.split(),
                "needs_reauth": True,
                "missing_scopes": WHOOP_SCOPES.split(),
            }

        current_str = conn.get("scopes", "") or ""
        current = set(current_str.split())
        required = set(WHOOP_SCOPES.split())
        missing = required - current

        return {
            "current_scopes": sorted(current),
            "required_scopes": sorted(required),
            "needs_reauth": len(missing) > 0,
            "missing_scopes": sorted(missing),
        }

    # =========================================================================
    # Matching
    # =========================================================================

    def find_matching_workouts(self, user_id: int, session_id: int) -> list[dict]:
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

        session_start = datetime(
            date_part.year,
            date_part.month,
            date_part.day,
            hour,
            minute,
            tzinfo=UTC,
        )
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
                logger.warning("Auto-sync failed during matching", exc_info=True)
                return []

        # Calculate overlap
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

    def find_matching_workouts_by_params(
        self,
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
                logger.warning("Auto-sync failed during matching", exc_info=True)
                return []

        matches = []
        session_duration = (session_end - session_start).total_seconds()
        if session_duration <= 0:
            session_duration = 3600

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

    def apply_workout_to_session(
        self, user_id: int, session_id: int, workout_cache_id: int
    ) -> dict:
        """Apply cached WHOOP data to a session's WHOOP fields."""
        session = self.session_repo.get_by_id(user_id, session_id)
        if not session:
            raise NotFoundError("Session not found")

        # Get the cached workout (raw query since we need by ID + user)
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM whoop_workout_cache
                    WHERE id = ? AND user_id = ?
                    """),
                (workout_cache_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                raise NotFoundError("Workout not found in cache")
            workout = self.workout_cache_repo._row_to_dict(row)

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

        return self.session_repo.get_by_id(user_id, session_id)

    # =========================================================================
    # Auto-create sessions
    # =========================================================================

    def auto_create_sessions_for_workouts(self, user_id: int) -> list[int]:
        """Auto-create sessions from unlinked BJJ WHOOP workouts.

        Returns list of created session IDs.
        """
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
            default_class_type = (
                profile.get("primary_training_type") or default_class_type
            )

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
            except Exception:
                logger.warning(
                    "Failed to auto-create session for workout %s",
                    workout.get("id"),
                    exc_info=True,
                )

        return created_ids

    def backfill_session_timezones(self, user_id: int) -> int:
        """Fix UTC times on existing auto-created sessions.

        Looks up linked WHOOP workouts, applies timezone_offset to
        recalculate class_time and session_date. Returns count fixed.
        """
        from rivaflow.db.database import convert_query, get_connection

        fixed = 0
        with get_connection() as conn:
            cursor = conn.cursor()
            # Find auto-created sessions with linked workouts
            cursor.execute(
                convert_query(
                    "SELECT wc.session_id, wc.start_time, "
                    "wc.timezone_offset "
                    "FROM whoop_workout_cache wc "
                    "WHERE wc.user_id = ? AND wc.session_id IS NOT NULL "
                    "AND wc.timezone_offset IS NOT NULL"
                ),
                (user_id,),
            )
            rows = cursor.fetchall()

        for row in rows:
            row_d = (
                dict(row)
                if hasattr(row, "keys")
                else {
                    "session_id": row[0],
                    "start_time": row[1],
                    "timezone_offset": row[2],
                }
            )
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

    def set_auto_create_sessions(self, user_id: int, enabled: bool) -> dict:
        """Toggle auto-create and backfill if enabling."""
        self.connection_repo.update_auto_create(user_id, enabled)

        backfilled = 0
        if enabled:
            created_ids = self.auto_create_sessions_for_workouts(user_id)
            backfilled = len(created_ids)

        return {
            "auto_create_sessions": enabled,
            "backfilled": backfilled,
        }

    # =========================================================================
    # Connection management
    # =========================================================================

    def get_connection_status(self, user_id: int) -> dict:
        """Return connection status with metadata."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn or not conn.get("is_active"):
            return {"connected": False}

        return {
            "connected": True,
            "whoop_user_id": conn.get("whoop_user_id"),
            "connected_at": conn.get("connected_at"),
            "last_synced_at": conn.get("last_synced_at"),
            "auto_create_sessions": bool(conn.get("auto_create_sessions")),
        }

    def disconnect(self, user_id: int) -> bool:
        """Disconnect WHOOP: revoke tokens, delete connection + cache."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if conn:
            # Best-effort token revocation
            try:
                access_token = decrypt_token(conn["access_token_encrypted"])
                self.client.revoke_access(access_token)
            except Exception:
                logger.warning("Token revocation failed (best-effort)")

        # Delete cached workouts and recovery data
        self.workout_cache_repo.delete_by_user(user_id)
        self.recovery_cache_repo.delete_by_user(user_id)

        # Delete connection
        self.connection_repo.delete(user_id)

        # Clear WHOOP fields from linked sessions
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as db_conn:
            cursor = db_conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE sessions
                    SET whoop_strain = NULL,
                        whoop_calories = NULL,
                        whoop_avg_hr = NULL,
                        whoop_max_hr = NULL
                    WHERE user_id = ?
                      AND (whoop_strain IS NOT NULL
                           OR whoop_calories IS NOT NULL
                           OR whoop_avg_hr IS NOT NULL
                           OR whoop_max_hr IS NOT NULL)
                    """),
                (user_id,),
            )

        return True
