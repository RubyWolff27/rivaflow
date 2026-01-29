"""Repository for daily check-in operations."""
import sqlite3
from datetime import date
from typing import Optional

from rivaflow.db.database import get_connection


class CheckinRepository:
    """Data access layer for daily check-ins."""

    @staticmethod
    def get_checkin(user_id: int, check_date: date) -> Optional[dict]:
        """Get check-in for a specific date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, check_date, checkin_type, rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention, insight_shown,
                       created_at
                FROM daily_checkins
                WHERE user_id = %s AND check_date = %s
                """,
                (user_id, check_date.isoformat())
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
        rest_type: Optional[str] = None,
        rest_note: Optional[str] = None,
        session_id: Optional[int] = None,
        readiness_id: Optional[int] = None,
        tomorrow_intention: Optional[str] = None,
        insight_shown: Optional[str] = None
    ) -> int:
        """Create or update daily check-in."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO daily_checkins (
                    user_id, check_date, checkin_type, rest_type, rest_note,
                    session_id, readiness_id, tomorrow_intention, insight_shown
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(user_id, check_date) DO UPDATE SET
                    checkin_type = excluded.checkin_type,
                    rest_type = excluded.rest_type,
                    rest_note = excluded.rest_note,
                    session_id = excluded.session_id,
                    readiness_id = excluded.readiness_id,
                    tomorrow_intention = excluded.tomorrow_intention,
                    insight_shown = excluded.insight_shown
                """,
                (
                    user_id,
                    check_date.isoformat(),
                    checkin_type,
                    rest_type,
                    rest_note,
                    session_id,
                    readiness_id,
                    tomorrow_intention,
                    insight_shown,
                )
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_checkins_range(user_id: int, start_date: date, end_date: date) -> list[dict]:
        """Get all check-ins in date range."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, check_date, checkin_type, rest_type, rest_note,
                       session_id, readiness_id, tomorrow_intention, insight_shown,
                       created_at
                FROM daily_checkins
                WHERE user_id = %s AND check_date >= %s AND check_date <= %s
                ORDER BY check_date DESC
                """,
                (user_id, start_date.isoformat(), end_date.isoformat())
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def has_checked_in_today(user_id: int) -> bool:
        """Check if user has checked in today."""
        today = date.today()
        checkin = CheckinRepository.get_checkin(user_id, today)
        return checkin is not None

    @staticmethod
    def update_tomorrow_intention(user_id: int, check_date: date, intention: str) -> None:
        """Update tomorrow's intention for a specific date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE daily_checkins
                SET tomorrow_intention = %s
                WHERE user_id = %s AND check_date = %s
                """,
                (intention, user_id, check_date.isoformat())
            )
            conn.commit()
