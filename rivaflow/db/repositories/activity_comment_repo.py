"""Repository for activity comments data access."""
import sqlite3
from typing import List, Optional

from rivaflow.db.database import get_connection


class ActivityCommentRepository:
    """Data access layer for activity comments (polymorphic across activity types)."""

    @staticmethod
    def create(
        user_id: int,
        activity_type: str,
        activity_id: int,
        comment_text: str,
        parent_comment_id: Optional[int] = None,
    ) -> dict:
        """
        Create a comment on an activity.

        Args:
            user_id: User who is commenting
            activity_type: Type of activity ('session', 'readiness', 'rest')
            activity_id: ID of the activity
            comment_text: The comment text (1-1000 characters)
            parent_comment_id: Optional parent comment ID for nested replies

        Returns:
            The created comment

        Raises:
            sqlite3.IntegrityError: If comment_text violates constraints
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO activity_comments
                (user_id, activity_type, activity_id, comment_text, parent_comment_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, activity_type, activity_id, comment_text, parent_comment_id),
            )
            comment_id = cursor.lastrowid

            cursor.execute("SELECT * FROM activity_comments WHERE id = %s", (comment_id,))
            row = cursor.fetchone()
            return ActivityCommentRepository._row_to_dict(row)

    @staticmethod
    def get_by_activity(activity_type: str, activity_id: int) -> List[dict]:
        """
        Get all comments for an activity with user information.

        Args:
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            List of comments with user info, ordered by creation date
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    ac.id,
                    ac.user_id,
                    ac.activity_type,
                    ac.activity_id,
                    ac.comment_text,
                    ac.parent_comment_id,
                    ac.edited_at,
                    ac.created_at,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM activity_comments ac
                JOIN users u ON ac.user_id = u.id
                WHERE ac.activity_type = %s AND ac.activity_id = %s
                ORDER BY ac.created_at ASC
                """,
                (activity_type, activity_id),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(comment_id: int) -> Optional[dict]:
        """
        Get a comment by ID.

        Args:
            comment_id: The comment ID

        Returns:
            The comment or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    ac.id,
                    ac.user_id,
                    ac.activity_type,
                    ac.activity_id,
                    ac.comment_text,
                    ac.parent_comment_id,
                    ac.edited_at,
                    ac.created_at,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM activity_comments ac
                JOIN users u ON ac.user_id = u.id
                WHERE ac.id = %s
                """,
                (comment_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update(comment_id: int, user_id: int, comment_text: str) -> Optional[dict]:
        """
        Update a comment (user can only update their own comments).

        Args:
            comment_id: The comment ID to update
            user_id: User attempting the update (must be comment owner)
            comment_text: New comment text

        Returns:
            Updated comment or None if not found or user doesn't own it
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE activity_comments
                SET comment_text = %s, edited_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                """,
                (comment_text, comment_id, user_id),
            )

            if cursor.rowcount == 0:
                return None

            return ActivityCommentRepository.get_by_id(comment_id)

    @staticmethod
    def delete(comment_id: int, user_id: int) -> bool:
        """
        Delete a comment (user can only delete their own comments).

        Args:
            comment_id: The comment ID to delete
            user_id: User attempting the deletion (must be comment owner)

        Returns:
            True if deleted, False if not found or user doesn't own it
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM activity_comments
                WHERE id = %s AND user_id = %s
                """,
                (comment_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_comment_count(activity_type: str, activity_id: int) -> int:
        """
        Get the count of comments for an activity.

        Args:
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            Number of comments
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM activity_comments
                WHERE activity_type = %s AND activity_id = %s
                """,
                (activity_type, activity_id),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    @staticmethod
    def get_by_user(user_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        """
        Get all comments by a user.

        Args:
            user_id: User whose comments to retrieve
            limit: Maximum number of comments to return
            offset: Number of comments to skip

        Returns:
            List of comments with activity info
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM activity_comments
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()
            return [ActivityCommentRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}
        return dict(row)
