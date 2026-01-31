"""Social features API routes (relationships, likes, comments)."""
from fastapi import APIRouter, Depends, Path, Body
from pydantic import BaseModel, Field
from typing import Optional

from rivaflow.core.services.social_service import SocialService
from rivaflow.core.dependencies import get_current_user
from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/social", tags=["social"])


# Pydantic models
class LikeRequest(BaseModel):
    """Request model for liking an activity."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)


class UnlikeRequest(BaseModel):
    """Request model for unliking an activity."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)


class CommentRequest(BaseModel):
    """Request model for creating a comment."""

    activity_type: str = Field(..., pattern="^(session|readiness|rest)$")
    activity_id: int = Field(..., gt=0)
    comment_text: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[int] = None


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    comment_text: str = Field(..., min_length=1, max_length=1000)


# Relationship endpoints
@router.post("/follow/{user_id}")
async def follow_user(user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)):
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
        return {"success": True, "relationship": relationship}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/follow/{user_id}")
async def unfollow_user(user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)):
    """
    Unfollow a user.

    Args:
        user_id: ID of user to unfollow

    Returns:
        Success status

    Raises:
        500: Database error
    """
    success = SocialService.unfollow_user(current_user["id"], user_id)
    return {"success": success}


@router.get("/followers")
async def get_followers(current_user: dict = Depends(get_current_user)):
    """
    Get list of users who follow the current user.

    Returns:
        List of follower users with basic info
    """
    followers = SocialService.get_followers(current_user["id"])
    return {
        "followers": followers,
        "count": len(followers),
    }


@router.get("/following")
async def get_following(current_user: dict = Depends(get_current_user)):
    """
    Get list of users that the current user follows.

    Returns:
        List of followed users with basic info
    """
    following = SocialService.get_following(current_user["id"])
    return {
        "following": following,
        "count": len(following),
    }


@router.get("/following/{user_id}")
async def check_following(user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)):
    """
    Check if current user follows another user.

    Args:
        user_id: ID of user to check

    Returns:
        is_following status
    """
    is_following = SocialService.is_following(current_user["id"], user_id)
    return {"is_following": is_following}


# Like endpoints
@router.post("/like")
async def like_activity(request: LikeRequest, current_user: dict = Depends(get_current_user)):
    """
    Like an activity.

    Args:
        request: Like request with activity_type and activity_id

    Returns:
        Created like

    Raises:
        400: If activity doesn't exist, is private, or already liked
        500: Database error
    """
    try:
        like = SocialService.like_activity(
            current_user["id"], request.activity_type, request.activity_id
        )
        return {"success": True, "like": like}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/like")
async def unlike_activity(request: UnlikeRequest, current_user: dict = Depends(get_current_user)):
    """
    Remove a like from an activity.

    Args:
        request: Unlike request with activity_type and activity_id

    Returns:
        Success status
    """
    success = SocialService.unlike_activity(
        current_user["id"], request.activity_type, request.activity_id
    )
    return {"success": success}


@router.get("/likes/{activity_type}/{activity_id}")
async def get_activity_likes(
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


# Comment endpoints
@router.post("/comment")
async def add_comment(request: CommentRequest, current_user: dict = Depends(get_current_user)):
    """
    Add a comment to an activity.

    Args:
        request: Comment request with activity info and comment text

    Returns:
        Created comment

    Raises:
        400: If activity doesn't exist, is private, or comment text is invalid
        500: Database error
    """
    try:
        comment = SocialService.add_comment(
            current_user["id"],
            request.activity_type,
            request.activity_id,
            request.comment_text,
            request.parent_comment_id,
        )
        return {"success": True, "comment": comment}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.put("/comment/{comment_id}")
async def update_comment(
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
        comment = SocialService.update_comment(comment_id, current_user["id"], request.comment_text)
        if not comment:
            raise NotFoundError("Comment not found or you don't own it")
        return {"success": True, "comment": comment}
    except ValueError as e:
        raise ValidationError(str(e))
    except HTTPException:
        raise


@router.delete("/comment/{comment_id}")
async def delete_comment(comment_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)):
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
    try:
        success = SocialService.delete_comment(comment_id, current_user["id"])
        if not success:
            raise NotFoundError("Comment not found or you don't own it")
        return {"success": True}
    except HTTPException:
        raise


@router.get("/comments/{activity_type}/{activity_id}")
async def get_activity_comments(
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


# User search endpoint
@router.get("/users/search")
async def search_users(q: str = "", current_user: dict = Depends(get_current_user)):
    """
    Search for users by name or email.

    Args:
        q: Search query (name or email)

    Returns:
        List of users with follow status
    """
    if not q or len(q) < 2:
        return {"users": []}

    # Get all users (simple implementation for now)
    all_users = UserRepository.list_all()

    # Filter by query (case-insensitive search in first_name, last_name, email)
    query_lower = q.lower()
    filtered_users = [
        user for user in all_users
        if (query_lower in user.get('first_name', '').lower() or
            query_lower in user.get('last_name', '').lower() or
            query_lower in user.get('email', '').lower())
        and user['id'] != current_user['id']  # Exclude current user
    ]

    # Add follow status for each user
    for user in filtered_users:
        user['is_following'] = SocialService.is_following(current_user['id'], user['id'])

    return {
        "users": filtered_users[:20],  # Limit to 20 results
        "count": len(filtered_users[:20]),
    }


# Friend recommendations endpoint
@router.get("/users/recommended")
async def get_recommended_users(current_user: dict = Depends(get_current_user)):
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
    recommendations = SocialService.get_friend_recommendations(current_user['id'])
    return {
        "recommendations": recommendations,
        "count": len(recommendations),
    }
