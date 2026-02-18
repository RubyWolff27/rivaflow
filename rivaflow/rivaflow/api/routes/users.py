"""User profile endpoints for viewing other users."""

from fastapi import APIRouter, Depends, Query, Request

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.user_service import UserService

router = APIRouter()


@router.get("/search")
@limiter.limit("120/minute")
@route_error_handler("search_users", detail="Failed to search users")
def search_users(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query (name or email)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Search for users by name or email."""
    service = UserService()
    users = service.search_users(
        query=q, limit=limit, exclude_user_id=current_user["id"]
    )

    # Enrich with social status for current user
    enriched_users = service.enrich_users_with_social_status(
        users=users, current_user_id=current_user["id"]
    )

    return enriched_users


@router.get("/{user_id}")
@limiter.limit("120/minute")
@route_error_handler("get_user_profile", detail="Failed to get user profile")
def get_user_profile(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public profile."""
    service = UserService()
    user_profile = service.get_user_profile(
        user_id=user_id, requesting_user_id=current_user["id"]
    )

    if not user_profile:
        raise NotFoundError("User not found")

    return user_profile


@router.get("/{user_id}/stats")
@limiter.limit("120/minute")
@route_error_handler("get_user_stats", detail="Failed to get user stats")
def get_user_stats(
    request: Request,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public statistics."""
    service = UserService()
    stats = service.get_user_stats(user_id=user_id)

    if stats is None:
        raise NotFoundError("User not found")

    return stats


@router.get("/{user_id}/activity")
@limiter.limit("120/minute")
@route_error_handler("get_user_activity", detail="Failed to get user activity")
def get_user_activity(
    request: Request,
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public activity feed."""
    service = UserService()
    from rivaflow.core.services.feed_service import FeedService

    # Check if user exists
    user = service.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")

    # Get public activities only
    activities = FeedService.get_user_public_activities(
        user_id=user_id,
        limit=limit,
        offset=offset,
        requesting_user_id=current_user["id"],
    )

    return activities
