"""Repository for notifications data access."""

from datetime import datetime, timedelta
from typing import Any

from rivaflow.db.database import convert_query, get_connection


class NotificationRepository:
    """Repository for managing user notifications."""

    @staticmethod
    def create(
        user_id: int,
        actor_id: int,
        notification_type: str,
        activity_type: str | None = None,
        activity_id: int | None = None,
        comment_id: int | None = None,
        message: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new notification.

        Args:
            user_id: User receiving the notification
            actor_id: User who triggered the notification
            notification_type: Type of notification (like, comment, follow, reply, mention)
            activity_type: Type of activity (session, readiness, rest)
            activity_id: ID of the activity
            comment_id: ID of the comment (for replies)
            message: Optional custom message

        Returns:
            Created notification as dict
        """
        query = convert_query("""
            INSERT INTO notifications (user_id, actor_id, notification_type, activity_type, activity_id, comment_id, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id, user_id, actor_id, notification_type, activity_type, activity_id, comment_id, message, is_read, created_at, read_at
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    user_id,
                    actor_id,
                    notification_type,
                    activity_type,
                    activity_id,
                    comment_id,
                    message,
                ),
            )
            row = cursor.fetchone()
            conn.commit()

            if row:
                d = dict(row)
                d["is_read"] = bool(d.get("is_read"))
                return d
            return {}

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications for a user."""
        query = convert_query(
            "SELECT COUNT(*) as cnt FROM notifications"
            " WHERE user_id = ? AND is_read = FALSE"
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if not result:
                return 0
            return dict(result).get("cnt", 0)

    @staticmethod
    def get_unread_count_by_type(user_id: int, notification_type: str) -> int:
        """Get count of unread notifications by type for a user."""
        query = convert_query(
            "SELECT COUNT(*) as cnt FROM notifications"
            " WHERE user_id = ? AND notification_type = ?"
            " AND is_read = FALSE"
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, notification_type))
            result = cursor.fetchone()
            if not result:
                return 0
            return dict(result).get("cnt", 0)

    @staticmethod
    def get_feed_unread_count(user_id: int) -> int:
        """Get count of unread feed notifications (likes and comments on user's activities)."""
        query = convert_query("""
            SELECT COUNT(*) as cnt
            FROM notifications
            WHERE user_id = ?
            AND notification_type IN ('like', 'comment', 'reply')
            AND is_read = FALSE
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            if not result:
                return 0
            return dict(result).get("cnt", 0)

    @staticmethod
    def get_by_user(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            unread_only: If True, only return unread notifications

        Returns:
            List of notifications with actor details
        """
        base_query = """
            SELECT
                n.id, n.user_id, n.actor_id, n.notification_type,
                n.activity_type, n.activity_id, n.comment_id, n.message,
                n.is_read, n.created_at, n.read_at,
                u.first_name as actor_first_name,
                u.last_name as actor_last_name,
                u.avatar_url as actor_avatar
            FROM notifications n
            JOIN users u ON n.actor_id = u.id
            WHERE n.user_id = ?"""
        params: list[Any] = [user_id]

        if unread_only:
            base_query += " AND n.is_read = FALSE"

        base_query += " ORDER BY n.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        query = convert_query(base_query)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                d = dict(row)
                results.append(
                    {
                        "id": d["id"],
                        "user_id": d["user_id"],
                        "actor_id": d["actor_id"],
                        "notification_type": d["notification_type"],
                        "activity_type": d.get("activity_type"),
                        "activity_id": d.get("activity_id"),
                        "comment_id": d.get("comment_id"),
                        "message": d.get("message"),
                        "is_read": bool(d.get("is_read")),
                        "created_at": d.get("created_at"),
                        "read_at": d.get("read_at"),
                        "actor": {
                            "first_name": d.get("actor_first_name"),
                            "last_name": d.get("actor_last_name"),
                            "avatar_url": d.get("actor_avatar"),
                        },
                    }
                )
            return results

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        query = convert_query("""
            UPDATE notifications
            SET is_read = ?, read_at = ?
            WHERE id = ? AND user_id = ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (True, datetime.utcnow(), notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Mark all notifications as read for a user. Returns count of notifications marked."""
        query = convert_query("""
            UPDATE notifications
            SET is_read = ?, read_at = ?
            WHERE user_id = ? AND is_read = FALSE
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (True, datetime.utcnow(), user_id))
            conn.commit()
            return cursor.rowcount

    @staticmethod
    def mark_feed_as_read(user_id: int) -> int:
        """Mark all feed notifications (likes, comments, replies) as read. Returns count."""
        query = convert_query("""
            UPDATE notifications
            SET is_read = ?, read_at = ?
            WHERE user_id = ?
            AND notification_type IN ('like', 'comment', 'reply')
            AND is_read = FALSE
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (True, datetime.utcnow(), user_id))
            conn.commit()
            return cursor.rowcount

    @staticmethod
    def mark_follows_as_read(user_id: int) -> int:
        """Mark all follow notifications as read. Returns count."""
        query = convert_query("""
            UPDATE notifications
            SET is_read = ?, read_at = ?
            WHERE user_id = ?
            AND notification_type = 'follow'
            AND is_read = FALSE
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (True, datetime.utcnow(), user_id))
            conn.commit()
            return cursor.rowcount

    @staticmethod
    def delete_by_id(notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        query = convert_query("DELETE FROM notifications WHERE id = ? AND user_id = ?")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (notification_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def check_duplicate(
        user_id: int,
        actor_id: int,
        notification_type: str,
        activity_type: str | None = None,
        activity_id: int | None = None,
    ) -> bool:
        """
        Check if a similar notification already exists (to prevent spam).
        Returns True if duplicate exists.
        """
        cutoff = datetime.utcnow() - timedelta(hours=1)
        query = convert_query("""
            SELECT COUNT(*) as cnt
            FROM notifications
            WHERE user_id = ?
            AND actor_id = ?
            AND notification_type = ?
            AND (activity_type = ? OR (activity_type IS NULL AND ? IS NULL))
            AND (activity_id = ? OR (activity_id IS NULL AND ? IS NULL))
            AND created_at > ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    user_id,
                    actor_id,
                    notification_type,
                    activity_type,
                    activity_type,
                    activity_id,
                    activity_id,
                    cutoff,
                ),
            )
            result = cursor.fetchone()
            if not result:
                return False
            return dict(result).get("cnt", 0) > 0
