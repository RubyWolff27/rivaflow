"""Grapple AI Coach — tier info, usage stats, and token monitor endpoints."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.middleware.feature_access import (
    get_user_tier_info,
    require_beta_or_premium,
)

router = APIRouter(tags=["grapple"])
logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================


class TierInfoResponse(BaseModel):
    """User's subscription tier and feature access."""

    tier: str
    is_beta: bool
    features: dict
    limits: dict


# ============================================================================
# Tier / Usage Endpoints
# ============================================================================


@router.get("/info", response_model=TierInfoResponse)
@route_error_handler("get_grapple_info", detail="Failed to get Grapple info")
def get_grapple_info(current_user: dict = Depends(get_current_user)):
    """
    Get information about Grapple AI Coach and user's access level.

    This endpoint is available to all authenticated users to show them
    what Grapple is and whether they have access.
    """
    tier_info = get_user_tier_info(current_user)

    return TierInfoResponse(
        tier=tier_info["tier"],
        is_beta=tier_info["is_beta"],
        features=tier_info["features"],
        limits=tier_info["limits"],
    )


@router.get("/teaser")
@route_error_handler("get_grapple_teaser", detail="Failed to get Grapple teaser")
def get_grapple_teaser(current_user: dict = Depends(get_current_user)):
    """
    Teaser endpoint showing free users what they're missing.

    Returns information about Grapple features and upgrade path.
    """
    tier = current_user.get("subscription_tier", "free")
    has_access = tier in ["beta", "premium", "admin"]

    return {
        "has_access": has_access,
        "current_tier": tier,
        "grapple_features": [
            "🧠 AI-powered BJJ coaching with personalized insights",
            "📊 Context-aware advice based on your training history",
            "🎯 Technique analysis and recommendations",
            "💪 Recovery and progression guidance",
            "📚 Access to curated BJJ knowledge base",
            "⚡ Powered by advanced cloud LLMs (Groq/Together AI)",
        ],
        "beta_features": [
            "✨ 30 messages per hour during beta",
            "🎁 Free access during beta period",
            "👥 Early access to new features",
            "💬 Direct feedback channel to developers",
        ],
        "premium_features": [
            "🚀 60 messages per hour",
            "📈 Advanced analytics and insights",
            "🔗 API access for integrations",
            "🎯 Priority support",
        ],
        "upgrade_url": "/settings/subscription" if not has_access else None,
        "message": (
            "Upgrade to Premium to unlock Grapple AI Coach!"
            if not has_access
            else "You have access to Grapple AI Coach!"
        ),
    }


@router.get("/usage")
@require_beta_or_premium
@route_error_handler("get_usage_stats", detail="Failed to get usage stats")
def get_usage_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get user's Grapple usage statistics.

    Returns:
        - Messages sent today/this week/this month
        - Tokens used
        - Cost incurred
        - Rate limit status
        - Cost projections
    """
    from rivaflow.core.middleware.feature_access import FeatureAccess
    from rivaflow.core.services.grapple.rate_limiter import GrappleRateLimiter
    from rivaflow.core.services.grapple.token_monitor import GrappleTokenMonitor

    user_id = current_user["id"]
    user_tier = current_user.get("subscription_tier", "free")

    logger.info("Fetching usage stats for user %s", user_id)

    # Get token usage stats
    token_monitor = GrappleTokenMonitor()
    usage_30d = token_monitor.get_user_usage(user_id)
    cost_projection = token_monitor.get_cost_projection(user_id)
    cost_limit_check = token_monitor.check_cost_limit(user_id, user_tier)

    # Get rate limit stats
    rate_limiter = GrappleRateLimiter()
    rate_stats = rate_limiter.get_user_usage_stats(user_id, days=7)
    rate_check = rate_limiter.check_rate_limit(user_id, user_tier)

    return {
        "user_id": user_id,
        "tier": user_tier,
        "usage_30_days": usage_30d,
        "cost_projection": cost_projection,
        "cost_limit": cost_limit_check,
        "rate_limit": {
            "current_status": {
                "allowed": rate_check["allowed"],
                "remaining": rate_check["remaining"],
                "limit": rate_check["limit"],
                "reset_at": rate_check["reset_at"].isoformat(),
            },
            "weekly_stats": rate_stats,
        },
        "limits": {
            "messages_per_hour": FeatureAccess.get_rate_limit(user_tier),
            "monthly_cost_limit_usd": FeatureAccess.get_cost_limit(user_tier),
        },
    }
