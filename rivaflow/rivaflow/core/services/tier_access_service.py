"""
Tier Access Service
Handles tier permission checks and feature usage tracking
"""

from datetime import date, datetime

from rivaflow.config.tiers import (
    TIERS,
    get_limit,
    get_tier_config,
    has_feature,
    is_premium_tier,
)
from rivaflow.db.database import get_db_connection


class TierAccessService:
    """Service for checking tier permissions and managing feature usage"""

    @staticmethod
    def check_tier_access(
        user_tier: str, required_feature: str
    ) -> tuple[bool, str | None]:
        """
        Check if a user's tier has access to a feature

        Returns:
            Tuple of (has_access: bool, error_message: Optional[str])
        """
        if not user_tier or user_tier not in TIERS:
            return False, "Invalid user tier"

        if has_feature(user_tier, required_feature):
            return True, None

        config = get_tier_config(user_tier)
        return (
            False,
            f"This feature requires a Premium subscription. You are currently on {config.display_name}.",
        )

    @staticmethod
    def check_usage_limit(
        user_id: int, user_tier: str, feature: str, increment: bool = False
    ) -> tuple[bool, str | None, int]:
        """
        Check if user has reached their tier limit for a feature

        Args:
            user_id: User ID
            user_tier: User's subscription tier
            feature: Feature to check (e.g., 'max_friends', 'max_photos_per_session')
            increment: If True, increment the usage count

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str], current_count: int)
        """
        limit = get_limit(user_tier, feature)

        # -1 means unlimited
        if limit == -1:
            return True, None, -1

        # 0 means feature not available
        if limit == 0:
            return False, "This feature is not available on your current plan.", 0

        # Get current usage
        current_count = TierAccessService._get_current_usage(user_id, feature)

        # Check if limit reached
        if current_count >= limit:
            config = get_tier_config(user_tier)
            return (
                False,
                f"You've reached your {config.display_name} limit of {limit} for this feature. Upgrade to Premium for unlimited access.",
                current_count,
            )

        # Increment if requested
        if increment:
            TierAccessService._increment_usage(user_id, feature)
            current_count += 1

        return True, None, current_count

    @staticmethod
    def _get_current_usage(user_id: int, feature: str) -> int:
        """Get current usage count for a feature"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            today = date.today()

            # For monthly limits, use first of month
            period_start = date(today.year, today.month, 1)

            cursor.execute(
                """
                SELECT count FROM feature_usage
                WHERE user_id = ? AND feature = ? AND period_start = ?
            """,
                (user_id, feature, period_start),
            )

            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

    @staticmethod
    def _increment_usage(user_id: int, feature: str) -> None:
        """Increment usage count for a feature"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            today = date.today()
            period_start = date(today.year, today.month, 1)

            # Upsert usage record
            cursor.execute(
                """
                INSERT INTO feature_usage (user_id, feature, count, period_start, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(user_id, feature, period_start)
                DO UPDATE SET count = count + 1, updated_at = ?
            """,
                (user_id, feature, period_start, datetime.now(), datetime.now()),
            )

            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_usage_summary(user_id: int, user_tier: str) -> dict:
        """
        Get usage summary for all limited features

        Returns:
            Dict with feature usage and limits
        """
        config = get_tier_config(user_tier)
        if not config:
            return {}

        summary = {
            "tier": user_tier,
            "tier_display": config.display_name,
            "is_premium": is_premium_tier(user_tier),
            "features": {},
        }

        # Get usage for each limited feature
        for feature_name, limit in config.limits.items():
            if limit == -1:
                summary["features"][feature_name] = {
                    "limit": "unlimited",
                    "current": "unlimited",
                    "percentage": 0,
                }
            elif limit > 0:
                current = TierAccessService._get_current_usage(user_id, feature_name)
                summary["features"][feature_name] = {
                    "limit": limit,
                    "current": current,
                    "percentage": (current / limit * 100) if limit > 0 else 0,
                }

        return summary

    @staticmethod
    def check_tier_expired(tier_expires_at: datetime | None) -> bool:
        """Check if user's premium tier has expired"""
        if not tier_expires_at:
            return False  # NULL means never expires
        return datetime.now() > tier_expires_at

    @staticmethod
    def get_tier_features(user_tier: str) -> list:
        """Get list of features available for a tier"""
        config = get_tier_config(user_tier)
        return config.features if config else []
