"""Repository for activity likes data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class ActivityLikeRepository(BaseRepository):
    """Data access layer for activity likes (polymorphic across activity types)."""

    @staticmethod
    def create(user_id: int, activity_type: str, activity_id: int) -> dict:
        """
        Create a like on an activity.

        Args:
            user_id: User who is liking
            activity_type: Type of activity ('session', 'readiness', 'rest')
            activity_id: ID of the activity

        Returns:
            The created like

        Raises:
            sqlite3.IntegrityError: If user has already liked this activity
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            like_id = execute_insert(
                cursor,
                """
                INSERT INTO activity_likes (user_id, activity_type, activity_id)
                VALUES (?, ?, ?)
                """,
                (user_id, activity_type, activity_id),
            )

            cursor.execute(
                convert_query("SELECT * FROM activity_likes WHERE id = ?"), (like_id,)
            )
            row = cursor.fetchone()
            return ActivityLikeRepository._row_to_dict(row)

    @staticmethod
    def delete(user_id: int, activity_type: str, activity_id: int) -> bool:
        """
        Remove a like from an activity.

        Args:
            user_id: User who is unliking
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            True if like was deleted, False if it didn't exist
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                DELETE FROM activity_likes
                WHERE user_id = ? AND activity_type = ? AND activity_id = ?
                """),
                (user_id, activity_type, activity_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_like_count(activity_type: str, activity_id: int) -> int:
        """
        Get the count of likes for an activity.

        Args:
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            Number of likes
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT COUNT(*) as count
                FROM activity_likes
                WHERE activity_type = ? AND activity_id = ?
                """),
                (activity_type, activity_id),
            )
            row = cursor.fetchone()
            if not row:
                return 0
            return row["count"]

    @staticmethod
    def has_user_liked(user_id: int, activity_type: str, activity_id: int) -> bool:
        """
        Check if a user has liked an activity.

        Args:
            user_id: User to check
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            True if user has liked this activity
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT 1 FROM activity_likes
                WHERE user_id = ? AND activity_type = ? AND activity_id = ?
                """),
                (user_id, activity_type, activity_id),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_by_activity(activity_type: str, activity_id: int) -> list[dict]:
        """
        Get all likes for an activity with user information.

        Args:
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            List of likes with user info
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT
                    al.id,
                    al.user_id,
                    al.activity_type,
                    al.activity_id,
                    al.created_at,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM activity_likes al
                JOIN users u ON al.user_id = u.id
                WHERE al.activity_type = ? AND al.activity_id = ?
                ORDER BY al.created_at DESC
                """),
                (activity_type, activity_id),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_by_user(user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
        """
        Get all likes by a user.

        Args:
            user_id: User whose likes to retrieve
            limit: Maximum number of likes to return
            offset: Number of likes to skip

        Returns:
            List of likes
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT * FROM activity_likes
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """),
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()
            return [ActivityLikeRepository._row_to_dict(row) for row in rows]
