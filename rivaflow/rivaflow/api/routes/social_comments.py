"""Social features — comment CRUD endpoints."""

from fastapi import APIRouter, Body, Depends, Path, Request, Response, status
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.social_service import SocialService

router = APIRouter(tags=["social"])


# Pydantic models
class CommentRequest(BaseModel):
    """Request model for creating a comment."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)
    comment_text: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: int | None = None


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    comment_text: str = Field(..., min_length=1, max_length=1000)


# Comment endpoints
@router.post("/comment")
@limiter.limit("20/minute")
@route_error_handler("add_comment", detail="Failed to add comment")
def add_comment(
    request: Request,
    comment_req: CommentRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Add a comment to an activity.

    Args:
        comment_req: Comment request with activity info and comment text

    Returns:
        Created comment

    Raises:
        400: If activity doesn't exist, is private, or comment text is invalid
        500: Database error
    """
    try:
        comment = SocialService.add_comment(
            current_user["id"],
            comment_req.activity_type,
            comment_req.activity_id,
            comment_req.comment_text,
            comment_req.parent_comment_id,
        )
        return comment
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.put("/comment/{comment_id}")
@route_error_handler("update_comment", detail="Failed to update comment")
def update_comment(
    comment_id: int = Path(..., gt=0),
    request: CommentUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a comment (user can only update their own comments).

    Args:
        comment_id: ID of comment to update
        request: Updated comment text

    Returns:
        Updated comment

    Raises:
        400: If comment text is invalid
        404: If comment not found or user doesn't own it
        500: Database error
    """
    try:
        comment = SocialService.update_comment(
            comment_id, current_user["id"], request.comment_text
        )
        if not comment:
            raise NotFoundError("Comment not found or you don't own it")
        return comment
    except ValueError as e:
        raise ValidationError(str(e))


@router.delete("/comment/{comment_id}")
@route_error_handler("delete_comment", detail="Failed to delete comment")
def delete_comment(
    comment_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """
    Delete a comment (user can only delete their own comments).

    Args:
        comment_id: ID of comment to delete

    Returns:
        Success status

    Raises:
        404: If comment not found or user doesn't own it
        500: Database error
    """
    success = SocialService.delete_comment(comment_id, current_user["id"])
    if not success:
        raise NotFoundError("Comment not found or you don't own it")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/comments/{activity_type}/{activity_id}")
@route_error_handler("get_activity_comments", detail="Failed to get comments")
def get_activity_comments(
    activity_type: str = Path(..., pattern="^(session|readiness|rest)$"),
    activity_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all comments for an activity.

    Args:
        activity_type: Type of activity
        activity_id: ID of activity

    Returns:
        List of comments with user info
    """
    comments = SocialService.get_activity_comments(activity_type, activity_id)
    return {
        "comments": comments,
        "count": len(comments),
    }
