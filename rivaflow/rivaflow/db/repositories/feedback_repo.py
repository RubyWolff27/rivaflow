"""Repository for app feedback data access."""
from datetime import datetime
from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection


class FeedbackRepository:
    """Data access layer for app feedback."""

    @staticmethod
    def create(
        user_id: int,
        category: str,
        message: str,
        subject: str | None = None,
        platform: str | None = None,
        version: str | None = None,
        url: str | None = None,
    ) -> int:
        """Create a new feedback submission."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO app_feedback (
                    user_id, category, subject, message,
                    platform, version, url, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    category,
                    subject,
                    message,
                    platform,
                    version,
                    url,
                    "new",
                    datetime.now(),
                    datetime.now(),
                ),
            )

    @staticmethod
    def get_by_id(feedback_id: int) -> dict[str, Any] | None:
        """Get a feedback submission by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM app_feedback WHERE id = ?"),
                (feedback_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return FeedbackRepository._row_to_dict(row)

    @staticmethod
    def list_all(
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List all feedback submissions with optional filtering."""
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM app_feedback WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(convert_query(query), params)
            rows = cursor.fetchall()
            return [FeedbackRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def list_by_user(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
        """Get all feedback submissions from a specific user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT * FROM app_feedback
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """),
                (user_id, limit),
            )
            rows = cursor.fetchall()
            return [FeedbackRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def update_status(
        feedback_id: int,
        status: str,
        admin_notes: str | None = None,
    ) -> bool:
        """Update the status of a feedback submission."""
        with get_connection() as conn:
            cursor = conn.cursor()

            if status == "resolved":
                cursor.execute(
                    convert_query("""
                        UPDATE app_feedback
                        SET status = ?, admin_notes = ?, resolved_at = ?, updated_at = ?
                        WHERE id = ?
                    """),
                    (status, admin_notes, datetime.now(), datetime.now(), feedback_id),
                )
            else:
                cursor.execute(
                    convert_query("""
                        UPDATE app_feedback
                        SET status = ?, admin_notes = ?, updated_at = ?
                        WHERE id = ?
                    """),
                    (status, admin_notes, datetime.now(), feedback_id),
                )

            return cursor.rowcount > 0

    @staticmethod
    def get_stats() -> dict[str, Any]:
        """Get feedback statistics."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute(convert_query("SELECT COUNT(*) as count FROM app_feedback"))
            total = cursor.fetchone()
            total_count = total["count"] if hasattr(total, "keys") else total[0]

            # Count by status
            cursor.execute(
                convert_query("""
                    SELECT status, COUNT(*) as count
                    FROM app_feedback
                    GROUP BY status
                """)
            )
            status_counts = {}
            for row in cursor.fetchall():
                if hasattr(row, "keys"):
                    status_counts[row["status"]] = row["count"]
                else:
                    status_counts[row[0]] = row[1]

            # Count by category
            cursor.execute(
                convert_query("""
                    SELECT category, COUNT(*) as count
                    FROM app_feedback
                    GROUP BY category
                """)
            )
            category_counts = {}
            for row in cursor.fetchall():
                if hasattr(row, "keys"):
                    category_counts[row["category"]] = row["count"]
                else:
                    category_counts[row[0]] = row[1]

            return {
                "total": total_count,
                "by_status": status_counts,
                "by_category": category_counts,
            }

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert database row to dictionary."""
        if hasattr(row, "keys"):
            return dict(row)
        else:
            # Tuple-based result (SQLite)
            return {
                "id": row[0],
                "user_id": row[1],
                "category": row[2],
                "subject": row[3],
                "message": row[4],
                "platform": row[5],
                "version": row[6],
                "url": row[7],
                "status": row[8],
                "admin_notes": row[9],
                "resolved_at": row[10],
                "created_at": row[11],
                "updated_at": row[12],
            }
