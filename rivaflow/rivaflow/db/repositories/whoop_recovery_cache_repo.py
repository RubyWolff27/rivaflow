"""Repository for cached WHOOP recovery/sleep cycle data."""

import json
from datetime import UTC, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


class WhoopRecoveryCacheRepository:
    """Data access layer for whoop_recovery_cache table."""

    @staticmethod
    def upsert(
        user_id: int,
        whoop_cycle_id: str,
        recovery_score: float | None = None,
        resting_hr: float | None = None,
        hrv_ms: float | None = None,
        spo2: float | None = None,
        skin_temp: float | None = None,
        sleep_performance: float | None = None,
        sleep_duration_ms: int | None = None,
        sleep_need_ms: int | None = None,
        sleep_debt_ms: int | None = None,
        light_sleep_ms: int | None = None,
        slow_wave_ms: int | None = None,
        rem_sleep_ms: int | None = None,
        awake_ms: int | None = None,
        cycle_start: str = "",
        cycle_end: str | None = None,
        raw_data: dict | None = None,
    ) -> int:
        """Insert or update a cached recovery cycle. Returns the row ID.

        Uses SELECT-then-INSERT/UPDATE to avoid SQLite lastrowid=0 on upsert.
        """
        raw_data_str = json.dumps(raw_data) if raw_data else None

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if row exists
            cursor.execute(
                convert_query(
                    "SELECT id FROM whoop_recovery_cache "
                    "WHERE user_id = ? AND whoop_cycle_id = ?"
                ),
                (user_id, whoop_cycle_id),
            )
            existing = cursor.fetchone()

            if existing:
                row_id = existing["id"] if hasattr(existing, "keys") else existing[0]
                cursor.execute(
                    convert_query("""
                        UPDATE whoop_recovery_cache
                        SET recovery_score = ?, resting_hr = ?, hrv_ms = ?,
                            spo2 = ?, skin_temp = ?, sleep_performance = ?,
                            sleep_duration_ms = ?, sleep_need_ms = ?,
                            sleep_debt_ms = ?, light_sleep_ms = ?,
                            slow_wave_ms = ?, rem_sleep_ms = ?,
                            awake_ms = ?, cycle_start = ?,
                            cycle_end = ?, raw_data = ?,
                            synced_at = ?
                        WHERE id = ?
                    """),
                    (
                        recovery_score,
                        resting_hr,
                        hrv_ms,
                        spo2,
                        skin_temp,
                        sleep_performance,
                        sleep_duration_ms,
                        sleep_need_ms,
                        sleep_debt_ms,
                        light_sleep_ms,
                        slow_wave_ms,
                        rem_sleep_ms,
                        awake_ms,
                        cycle_start,
                        cycle_end,
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
                    INSERT INTO whoop_recovery_cache (
                        user_id, whoop_cycle_id, recovery_score,
                        resting_hr, hrv_ms, spo2, skin_temp,
                        sleep_performance, sleep_duration_ms,
                        sleep_need_ms, sleep_debt_ms,
                        light_sleep_ms, slow_wave_ms,
                        rem_sleep_ms, awake_ms,
                        cycle_start, cycle_end, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        whoop_cycle_id,
                        recovery_score,
                        resting_hr,
                        hrv_ms,
                        spo2,
                        skin_temp,
                        sleep_performance,
                        sleep_duration_ms,
                        sleep_need_ms,
                        sleep_debt_ms,
                        light_sleep_ms,
                        slow_wave_ms,
                        rem_sleep_ms,
                        awake_ms,
                        cycle_start,
                        cycle_end,
                        raw_data_str,
                    ),
                )

    @staticmethod
    def get_latest(user_id: int) -> dict | None:
        """Get the most recent recovery entry by cycle_start."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM whoop_recovery_cache "
                    "WHERE user_id = ? "
                    "ORDER BY cycle_start DESC LIMIT 1"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return WhoopRecoveryCacheRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_date_range(user_id: int, start_dt: str, end_dt: str) -> list[dict]:
        """Get cached recovery data within a date range."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM whoop_recovery_cache
                    WHERE user_id = ?
                      AND cycle_start >= ?
                      AND cycle_start <= ?
                    ORDER BY cycle_start DESC
                """),
                (user_id, start_dt, end_dt),
            )
            return [
                WhoopRecoveryCacheRepository._row_to_dict(row)
                for row in cursor.fetchall()
            ]

    @staticmethod
    def delete_by_user(user_id: int) -> int:
        """Delete all cached recovery data for a user. Returns count deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM whoop_recovery_cache WHERE user_id = ?"),
                (user_id,),
            )
            return cursor.rowcount

    @staticmethod
    def exists_by_cycle_id(user_id: int, whoop_cycle_id: str) -> bool:
        """Check if a recovery entry exists for user + cycle_id."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id FROM whoop_recovery_cache "
                    "WHERE user_id = ? AND whoop_cycle_id = ?"
                ),
                (user_id, whoop_cycle_id),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        d = dict(row)

        # Parse JSON fields
        val = d.get("raw_data")
        if isinstance(val, str):
            try:
                d["raw_data"] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass

        return d
