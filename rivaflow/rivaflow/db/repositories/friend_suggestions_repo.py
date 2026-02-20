"""Repository for friend suggestions data access."""

import json
from datetime import datetime, timedelta
from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class FriendSuggestionsRepository(BaseRepository):
    """Data access layer for friend suggestions."""

    @staticmethod
    def create(
        user_id: int,
        suggested_user_id: int,
        score: float,
        reasons: list[str],
        mutual_friends_count: int = 0,
        expires_at: datetime | None = None,
    ) -> int:
        """Create a new friend suggestion."""
        if expires_at is None:
            expires_at = datetime.now() + timedelta(days=7)  # Default 7-day expiry

        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO friend_suggestions (
                    user_id, suggested_user_id, score, reasons,
                    mutual_friends_count, generated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    suggested_user_id,
                    score,
                    json.dumps(reasons),
                    mutual_friends_count,
                    datetime.now().isoformat(),
                    (
                        expires_at.isoformat()
                        if isinstance(expires_at, datetime)
                        else str(expires_at)
                    ),
                ),
            )

    @staticmethod
    def get_active_suggestions(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        """Get active (non-dismissed, non-expired) suggestions for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        fs.*,
                        u.username,
                        u.display_name,
                        u.profile_photo_url,
                        u.belt_rank,
                        u.belt_stripes,
                        u.location_city,
                        u.location_state,
                        u.primary_gym_id,
                        g.name as primary_gym_name
                    FROM friend_suggestions fs
                    JOIN users u ON fs.suggested_user_id = u.id
                    LEFT JOIN gyms g ON u.primary_gym_id = g.id
                    WHERE fs.user_id = ?
                    AND fs.dismissed = FALSE
                    AND fs.expires_at > ?
                    ORDER BY fs.score DESC
                    LIMIT ?
                """),
                (user_id, datetime.now().isoformat(), limit),
            )
            rows = cursor.fetchall()
            return [FriendSuggestionsRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def dismiss_suggestion(user_id: int, suggested_user_id: int) -> bool:
        """Dismiss a friend suggestion."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE friend_suggestions
                    SET dismissed = TRUE, dismissed_at = ?
                    WHERE user_id = ? AND suggested_user_id = ?
                """),
                (datetime.now().isoformat(), user_id, suggested_user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def clear_expired_suggestions(user_id: int) -> int:
        """Delete expired suggestions for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    DELETE FROM friend_suggestions
                    WHERE user_id = ? AND expires_at < ?
                """),
                (user_id, datetime.now().isoformat()),
            )
            return cursor.rowcount

    @staticmethod
    def clear_all_suggestions(user_id: int) -> int:
        """Clear all suggestions for a user (for regeneration)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM friend_suggestions WHERE user_id = ?"),
                (user_id,),
            )
            return cursor.rowcount

    @staticmethod
    def suggestion_exists(user_id: int, suggested_user_id: int) -> bool:
        """Check if a suggestion already exists."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT COUNT(*) as count FROM friend_suggestions
                    WHERE user_id = ? AND suggested_user_id = ?
                    AND dismissed = FALSE
                """),
                (user_id, suggested_user_id),
            )
            row = cursor.fetchone()
            count = row["count"]
            return count > 0

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert database row to dictionary."""
        result = dict(row)

        # Parse JSON fields if they're strings
        if isinstance(result.get("reasons"), str):
            result["reasons"] = json.loads(result["reasons"])

        return result
