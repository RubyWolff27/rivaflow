"""Repository for grading/belt progression data access."""
import sqlite3
from datetime import datetime
from typing import List, Optional

from rivaflow.db.database import get_connection


class GradingRepository:
    """Data access layer for belt gradings."""

    @staticmethod
    def create(grade: str, date_graded: str, notes: Optional[str] = None) -> dict:
        """Create a new grading entry."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO gradings (grade, date_graded, notes)
                VALUES (?, ?, ?)
                """,
                (grade, date_graded, notes),
            )
            grading_id = cursor.lastrowid

            # Return the created grading
            cursor.execute("SELECT * FROM gradings WHERE id = ?", (grading_id,))
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row)

    @staticmethod
    def list_all(order_by: str = "date_graded DESC") -> List[dict]:
        """Get all gradings, ordered by date (newest first by default)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM gradings ORDER BY {order_by}")
            rows = cursor.fetchall()
            return [GradingRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_latest() -> Optional[dict]:
        """Get the most recent grading."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM gradings ORDER BY date_graded DESC, id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row) if row else None

    @staticmethod
    def delete(grading_id: int) -> bool:
        """Delete a grading by ID. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM gradings WHERE id = ?", (grading_id,))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse datetime fields
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
