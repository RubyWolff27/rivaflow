"""Repository for grading/belt progression data access."""

import sqlite3
from datetime import date, datetime

from rivaflow.core.constants import GRADING_SORT_OPTIONS
from rivaflow.db.database import convert_query, execute_insert, get_connection


class GradingRepository:
    """Data access layer for belt gradings."""

    @staticmethod
    def create(
        user_id: int,
        grade: str,
        date_graded: str,
        professor: str | None = None,
        instructor_id: int | None = None,
        notes: str | None = None,
        photo_url: str | None = None,
    ) -> dict:
        """Create a new grading entry."""
        with get_connection() as conn:
            cursor = conn.cursor()
            grading_id = execute_insert(
                cursor,
                """
                INSERT INTO gradings (user_id, grade, date_graded, professor, instructor_id, notes, photo_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    grade,
                    date_graded,
                    professor,
                    instructor_id,
                    notes,
                    photo_url,
                ),
            )

            # Return the created grading
            cursor.execute(
                convert_query("SELECT * FROM gradings WHERE id = ? AND user_id = ?"),
                (grading_id, user_id),
            )
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row)

    @staticmethod
    def list_all(user_id: int, order_by: str = "date_graded DESC") -> list[dict]:
        """Get all gradings, ordered by date (newest first by default)."""
        # Whitelist allowed ORDER BY values to prevent SQL injection
        if order_by not in GRADING_SORT_OPTIONS:
            order_by = "date_graded DESC"  # Safe default

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT * FROM gradings WHERE user_id = ? ORDER BY {order_by}"
                ),
                (user_id,),
            )
            rows = cursor.fetchall()
            return [GradingRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_latest(user_id: int) -> dict | None:
        """Get the most recent grading."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM gradings WHERE user_id = ? ORDER BY date_graded DESC, id DESC LIMIT 1"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row) if row else None

    @staticmethod
    def update(
        user_id: int,
        grading_id: int,
        grade: str | None = None,
        date_graded: str | None = None,
        professor: str | None = None,
        instructor_id: int | None = None,
        notes: str | None = None,
        photo_url: str | None = None,
    ) -> dict | None:
        """Update a grading by ID. Returns updated grading or None if not found."""
        # Valid fields that can be updated (whitelist for SQL safety)
        valid_update_fields = {
            "grade",
            "date_graded",
            "professor",
            "instructor_id",
            "notes",
            "photo_url",
        }

        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query — all field names validated against whitelist
            updates = []
            params = []

            field_values = {
                "grade": grade,
                "date_graded": date_graded,
                "professor": professor,
                "instructor_id": instructor_id,
                "notes": notes,
                "photo_url": photo_url,
            }

            for field, value in field_values.items():
                if field not in valid_update_fields:
                    raise ValueError(f"Invalid field: {field}")
                if value is not None:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if not updates:
                # Nothing to update, just return the current grading
                cursor.execute(
                    convert_query(
                        "SELECT * FROM gradings WHERE id = ? AND user_id = ?"
                    ),
                    (grading_id, user_id),
                )
                row = cursor.fetchone()
                return GradingRepository._row_to_dict(row) if row else None

            params.extend([grading_id, user_id])
            query = (
                f"UPDATE gradings SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            )
            cursor.execute(convert_query(query), params)

            if cursor.rowcount == 0:
                return None

            # Return updated grading
            cursor.execute(
                convert_query("SELECT * FROM gradings WHERE id = ? AND user_id = ?"),
                (grading_id, user_id),
            )
            row = cursor.fetchone()
            return GradingRepository._row_to_dict(row) if row else None

    @staticmethod
    def delete(user_id: int, grading_id: int) -> bool:
        """Delete a grading by ID. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM gradings WHERE id = ? AND user_id = ?"),
                (grading_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse date fields - handle both PostgreSQL (date/datetime) and SQLite (string)
        if data.get("date_graded") and isinstance(data["date_graded"], str):
            data["date_graded"] = date.fromisoformat(data["date_graded"])
        # Parse datetime fields
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return data
