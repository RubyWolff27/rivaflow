"""Repository for session data access."""
import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from rivaflow.db.database import get_connection


class SessionRepository:
    """Data access layer for training sessions."""

    @staticmethod
    def create(
        session_date: date,
        class_type: str,
        gym_name: str,
        location: Optional[str] = None,
        duration_mins: int = 60,
        intensity: int = 4,
        rolls: int = 0,
        submissions_for: int = 0,
        submissions_against: int = 0,
        partners: Optional[list[str]] = None,
        techniques: Optional[list[str]] = None,
        notes: Optional[str] = None,
        visibility_level: str = "private",
    ) -> int:
        """Create a new session and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (
                    session_date, class_type, gym_name, location,
                    duration_mins, intensity, rolls,
                    submissions_for, submissions_against,
                    partners, techniques, notes, visibility_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_date.isoformat(),
                    class_type,
                    gym_name,
                    location,
                    duration_mins,
                    intensity,
                    rolls,
                    submissions_for,
                    submissions_against,
                    json.dumps(partners) if partners else None,
                    json.dumps(techniques) if techniques else None,
                    notes,
                    visibility_level,
                ),
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_id(session_id: int) -> Optional[dict]:
        """Get a session by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return SessionRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_date_range(start_date: date, end_date: date) -> list[dict]:
        """Get all sessions within a date range (inclusive)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM sessions
                WHERE session_date BETWEEN ? AND ?
                ORDER BY session_date DESC
                """,
                (start_date.isoformat(), end_date.isoformat()),
            )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_recent(limit: int = 10) -> list[dict]:
        """Get most recent sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions ORDER BY session_date DESC LIMIT ?", (limit,)
            )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_unique_gyms() -> list[str]:
        """Get list of unique gym names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT gym_name FROM sessions ORDER BY gym_name"
            )
            return [row["gym_name"] for row in cursor.fetchall()]

    @staticmethod
    def get_unique_locations() -> list[str]:
        """Get list of unique locations from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT location FROM sessions
                WHERE location IS NOT NULL
                ORDER BY location
                """
            )
            return [row["location"] for row in cursor.fetchall()]

    @staticmethod
    def get_unique_partners() -> list[str]:
        """Get list of unique partner names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT partners FROM sessions WHERE partners IS NOT NULL")
            partners_set = set()
            for row in cursor.fetchall():
                partners_list = json.loads(row["partners"])
                partners_set.update(partners_list)
            return sorted(partners_set)

    @staticmethod
    def get_last_n_sessions_by_type(n: int = 5) -> dict[str, list[str]]:
        """Get the class types of the last N sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT class_type FROM sessions
                ORDER BY session_date DESC, created_at DESC
                LIMIT ?
                """,
                (n,),
            )
            return [row["class_type"] for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse JSON fields
        if data.get("partners"):
            data["partners"] = json.loads(data["partners"])
        if data.get("techniques"):
            data["techniques"] = json.loads(data["techniques"])
        # Parse dates
        if data.get("session_date"):
            data["session_date"] = date.fromisoformat(data["session_date"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return data
