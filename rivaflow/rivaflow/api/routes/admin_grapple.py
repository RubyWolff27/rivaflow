"""Admin endpoints for Grapple AI Coach monitoring and management."""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rivaflow.core.dependencies import get_admin_user, get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.grapple_admin_service import GrappleAdminService

router = APIRouter(prefix="/admin/grapple", tags=["admin", "grapple"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class FeedbackRequest(BaseModel):
    """User feedback on a Grapple response."""

    message_id: str
    rating: str  # 'positive' or 'negative'
    category: str | None = None  # 'helpful', 'accurate', 'unclear', etc.
    comment: str | None = None


class UsageStatsResponse(BaseModel):
    """Global usage statistics."""

    total_users: int
    active_users_7d: int
    total_sessions: int
    total_messages: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict[str, Any]
    by_tier: dict[str, Any]


# ============================================================================
# User Feedback Endpoints (Beta/Premium users)
# ============================================================================


@router.post("/feedback")
@route_error_handler("submit_grapple_feedback", detail="Failed to submit feedback")
def submit_feedback(
    feedback: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit feedback on a Grapple response.

    Available to all authenticated users (beta/premium/admin).
    """
    user_id = current_user["id"]

    return GrappleAdminService.submit_feedback(
        user_id=user_id,
        message_id=feedback.message_id,
        rating=feedback.rating,
        category=feedback.category,
        comment=feedback.comment,
    )


# ============================================================================
# Admin Monitoring Endpoints
# ============================================================================


@router.get("/stats/global", response_model=UsageStatsResponse)
@route_error_handler("get_global_stats", detail="Failed to get global stats")
def get_global_stats(
    days: int = 30,
    current_user: dict = Depends(get_admin_user),
):
    """
    Get global Grapple usage statistics.

    Admin only. Shows usage across all users.
    """
    logger.info("Admin %s fetching global Grapple stats", current_user["id"])

    stats = GrappleAdminService.get_global_stats(days=days)

    return UsageStatsResponse(
        total_users=stats["total_users"],
        active_users_7d=stats["active_users_7d"],
        total_sessions=stats["total_sessions"],
        total_messages=stats["total_messages"],
        total_tokens=stats["total_tokens"],
        total_cost_usd=stats["total_cost_usd"],
        by_provider=stats["by_provider"],
        by_tier=stats["by_tier"],
    )


@router.get("/stats/projections")
@route_error_handler("get_cost_projections", detail="Failed to get cost projections")
def get_cost_projections(
    current_user: dict = Depends(get_admin_user),
):
    """
    Get cost projections for current month.

    Admin only. Projects total costs based on current usage.
    """
    logger.info("Admin %s fetching cost projections", current_user["id"])

    return GrappleAdminService.get_projections()


@router.get("/stats/providers")
@route_error_handler("get_provider_stats", detail="Failed to get provider stats")
def get_provider_stats(
    days: int = 7,
    current_user: dict = Depends(get_admin_user),
):
    """
    Get LLM provider usage breakdown.

    Admin only. Shows which providers are being used and their reliability.
    """
    logger.info("Admin %s fetching provider stats", current_user["id"])

    return GrappleAdminService.get_provider_stats(days=days)


@router.get("/stats/users")
@route_error_handler("get_user_stats", detail="Failed to get user stats")
def get_user_stats(
    limit: int = 50,
    current_user: dict = Depends(get_admin_user),
):
    """
    Get top users by usage.

    Admin only. Shows which users are using Grapple most.
    """
    logger.info("Admin %s fetching user stats", current_user["id"])

    return GrappleAdminService.get_top_users(limit=limit)


@router.get("/feedback")
@route_error_handler("get_grapple_feedback", detail="Failed to get feedback")
def get_feedback(
    limit: int = 100,
    rating: str | None = None,
    current_user: dict = Depends(get_admin_user),
):
    """
    Get user feedback on Grapple responses.

    Admin only. Shows feedback to improve the system.
    """
    logger.info("Admin %s fetching feedback", current_user["id"])

    return GrappleAdminService.get_feedback(limit=limit, rating=rating)


@router.get("/health")
@route_error_handler("get_grapple_health", detail="Failed to get Grapple health")
def get_grapple_health(
    current_user: dict = Depends(get_admin_user),
):
    """
    Get Grapple system health status.

    Admin only. Shows LLM provider availability and system status.
    """
    logger.info("Admin %s checking Grapple health", current_user["id"])

    return GrappleAdminService.check_health()
