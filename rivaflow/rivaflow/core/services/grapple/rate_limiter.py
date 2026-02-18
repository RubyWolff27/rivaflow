"""Rate limiting for Grapple AI Coach."""

import logging
from datetime import datetime, timedelta
from typing import Any

from rivaflow.core.middleware.feature_access import FeatureAccess
from rivaflow.core.time_utils import utcnow
from rivaflow.db.repositories.grapple_usage_repo import GrappleUsageRepository

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
                "reset_at": utcnow(),
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
        window_start = utcnow().replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        try:
            GrappleUsageRepository.record_message(
                user_id=user_id,
                window_start=window_start.isoformat(),
                window_end=window_end.isoformat(),
            )
        except (ConnectionError, OSError) as e:
            logger.error(f"Failed to record message for user {user_id}: {e}")
            # Don't fail the request if we can't record - just log it

    def _get_user_message_count(self, user_id: int) -> tuple[int, datetime]:
        """
        Get message count for user in current hour window.

        Returns:
            Tuple of (message_count, window_end)
        """
        window_start = utcnow().replace(minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(hours=1)

        try:
            result = GrappleUsageRepository.get_user_message_count(
                user_id, window_start.isoformat()
            )
            if result:
                return result[0], result[1]
            return 0, window_end
        except (ConnectionError, OSError) as e:
            logger.error(f"Failed to get message count for user {user_id}: {e}")
            return 0, window_end

    def _get_global_message_count(self) -> int:
        """Get total message count across all users in current hour."""
        window_start = utcnow().replace(minute=0, second=0, microsecond=0)

        try:
            return GrappleUsageRepository.get_global_message_count(
                window_start.isoformat()
            )
        except (ConnectionError, OSError) as e:
            logger.error(f"Failed to get global message count: {e}")
            return 0

    def _get_next_hour_start(self) -> datetime:
        """Get the start of the next hour."""
        now = utcnow()
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
        start_date = utcnow() - timedelta(days=days)

        try:
            r = GrappleUsageRepository.get_user_usage_stats(
                user_id, start_date.isoformat()
            )
            if r:
                return {
                    "active_hours": r["window_count"],
                    "total_messages": r["total_messages"] or 0,
                    "peak_hourly_usage": r["peak_hourly_usage"] or 0,
                    "avg_hourly_usage": round(float(r["avg_hourly_usage"] or 0), 2),
                    "days_analyzed": days,
                }

            return {
                "active_hours": 0,
                "total_messages": 0,
                "peak_hourly_usage": 0,
                "avg_hourly_usage": 0,
                "days_analyzed": days,
            }
        except (ConnectionError, OSError) as e:
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
        cutoff_date = utcnow() - timedelta(days=days_to_keep)

        try:
            deleted_count = GrappleUsageRepository.cleanup_old_records(
                cutoff_date.isoformat()
            )
            logger.info(f"Cleaned up {deleted_count} old rate limit records")
            return deleted_count
        except (ConnectionError, OSError) as e:
            logger.error(f"Failed to cleanup old rate limit records: {e}")
            return 0
