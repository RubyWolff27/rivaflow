"""Repository for feed-related data access (social engagement batch queries)."""

from datetime import date
from typing import Any

from rivaflow.db.database import convert_query, get_connection


class FeedRepository:
    """Data access layer for feed-related batch queries."""

    @staticmethod
    def batch_load_friend_sessions(
        user_ids: list[int], start_date: date, end_date: date
    ) -> list[dict]:
        """Load non-private sessions from multiple users within a date range."""
        if not user_ids:
            return []

        placeholders = ",".join("?" * len(user_ids))

        with get_connection() as conn:
            cursor = conn.cursor()

            query = convert_query(f"""
                SELECT
                    id, user_id, session_date, class_type, gym_name, location,
                    duration_mins, intensity, rolls, submissions_for,
                    submissions_against, partners, techniques, notes,
                    visibility_level, instructor_name
                FROM sessions
                WHERE user_id IN ({placeholders})
                    AND session_date BETWEEN ? AND ?
                    AND visibility_level != 'private'
                ORDER BY session_date DESC
            """)
            cursor.execute(query, user_ids + [start_date, end_date])

            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def batch_get_like_counts(
        items_by_type: dict[str, list[int]],
    ) -> dict[tuple, int]:
        """Get like counts grouped by (activity_type, activity_id)."""
        like_counts: dict[tuple, int] = {}

        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_id, COUNT(*) as count
                    FROM activity_likes
                    WHERE activity_type = ?
                      AND activity_id IN ({placeholders})
                    GROUP BY activity_id
                """)
                cursor.execute(query, [activity_type] + activity_ids)
                for row in cursor.fetchall():
                    like_counts[(activity_type, row["activity_id"])] = row["count"]

        return like_counts

    @staticmethod
    def batch_get_comment_counts(
        items_by_type: dict[str, list[int]],
    ) -> dict[tuple, int]:
        """Get comment counts grouped by (activity_type, activity_id)."""
        comment_counts: dict[tuple, int] = {}

        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_id, COUNT(*) as count
                    FROM activity_comments
                    WHERE activity_type = ?
                      AND activity_id IN ({placeholders})
                    GROUP BY activity_id
                """)
                cursor.execute(query, [activity_type] + activity_ids)
                for row in cursor.fetchall():
                    comment_counts[(activity_type, row["activity_id"])] = row["count"]

        return comment_counts

    @staticmethod
    def batch_get_user_likes(user_id: int, items_by_type: dict[str, list[int]]) -> set:
        """Get set of (activity_type, activity_id) that user has liked."""
        user_likes: set = set()

        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_type, activity_id
                    FROM activity_likes
                    WHERE user_id = ?
                      AND activity_type = ?
                      AND activity_id IN ({placeholders})
                """)
                cursor.execute(query, [user_id, activity_type] + activity_ids)
                for row in cursor.fetchall():
                    user_likes.add((row["activity_type"], row["activity_id"]))

        return user_likes

    @staticmethod
    def batch_get_user_profiles(
        user_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Load basic user profiles for a list of user IDs."""
        if not user_ids:
            return []

        with get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(user_ids))
            query = convert_query(f"""
                SELECT id, first_name, last_name, email
                FROM users
                WHERE id IN ({placeholders})
            """)
            cursor.execute(query, user_ids)

            return [dict(row) for row in cursor.fetchall()]
