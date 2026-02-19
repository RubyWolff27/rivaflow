"""Social features — follow/unfollow, relationship endpoints, user search, recommendations."""

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Request,
    Response,
    status,
)

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import (
    get_current_user,
    get_user_service,
)
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import ValidationError
from rivaflow.core.services.social_service import SocialService
from rivaflow.core.services.user_service import UserService

router = APIRouter(prefix="/social", tags=["social"])


# Relationship endpoints
@router.post("/follow/{user_id}")
@limiter.limit("30/minute")
@route_error_handler("follow_user", detail="Failed to follow user")
def follow_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Follow another user.

    Args:
        user_id: ID of user to follow

    Returns:
        Created relationship

    Raises:
        400: If trying to follow yourself or already following
        500: Database error
    """
    try:
        relationship = SocialService.follow_user(current_user["id"], user_id)
        return relationship
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/follow/{user_id}")
@route_error_handler("unfollow_user", detail="Failed to unfollow user")
def unfollow_user(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """
    Unfollow a user.

    Args:
        user_id: ID of user to unfollow

    Returns:
        Success status

    Raises:
        500: Database error
    """
    unfollowed = SocialService.unfollow_user(current_user["id"], user_id)
    if not unfollowed:
        return {"unfollowed": False}
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/followers")
@route_error_handler("get_followers", detail="Failed to get followers")
def get_followers(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of users who follow the current user with pagination.

    Returns:
        Paginated list of follower users with basic info
    """
    followers = SocialService.get_followers(
        current_user["id"], limit=limit, offset=offset
    )
    total = SocialService.count_followers(current_user["id"])

    return {"followers": followers, "total": total, "limit": limit, "offset": offset}


@router.get("/following")
@route_error_handler("get_following", detail="Failed to get following")
def get_following(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of users that the current user follows with pagination.

    Returns:
        Paginated list of followed users with basic info
    """
    following = SocialService.get_following(
        current_user["id"], limit=limit, offset=offset
    )
    total = SocialService.count_following(current_user["id"])

    return {"following": following, "total": total, "limit": limit, "offset": offset}


@router.get("/following/{user_id}")
@route_error_handler("check_following", detail="Failed to check following status")
def check_following(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """
    Check if current user follows another user.

    Args:
        user_id: ID of user to check

    Returns:
        is_following status
    """
    is_following = SocialService.is_following(current_user["id"], user_id)
    return {"is_following": is_following}


# User search endpoint
@router.get("/users/search")
@limiter.limit("60/minute")
@route_error_handler("search_users", detail="Failed to search users")
def search_users(
    request: Request,
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Search for users by name or email.

    Args:
        q: Search query (name or email)

    Returns:
        List of users with follow status
    """
    if not q or len(q) < 2:
        return {"users": []}
    filtered_users = user_service.search_users(
        q, limit=21, exclude_user_id=current_user["id"]
    )[:20]

    # Add follow status and strip sensitive fields
    for user in filtered_users:
        user["is_following"] = SocialService.is_following(
            current_user["id"], user["id"]
        )
        user.pop("email", None)
        user.pop("hashed_password", None)

    return {
        "users": filtered_users,
        "count": len(filtered_users),
    }


# Friend recommendations endpoint
@router.get("/users/recommended")
@route_error_handler("get_recommended_users", detail="Failed to get recommendations")
def get_recommended_users(current_user: dict = Depends(get_current_user)):
    """
    Get recommended users to follow based on gym overlap (Strava-style).

    Recommendations are based on:
    - Same gym (regular training location)
    - Recent gym overlap (trained at same gym in last 30 days)
    - Mutual training partners
    - Already following status excluded

    Returns:
        List of recommended users with context on why they're recommended
    """
    recommendations = SocialService.get_friend_recommendations(current_user["id"])
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
    }
