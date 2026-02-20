"""Repository for cached WHOOP workout data."""

import json
from datetime import UTC, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class WhoopWorkoutCacheRepository(BaseRepository):
    """Data access layer for whoop_workout_cache table."""

    @staticmethod
    def upsert(
        user_id: int,
        whoop_workout_id: str,
        start_time: str,
        end_time: str,
        sport_id: int | None = None,
        sport_name: str | None = None,
        timezone_offset: str | None = None,
        strain: float | None = None,
        avg_heart_rate: int | None = None,
        max_heart_rate: int | None = None,
        kilojoules: float | None = None,
        calories: int | None = None,
        score_state: str | None = None,
        zone_durations: dict | None = None,
        raw_data: dict | None = None,
    ) -> int:
        """Insert or update a cached workout. Returns the row ID.

        Uses SELECT-then-INSERT/UPDATE to avoid SQLite lastrowid=0 on upsert.
        """
        zone_durations_str = json.dumps(zone_durations) if zone_durations else None
        raw_data_str = json.dumps(raw_data) if raw_data else None

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if row exists
            cursor.execute(
                convert_query("""
                    SELECT id FROM whoop_workout_cache
                    WHERE user_id = ? AND whoop_workout_id = ?
                    """),
                (user_id, whoop_workout_id),
            )
            existing = cursor.fetchone()

            if existing:
                row_id = existing["id"]
                cursor.execute(
                    convert_query("""
                        UPDATE whoop_workout_cache
                        SET sport_id = ?, sport_name = ?, start_time = ?,
                            end_time = ?, timezone_offset = ?, strain = ?,
                            avg_heart_rate = ?, max_heart_rate = ?,
                            kilojoules = ?, calories = ?, score_state = ?,
                            zone_durations = ?, raw_data = ?,
                            synced_at = ?
                        WHERE id = ?
                        """),
                    (
                        sport_id,
                        sport_name,
                        start_time,
                        end_time,
                        timezone_offset,
                        strain,
                        avg_heart_rate,
                        max_heart_rate,
                        kilojoules,
                        calories,
                        score_state,
                        zone_durations_str,
                        raw_data_str,
                        datetime.now(UTC).isoformat(),
                        row_id,
                    ),
                )
                return row_id
            else:
                return execute_insert(
                    cursor,
                    """
                    INSERT INTO whoop_workout_cache (
                        user_id, whoop_workout_id, sport_id, sport_name,
                        start_time, end_time, timezone_offset, strain,
                        avg_heart_rate, max_heart_rate, kilojoules, calories,
                        score_state, zone_durations, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        whoop_workout_id,
                        sport_id,
                        sport_name,
                        start_time,
                        end_time,
                        timezone_offset,
                        strain,
                        avg_heart_rate,
                        max_heart_rate,
                        kilojoules,
                        calories,
                        score_state,
                        zone_durations_str,
                        raw_data_str,
                    ),
                )

    @staticmethod
    def get_by_user_and_time_range(
        user_id: int, start_dt: str, end_dt: str
    ) -> list[dict]:
        """Get cached workouts for a user within a time range."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM whoop_workout_cache
                    WHERE user_id = ?
                      AND start_time >= ?
                      AND start_time <= ?
                    ORDER BY start_time DESC
                    """),
                (user_id, start_dt, end_dt),
            )
            return [
                WhoopWorkoutCacheRepository._row_to_dict(row)
                for row in cursor.fetchall()
            ]

    @staticmethod
    def link_to_session(workout_cache_id: int, session_id: int) -> bool:
        """Link a cached workout to a session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_workout_cache
                    SET session_id = ?
                    WHERE id = ?
                    """),
                (session_id, workout_cache_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def unlink_session(session_id: int) -> bool:
        """Unlink any cached workouts from a session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_workout_cache
                    SET session_id = NULL
                    WHERE session_id = ?
                    """),
                (session_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_by_session_id(session_id: int) -> dict | None:
        """Get the cached workout linked to a session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM whoop_workout_cache
                    WHERE session_id = ?
                    """),
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return WhoopWorkoutCacheRepository._row_to_dict(row)

    @staticmethod
    def get_by_session_ids(session_ids: list[int]) -> dict[int, dict]:
        """Get cached workouts keyed by session_id for a batch of sessions."""
        if not session_ids:
            return {}
        placeholders = ",".join("?" for _ in session_ids)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT * FROM whoop_workout_cache WHERE session_id IN ({placeholders})"
                ),
                tuple(session_ids),
            )
            rows = cursor.fetchall()
        return {
            row_dict["session_id"]: row_dict
            for row in rows
            if (row_dict := WhoopWorkoutCacheRepository._row_to_dict(row))
            and row_dict.get("session_id")
        }

    @staticmethod
    def delete_by_user(user_id: int) -> int:
        """Delete all cached workouts for a user. Returns count deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM whoop_workout_cache WHERE user_id = ?"),
                (user_id,),
            )
            return cursor.rowcount

    @staticmethod
    def get_unlinked_workouts(user_id: int) -> list[dict]:
        """Get all workouts not yet linked to a session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM whoop_workout_cache
                    WHERE user_id = ? AND session_id IS NULL
                    ORDER BY start_time DESC
                    """),
                (user_id,),
            )
            return [
                WhoopWorkoutCacheRepository._row_to_dict(row)
                for row in cursor.fetchall()
            ]

    @staticmethod
    def exists_by_whoop_id(user_id: int, whoop_workout_id: str) -> bool:
        """Check if a workout exists for user + whoop_workout_id."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT id FROM whoop_workout_cache
                    WHERE user_id = ? AND whoop_workout_id = ?
                """),
                (user_id, whoop_workout_id),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_by_id_and_user(workout_cache_id: int, user_id: int) -> dict | None:
        """Get a cached workout by ID and user_id."""
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
                return None
            return WhoopWorkoutCacheRepository._row_to_dict(row)

    @staticmethod
    def get_linked_sessions_with_tz(user_id: int) -> list[dict]:
        """Get linked workout cache entries with timezone offset."""
        with get_connection() as conn:
            cursor = conn.cursor()
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

        results = []
        for row in rows:
            results.append(dict(row))
        return results

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        d = dict(row)

        # Parse JSON fields
        for field in ("zone_durations", "raw_data"):
            val = d.get(field)
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
