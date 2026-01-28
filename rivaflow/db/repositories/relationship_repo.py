"""Repository for user relationships (social graph) data access."""
import sqlite3
from typing import List, Optional

from rivaflow.db.database import get_connection


class UserRelationshipRepository:
    """Data access layer for user relationships (following/followers)."""

    @staticmethod
    def follow(follower_user_id: int, following_user_id: int) -> dict:
        """
        Create a follow relationship.

        Args:
            follower_user_id: User who is following
            following_user_id: User being followed

        Returns:
            The created relationship

        Raises:
            sqlite3.IntegrityError: If relationship already exists or users are the same
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_relationships (follower_user_id, following_user_id, status)
                VALUES (%s, %s, 'active')
                """,
                (follower_user_id, following_user_id),
            )
            relationship_id = cursor.lastrowid

            cursor.execute("SELECT * FROM user_relationships WHERE id = %s", (relationship_id,))
            row = cursor.fetchone()
            return UserRelationshipRepository._row_to_dict(row)

    @staticmethod
    def unfollow(follower_user_id: int, following_user_id: int) -> bool:
        """
        Remove a follow relationship.

        Args:
            follower_user_id: User who is unfollowing
            following_user_id: User being unfollowed

        Returns:
            True if relationship was deleted, False if it didn't exist
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM user_relationships
                WHERE follower_user_id = %s AND following_user_id = %s
                """,
                (follower_user_id, following_user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_followers(user_id: int) -> List[dict]:
        """
        Get all users who follow this user.

        Args:
            user_id: The user whose followers to retrieve

        Returns:
            List of follower user records with relationship info
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    ur.id as relationship_id,
                    ur.follower_user_id,
                    ur.created_at as followed_at,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM user_relationships ur
                JOIN users u ON ur.follower_user_id = u.id
                WHERE ur.following_user_id = %s AND ur.status = 'active'
                ORDER BY ur.created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_following(user_id: int) -> List[dict]:
        """
        Get all users that this user follows.

        Args:
            user_id: The user whose following list to retrieve

        Returns:
            List of followed user records with relationship info
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    ur.id as relationship_id,
                    ur.following_user_id,
                    ur.created_at as followed_at,
                    u.first_name,
                    u.last_name,
                    u.email
                FROM user_relationships ur
                JOIN users u ON ur.following_user_id = u.id
                WHERE ur.follower_user_id = %s AND ur.status = 'active'
                ORDER BY ur.created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def is_following(follower_user_id: int, following_user_id: int) -> bool:
        """
        Check if follower_user_id follows following_user_id.

        Args:
            follower_user_id: User who might be following
            following_user_id: User who might be followed

        Returns:
            True if the relationship exists and is active
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1 FROM user_relationships
                WHERE follower_user_id = %s AND following_user_id = %s AND status = 'active'
                """,
                (follower_user_id, following_user_id),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def get_follower_count(user_id: int) -> int:
        """
        Get the count of users who follow this user.

        Args:
            user_id: The user whose follower count to retrieve

        Returns:
            Number of followers
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM user_relationships
                WHERE following_user_id = %s AND status = 'active'
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    @staticmethod
    def get_following_count(user_id: int) -> int:
        """
        Get the count of users that this user follows.

        Args:
            user_id: The user whose following count to retrieve

        Returns:
            Number of users being followed
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM user_relationships
                WHERE follower_user_id = %s AND status = 'active'
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    @staticmethod
    def get_following_user_ids(user_id: int) -> List[int]:
        """
        Get list of user IDs that this user follows.

        Args:
            user_id: The user whose following list to retrieve

        Returns:
            List of user IDs
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT following_user_id
                FROM user_relationships
                WHERE follower_user_id = %s AND status = 'active'
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [row["following_user_id"] for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}
        return dict(row)
