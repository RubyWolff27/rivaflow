"""Repository for readiness check-in data access."""
import sqlite3
from datetime import date, datetime
from typing import Optional

from rivaflow.db.database import get_connection, convert_query, execute_insert


class ReadinessRepository:
    """Data access layer for daily readiness check-ins."""

    @staticmethod
    def upsert(
        user_id: int,
        check_date: date,
        sleep: int,
        stress: int,
        soreness: int,
        energy: int,
        hotspot_note: Optional[str] = None,
        weight_kg: Optional[float] = None,
    ) -> int:
        """Create or update readiness entry for a date. Returns ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            # Try to get existing entry
            cursor.execute(
                convert_query("SELECT id FROM readiness WHERE user_id = ? AND check_date = ?"),
                (user_id, check_date.isoformat()),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute(
                convert_query("""
                    UPDATE readiness
                    SET sleep = ?, stress = ?, soreness = ?, energy = ?,
                        hotspot_note = ?, weight_kg = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND check_date = ?
                    """),
                    (sleep, stress, soreness, energy, hotspot_note, weight_kg, user_id, check_date.isoformat()),
                )
                return existing["id"]
            else:
                # Insert new
                return execute_insert(
                    cursor,
                    """
                    INSERT INTO readiness (
                        user_id, check_date, sleep, stress, soreness, energy, hotspot_note, weight_kg
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, check_date.isoformat(), sleep, stress, soreness, energy, hotspot_note, weight_kg),
                )

    @staticmethod
    def get_by_date(user_id: int, check_date: date) -> Optional[dict]:
        """Get readiness entry for a specific date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM readiness WHERE user_id = ? AND check_date = ?"),
                (user_id, check_date.isoformat()),
            )
            row = cursor.fetchone()
            if row:
                return ReadinessRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_latest(user_id: int) -> Optional[dict]:
        """Get the most recent readiness entry."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM readiness WHERE user_id = ? ORDER BY check_date DESC LIMIT 1"),
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return ReadinessRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_id_any_user(readiness_id: int) -> Optional[dict]:
        """Get a readiness entry by ID without user scope (for validation/privacy checks)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM readiness WHERE id = ?"), (readiness_id,))
            row = cursor.fetchone()
            if row:
                return ReadinessRepository._row_to_dict(row)
            return None

    @staticmethod
    def get_by_date_range(user_id: int, start_date: date, end_date: date) -> list[dict]:
        """Get readiness entries within a date range (inclusive)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM readiness
                WHERE user_id = ? AND check_date BETWEEN ? AND ?
                ORDER BY check_date DESC
                """),
                (user_id, start_date.isoformat(), end_date.isoformat()),
            )
            return [ReadinessRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse dates - handle both PostgreSQL (date/datetime) and SQLite (string)
        if data.get("check_date") and isinstance(data["check_date"], str):
            data["check_date"] = date.fromisoformat(data["check_date"])
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at") and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        # Calculate composite score
        data["composite_score"] = (
            data["sleep"] + (6 - data["stress"]) + (6 - data["soreness"]) + data["energy"]
        )
        return data
