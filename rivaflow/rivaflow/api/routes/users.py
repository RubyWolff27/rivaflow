"""User profile endpoints for viewing other users."""

from fastapi import APIRouter, Depends, Query

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.user_service import UserService

router = APIRouter()
service = UserService()


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1, description="Search query (name or email)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Search for users by name or email."""
    users = service.search_users(query=q, limit=limit, exclude_user_id=current_user["id"])

    # Enrich with social status for current user
    enriched_users = service.enrich_users_with_social_status(
        users=users, current_user_id=current_user["id"]
    )

    return enriched_users


@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public profile."""
    user_profile = service.get_user_profile(user_id=user_id, requesting_user_id=current_user["id"])

    if not user_profile:
        raise NotFoundError("User not found")

    return user_profile


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public statistics."""
    stats = service.get_user_stats(user_id=user_id)

    if stats is None:
        raise NotFoundError("User not found")

    return stats


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get a user's public activity feed."""
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
