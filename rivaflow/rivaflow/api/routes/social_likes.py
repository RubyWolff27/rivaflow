"""Social features — like/unlike endpoints."""

from fastapi import APIRouter, Depends, Path, Request, Response, status
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import ValidationError
from rivaflow.core.services.social_service import SocialService

router = APIRouter(tags=["social"])


# Pydantic models
class LikeRequest(BaseModel):
    """Request model for liking an activity."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)


class UnlikeRequest(BaseModel):
    """Request model for unliking an activity."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)


# Like endpoints
@router.post("/like")
@limiter.limit("60/minute")
@route_error_handler("like_activity", detail="Failed to like activity")
def like_activity(
    request: Request,
    like_req: LikeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Like an activity.

    Args:
        like_req: Like request with activity_type and activity_id

    Returns:
        Created like

    Raises:
        400: If activity doesn't exist, is private, or already liked
        500: Database error
    """
    try:
        like = SocialService.like_activity(
            current_user["id"], like_req.activity_type, like_req.activity_id
        )
        return like
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/like")
@route_error_handler("unlike_activity", detail="Failed to unlike activity")
def unlike_activity(
    request: UnlikeRequest, current_user: dict = Depends(get_current_user)
):
    """
    Remove a like from an activity.

    Args:
        request: Unlike request with activity_type and activity_id

    Returns:
        Success status
    """
    unliked = SocialService.unlike_activity(
        current_user["id"],
        request.activity_type,
        request.activity_id,
    )
    if not unliked:
        return {"unliked": False}
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/likes/{activity_type}/{activity_id}")
@route_error_handler("get_activity_likes", detail="Failed to get likes")
def get_activity_likes(
    activity_type: str = Path(..., pattern="^(session|readiness|rest)$"),
    activity_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all likes for an activity.

    Args:
        activity_type: Type of activity
        activity_id: ID of activity

    Returns:
        List of likes with user info
    """
    likes = SocialService.get_activity_likes(activity_type, activity_id)
    return {
        "likes": likes,
        "count": len(likes),
    }
