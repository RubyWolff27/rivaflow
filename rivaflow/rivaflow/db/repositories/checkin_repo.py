"""Repository for daily check-in operations."""

import logging
from datetime import date, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection

logger = logging.getLogger(__name__)


class CheckinRepository:
    """Data access layer for daily check-ins."""

    @staticmethod
    def get_checkin(
        user_id: int,
        check_date: date,
        checkin_slot: str = "morning",
    ) -> dict | None:
        """Get check-in for a specific date and slot."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, check_date, checkin_type, checkin_slot,
                       rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention,
                       insight_shown, energy_level, midday_note,
                       training_quality, recovery_note, created_at
                FROM daily_checkins
                WHERE user_id = ? AND check_date = ? AND checkin_slot = ?
                """),
                (user_id, check_date.isoformat(), checkin_slot),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return dict(row)

    @staticmethod
    def upsert_checkin(
        user_id: int,
        check_date: date,
        checkin_type: str,
        checkin_slot: str = "morning",
        rest_type: str | None = None,
        rest_note: str | None = None,
        session_id: int | None = None,
        readiness_id: int | None = None,
        tomorrow_intention: str | None = None,
        insight_shown: str | None = None,
    ) -> int:
        """Create or update daily check-in for a given slot."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id FROM daily_checkins"
                    " WHERE user_id = ? AND check_date = ?"
                    " AND checkin_slot = ?"
                ),
                (user_id, check_date.isoformat(), checkin_slot),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    convert_query("""
                    UPDATE daily_checkins
                    SET checkin_type = ?, rest_type = ?, rest_note = ?,
                        session_id = ?, readiness_id = ?,
                        tomorrow_intention = ?, insight_shown = ?
                    WHERE user_id = ? AND check_date = ?
                          AND checkin_slot = ?
                    """),
                    (
                        checkin_type,
                        rest_type,
                        rest_note,
                        session_id,
                        readiness_id,
                        tomorrow_intention,
                        insight_shown,
                        user_id,
                        check_date.isoformat(),
                        checkin_slot,
                    ),
                )
                return existing["id"]
            else:
                checkin_id = execute_insert(
                    cursor,
                    """
                    INSERT INTO daily_checkins (
                        user_id, check_date, checkin_type, checkin_slot,
                        rest_type, rest_note, session_id, readiness_id,
                        tomorrow_intention, insight_shown
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        check_date.isoformat(),
                        checkin_type,
                        checkin_slot,
                        rest_type,
                        rest_note,
                        session_id,
                        readiness_id,
                        tomorrow_intention,
                        insight_shown,
                    ),
                )
                return checkin_id

    @staticmethod
    def get_checkins_range(user_id: int, start_date: date, end_date: date) -> list[dict]:
        """Get all check-ins in date range (all slots)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, check_date, checkin_type, checkin_slot,
                       rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention,
                       insight_shown, energy_level, midday_note,
                       training_quality, recovery_note, created_at
                FROM daily_checkins
                WHERE user_id = ? AND check_date >= ? AND check_date <= ?
                ORDER BY check_date DESC, checkin_slot
                """),
                (user_id, start_date.isoformat(), end_date.isoformat()),
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def has_checked_in_today(user_id: int) -> bool:
        """Check if user has checked in today (any slot)."""
        today = date.today()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT 1 FROM daily_checkins"
                    " WHERE user_id = ? AND check_date = ?"
                    " LIMIT 1"
                ),
                (user_id, today.isoformat()),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def update_tomorrow_intention(
        user_id: int,
        check_date: date,
        intention: str,
        checkin_slot: str = "morning",
    ) -> None:
        """Update tomorrow's intention for a specific date and slot."""
        with get_connection() as conn:
            cursor = conn.cursor()
            # Try evening slot first, fall back to specified slot
            cursor.execute(
                convert_query(
                    "SELECT id FROM daily_checkins"
                    " WHERE user_id = ? AND check_date = ?"
                    " AND checkin_slot = 'evening'"
                ),
                (user_id, check_date.isoformat()),
            )
            evening = cursor.fetchone()

            target_slot = "evening" if evening else checkin_slot
            cursor.execute(
                convert_query("""
                UPDATE daily_checkins
                SET tomorrow_intention = ?
                WHERE user_id = ? AND check_date = ?
                      AND checkin_slot = ?
                """),
                (intention, user_id, check_date.isoformat(), target_slot),
            )

    @staticmethod
    def get_day_checkins(user_id: int, check_date: date) -> dict:
        """Get all slots for a given day as {morning, midday, evening}."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, check_date, checkin_type, checkin_slot,
                       rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention,
                       insight_shown, energy_level, midday_note,
                       training_quality, recovery_note, created_at
                FROM daily_checkins
                WHERE user_id = ? AND check_date = ?
                ORDER BY checkin_slot
                """),
                (user_id, check_date.isoformat()),
            )
            rows = cursor.fetchall()

            result: dict = {"morning": None, "midday": None, "evening": None}
            for row in rows:
                d = dict(row)
                slot = d.get("checkin_slot", "morning")
                if slot in result:
                    result[slot] = d
            return result

    @staticmethod
    def delete_checkin(user_id: int, checkin_id: int) -> bool:
        """Delete a check-in by ID. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM daily_checkins" " WHERE id = ? AND user_id = ?"),
                (checkin_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_checkin_by_id(user_id: int, checkin_id: int) -> dict | None:
        """Get a single check-in by ID (with ownership check)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, check_date, checkin_type, checkin_slot,
                       rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention,
                       insight_shown, energy_level, midday_note,
                       training_quality, recovery_note, created_at
                FROM daily_checkins
                WHERE id = ? AND user_id = ?
                """),
                (checkin_id, user_id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def upsert_midday(
        user_id: int,
        check_date: date,
        energy_level: int,
        midday_note: str | None = None,
    ) -> int:
        """Create or update midday check-in."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id FROM daily_checkins"
                    " WHERE user_id = ? AND check_date = ?"
                    " AND checkin_slot = 'midday'"
                ),
                (user_id, check_date.isoformat()),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    convert_query("""
                    UPDATE daily_checkins
                    SET energy_level = ?, midday_note = ?
                    WHERE id = ?
                    """),
                    (energy_level, midday_note, existing["id"]),
                )
                return existing["id"]
            else:
                checkin_id = execute_insert(
                    cursor,
                    """
                    INSERT INTO daily_checkins (
                        user_id, check_date, checkin_type, checkin_slot,
                        energy_level, midday_note, created_at
                    )
                    VALUES (?, ?, 'midday', 'midday', ?, ?, ?)
                    """,
                    (
                        user_id,
                        check_date.isoformat(),
                        energy_level,
                        midday_note,
                        datetime.now().isoformat(),
                    ),
                )
                return checkin_id

    @staticmethod
    def upsert_evening(
        user_id: int,
        check_date: date,
        training_quality: int | None = None,
        recovery_note: str | None = None,
        tomorrow_intention: str | None = None,
        did_not_train: bool = False,
        rest_type: str | None = None,
        rest_note: str | None = None,
    ) -> int:
        """Create or update evening check-in."""
        checkin_type = "rest" if did_not_train else "evening"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT id FROM daily_checkins"
                    " WHERE user_id = ? AND check_date = ?"
                    " AND checkin_slot = 'evening'"
                ),
                (user_id, check_date.isoformat()),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    convert_query("""
                    UPDATE daily_checkins
                    SET checkin_type = ?, training_quality = ?,
                        recovery_note = ?, tomorrow_intention = ?,
                        rest_type = ?, rest_note = ?
                    WHERE id = ?
                    """),
                    (
                        checkin_type,
                        training_quality,
                        recovery_note,
                        tomorrow_intention,
                        rest_type if did_not_train else None,
                        rest_note if did_not_train else None,
                        existing["id"],
                    ),
                )
                return existing["id"]
            else:
                checkin_id = execute_insert(
                    cursor,
                    """
                    INSERT INTO daily_checkins (
                        user_id, check_date, checkin_type, checkin_slot,
                        training_quality, recovery_note,
                        tomorrow_intention, rest_type, rest_note,
                        created_at
                    )
                    VALUES (?, ?, ?, 'evening', ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        check_date.isoformat(),
                        checkin_type,
                        training_quality,
                        recovery_note,
                        tomorrow_intention,
                        rest_type if did_not_train else None,
                        rest_note if did_not_train else None,
                        datetime.now().isoformat(),
                    ),
                )
                return checkin_id
