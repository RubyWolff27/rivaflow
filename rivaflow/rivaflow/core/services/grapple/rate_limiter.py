"""Rate limiting for Grapple AI Coach."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from rivaflow.core.middleware.feature_access import FeatureAccess
from rivaflow.db.database import convert_query, get_connection

logger = logging.getLogger(__name__)


class GrappleRateLimiter:
    """
    Rate limiter for Grapple AI Coach.

    Implements:
    - Per-user rate limits based on subscription tier
    - Global rate limit (1000 messages/hour)
    - 1-hour sliding window
    - Database-backed for distributed deployments
    """

    # Global rate limit across all users
    GLOBAL_RATE_LIMIT = 1000  # messages per hour

    def __init__(self):
        """Initialize rate limiter."""
        pass

    def check_rate_limit(self, user_id: int, user_tier: str) -> dict[str, Any]:
        """
        Check if user can send a message based on rate limits.

        Args:
            user_id: User ID
            user_tier: User's subscription tier ('free', 'beta', 'premium', 'admin')

        Returns:
            Dict with:
                - allowed: bool
                - remaining: int (messages remaining in current window)
                - limit: int (total messages allowed per hour)
                - reset_at: datetime (when window resets)
                - global_remaining: int (global messages remaining)
                - reason: Optional[str] (why request was denied)
        """
        # Get user's rate limit based on tier
        user_limit = FeatureAccess.get_rate_limit(user_tier)

        if user_limit == 0:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": 0,
                "reset_at": datetime.utcnow(),
                "global_remaining": 0,
                "reason": "No access to Grapple. Upgrade to Beta or Premium.",
            }

        # Check global rate limit first
        global_count = self._get_global_message_count()
        global_remaining = max(0, self.GLOBAL_RATE_LIMIT - global_count)

        if global_count >= self.GLOBAL_RATE_LIMIT:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": user_limit,
                "reset_at": self._get_next_hour_start(),
                "global_remaining": 0,
                "reason": "Global rate limit exceeded. Please try again in a few minutes.",
            }

        # Check per-user rate limit
        user_count, window_end = self._get_user_message_count(user_id)
        remaining = max(0, user_limit - user_count)

        if user_count >= user_limit:
            return {
                "allowed": False,
                "remaining": 0,
                "limit": user_limit,
                "reset_at": window_end,
                "global_remaining": global_remaining,
                "reason": f"Rate limit exceeded. You can send {user_limit} messages per hour.",
            }

        # All checks passed
        return {
            "allowed": True,
            "remaining": remaining,
            "limit": user_limit,
            "reset_at": window_end,
            "global_remaining": global_remaining,
            "reason": None,
        }

    def record_message(self, user_id: int) -> None:
        """
        Record that a message was sent.

        Args:
            user_id: User ID
        """
        # Get or create current window
        window_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        query = convert_query(
            """
            INSERT INTO grapple_rate_limits (id, user_id, window_start, window_end, message_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (user_id, window_start) DO UPDATE SET
                message_count = grapple_rate_limits.message_count + 1
        """
        )

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (str(uuid4()), user_id, window_start, window_end))
                conn.commit()
                cursor.close()
        except Exception as e:
            logger.error(f"Failed to record message for user {user_id}: {e}")
            # Don't fail the request if we can't record - just log it

    def _get_user_message_count(self, user_id: int) -> tuple[int, datetime]:
        """
        Get message count for user in current hour window.

        Returns:
            Tuple of (message_count, window_end)
        """
        window_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        query = """
            SELECT message_count, window_end
            FROM grapple_rate_limits
            WHERE user_id = ? AND window_start = ?
        """

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id, window_start))
                row = cursor.fetchone()
                cursor.close()

                if row:
                    return row[0], row[1]
                else:
                    return 0, window_end
        except Exception as e:
            logger.error(f"Failed to get message count for user {user_id}: {e}")
            return 0, window_end

    def _get_global_message_count(self) -> int:
        """Get total message count across all users in current hour."""
        window_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        query = """
            SELECT COALESCE(SUM(message_count), 0)
            FROM grapple_rate_limits
            WHERE window_start = ?
        """

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (window_start,))
                row = cursor.fetchone()
                cursor.close()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Failed to get global message count: {e}")
            return 0

    def _get_next_hour_start(self) -> datetime:
        """Get the start of the next hour."""
        now = datetime.utcnow()
        return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    def get_user_usage_stats(self, user_id: int, days: int = 7) -> dict[str, Any]:
        """
        Get usage statistics for a user over the past N days.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Dict with usage statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = """
            SELECT
                COUNT(*) as window_count,
                SUM(message_count) as total_messages,
                MAX(message_count) as peak_hourly_usage,
                AVG(message_count) as avg_hourly_usage
            FROM grapple_rate_limits
            WHERE user_id = ? AND window_start >= ?
        """

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id, start_date))
                row = cursor.fetchone()
                cursor.close()

                if row and row[0] > 0:
                    return {
                        "active_hours": row[0],
                        "total_messages": row[1] or 0,
                        "peak_hourly_usage": row[2] or 0,
                        "avg_hourly_usage": round(row[3] or 0, 2),
                        "days_analyzed": days,
                    }
                else:
                    return {
                        "active_hours": 0,
                        "total_messages": 0,
                        "peak_hourly_usage": 0,
                        "avg_hourly_usage": 0,
                        "days_analyzed": days,
                    }
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {e}")
            return {
                "active_hours": 0,
                "total_messages": 0,
                "peak_hourly_usage": 0,
                "avg_hourly_usage": 0,
                "days_analyzed": days,
            }

    @staticmethod
    def cleanup_old_records(days_to_keep: int = 7) -> int:
        """
        Clean up old rate limit records.

        Args:
            days_to_keep: Number of days of history to keep

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        query = "DELETE FROM grapple_rate_limits WHERE window_start < ?"

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()
                cursor.close()
                logger.info(f"Cleaned up {deleted_count} old rate limit records")
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old rate limit records: {e}")
            return 0
