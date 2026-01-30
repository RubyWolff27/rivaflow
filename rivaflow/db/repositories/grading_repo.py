"""Repository for grading/belt progression data access."""
import sqlite3
from datetime import datetime, date
from typing import List, Optional

from rivaflow.db.database import get_connection, convert_query, execute_insert


class GradingRepository:
    """Data access layer for belt gradings."""

    @staticmethod
    def create(user_id: int, grade: str, date_graded: str, professor: Optional[str] = None, notes: Optional[str] = None) -> dict:
        """Create a new grading entry."""
        with get_connection() as conn:
            cursor = conn.cursor()
            grading_id = execute_insert(
                cursor,
                """
                INSERT INTO gradings (user_id, grade, date_graded, professor, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, grade, date_graded, professor, notes),
            )

            # Return the created grading
            cursor.execute(convert_query("SELECT * FROM gradings WHERE id = ? AND user_id = ?"), (grading_id, user_id))
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row)

    @staticmethod
    def list_all(user_id: int, order_by: str = "date_graded DESC") -> List[dict]:
        """Get all gradings, ordered by date (newest first by default)."""
        # Whitelist allowed ORDER BY values to prevent SQL injection
        allowed_order = {
            "date_graded ASC", "date_graded DESC",
            "grade ASC", "grade DESC",
            "created_at ASC", "created_at DESC"
        }
        if order_by not in allowed_order:
            order_by = "date_graded DESC"  # Safe default

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(f"SELECT * FROM gradings WHERE user_id = ? ORDER BY {order_by}"), (user_id,))
            rows = cursor.fetchall()
            return [GradingRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_latest(user_id: int) -> Optional[dict]:
        """Get the most recent grading."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM gradings WHERE user_id = ? ORDER BY date_graded DESC, id DESC LIMIT 1"),
                (user_id,)
            )
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row) if row else None

    @staticmethod
    def update(
        user_id: int,
        grading_id: int,
        grade: Optional[str] = None,
        date_graded: Optional[str] = None,
        professor: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Update a grading by ID. Returns updated grading or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if grade is not None:
                updates.append("grade = ?")
                params.append(grade)
            if date_graded is not None:
                updates.append("date_graded = ?")
                params.append(date_graded)
            if professor is not None:
                updates.append("professor = ?")
                params.append(professor)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                # Nothing to update, just return the current grading
                cursor.execute(convert_query("SELECT * FROM gradings WHERE id = ? AND user_id = ?"), (grading_id, user_id))
                row = cursor.fetchone()
                return GradingRepository._row_to_dict(row) if row else None

            params.extend([grading_id, user_id])
            query = f"UPDATE gradings SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return None

            # Return updated grading
            cursor.execute(convert_query("SELECT * FROM gradings WHERE id = ? AND user_id = ?"), (grading_id, user_id))
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row) if row else None

    @staticmethod
    def delete(user_id: int, grading_id: int) -> bool:
        """Delete a grading by ID. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM gradings WHERE id = ? AND user_id = ?"), (grading_id, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse date fields
        if data.get("date_graded"):
            data["date_graded"] = date.fromisoformat(data["date_graded"])
        # Parse datetime fields
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
