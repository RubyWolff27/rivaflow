"""Business logic for WHOOP integration — OAuth, sync, and matching."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.whoop_client import WhoopClient
from rivaflow.core.utils.encryption import decrypt_token, encrypt_token
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.whoop_connection_repo import (
    WhoopConnectionRepository,
)
from rivaflow.db.repositories.whoop_oauth_state_repo import (
    WhoopOAuthStateRepository,
)
from rivaflow.db.repositories.whoop_workout_cache_repo import (
    WhoopWorkoutCacheRepository,
)

logger = logging.getLogger(__name__)


class WhoopService:
    """Central service for WHOOP integration logic."""

    def __init__(self):
        self.connection_repo = WhoopConnectionRepository()
        self.state_repo = WhoopOAuthStateRepository()
        self.workout_cache_repo = WhoopWorkoutCacheRepository()
        self.session_repo = SessionRepository()
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

        return {
            "total_fetched": len(all_workouts),
            "created": created,
            "updated": updated,
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

        # Delete cached workouts
        self.workout_cache_repo.delete_by_user(user_id)

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
