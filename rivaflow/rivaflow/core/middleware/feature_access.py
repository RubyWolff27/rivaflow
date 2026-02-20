"""Feature access control middleware for subscription tiers."""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class FeatureAccess:
    """Manages feature access based on subscription tiers."""

    # Define which tiers can access each feature
    FEATURE_TIERS: dict[str, list[str]] = {
        "grapple": ["beta", "premium", "admin"],
        "advanced_analytics": ["premium", "admin"],
        "api_access": ["premium", "admin"],
    }

    # Rate limits per tier (messages per hour for Grapple)
    RATE_LIMITS: dict[str, int] = {
        "free": 0,  # No access
        "beta": 30,  # 30 messages/hour during beta
        "premium": 60,  # 60 messages/hour
        "admin": 9999,  # Effectively unlimited
    }

    # Cost limits per tier (USD per month)
    COST_LIMITS: dict[str, float] = {
        "free": 0.0,
        "beta": 5.0,  # $5/month max during beta (covered by us)
        "premium": 50.0,  # $50/month max
        "admin": 9999.0,  # Effectively unlimited
    }

    @classmethod
    def check_feature_access(cls, feature: str, tier: str) -> bool:
        """
        Check if a subscription tier has access to a feature.

        Args:
            feature: Feature name (e.g., 'grapple', 'advanced_analytics')
            tier: User's subscription tier (e.g., 'free', 'beta', 'premium', 'admin')

        Returns:
            True if tier has access, False otherwise
        """
        if feature not in cls.FEATURE_TIERS:
            logger.warning("Unknown feature: %s", feature)
            return False

        allowed_tiers = cls.FEATURE_TIERS[feature]
        return tier in allowed_tiers

    @classmethod
    def get_rate_limit(cls, tier: str) -> int:
        """Get rate limit for a subscription tier."""
        return cls.RATE_LIMITS.get(tier, 0)

    @classmethod
    def get_cost_limit(cls, tier: str) -> float:
        """Get cost limit for a subscription tier."""
        return cls.COST_LIMITS.get(tier, 0.0)


def require_beta_or_premium(func: Callable) -> Callable:
    """
    Decorator to restrict endpoint access to beta, premium, or admin users.

    Usage:
        @router.post("/chat")
        @require_beta_or_premium
        async def chat_endpoint(current_user: dict = Depends(get_current_user)):
            ...

    Raises:
        HTTPException 403: If user doesn't have required subscription tier
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract current_user from kwargs
        current_user = kwargs.get("current_user")

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Get user's subscription tier (default to 'free' if not set)
        user_tier = current_user.get("subscription_tier", "free")

        # Check if tier has access to Grapple
        if not FeatureAccess.check_feature_access("grapple", user_tier):
            logger.warning(
                f"User {current_user.get('id')} (tier: {user_tier}) attempted to access Grapple without permission"
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "premium_required",
                    "message": "Grapple AI Coach requires a Premium subscription",
                    "upgrade_url": "/settings/subscription",
                    "current_tier": user_tier,
                    "required_tiers": ["beta", "premium", "admin"],
                },
            )

        # User has access - proceed with endpoint
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    Decorator to restrict endpoint access to admin users only.

    Usage:
        @router.get("/admin/stats")
        @require_admin
        async def admin_stats(current_user: dict = Depends(get_current_user)):
            ...
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Check if user is admin
        is_admin = current_user.get("is_admin", False)
        user_tier = current_user.get("subscription_tier", "free")

        if not is_admin and user_tier != "admin":
            logger.warning(
                f"Non-admin user {current_user.get('id')} attempted to access admin endpoint"
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper


def get_user_tier_info(user: dict[str, Any]) -> dict[str, Any]:
    """
    Get comprehensive tier information for a user.

    Args:
        user: User dict with subscription_tier field

    Returns:
        Dict with tier details including features, rate limits, etc.
    """
    tier = user.get("subscription_tier", "free")

    return {
        "tier": tier,
        "is_beta": user.get("is_beta_user", False),
        "features": {
            "grapple": FeatureAccess.check_feature_access("grapple", tier),
            "advanced_analytics": FeatureAccess.check_feature_access(
                "advanced_analytics", tier
            ),
            "api_access": FeatureAccess.check_feature_access("api_access", tier),
        },
        "limits": {
            "grapple_messages_per_hour": FeatureAccess.get_rate_limit(tier),
            "monthly_cost_limit_usd": FeatureAccess.get_cost_limit(tier),
        },
    }
