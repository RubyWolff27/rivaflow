"""Social features API routes (relationships, likes, comments)."""

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.friend_suggestions_service import FriendSuggestionsService
from rivaflow.core.services.social_service import SocialService
from rivaflow.db.repositories.social_connection_repo import SocialConnectionRepository
from rivaflow.db.repositories.user_repo import UserRepository

router = APIRouter(prefix="/social", tags=["social"])
limiter = Limiter(key_func=get_remote_address)


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
    parent_comment_id: int | None = None


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    comment_text: str = Field(..., min_length=1, max_length=1000)


# Relationship endpoints
@router.post("/follow/{user_id}")
@limiter.limit("30/minute")
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
        return {"success": True, "relationship": relationship}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/follow/{user_id}")
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
    success = SocialService.unfollow_user(current_user["id"], user_id)
    if not success:
        return {"success": False}
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/followers")
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
    all_followers = SocialService.get_followers(current_user["id"])
    total = len(all_followers)
    followers = all_followers[offset : offset + limit]

    return {"followers": followers, "total": total, "limit": limit, "offset": offset}


@router.get("/following")
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
    all_following = SocialService.get_following(current_user["id"])
    total = len(all_following)
    following = all_following[offset : offset + limit]

    return {"following": following, "total": total, "limit": limit, "offset": offset}


@router.get("/following/{user_id}")
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


# Like endpoints
@router.post("/like")
@limiter.limit("60/minute")
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
        return {"success": True, "like": like}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.delete("/like")
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
    success = SocialService.unlike_activity(
        current_user["id"],
        request.activity_type,
        request.activity_id,
    )
    if not success:
        return {"success": False}
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/likes/{activity_type}/{activity_id}")
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


# Comment endpoints
@router.post("/comment")
@limiter.limit("20/minute")
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
        return {"success": True, "comment": comment}
    except ValueError as e:

        raise ValidationError(str(e))

    # All other exceptions handled by global error handler


@router.put("/comment/{comment_id}")
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
        return {"success": True, "comment": comment}
    except ValueError as e:
        raise ValidationError(str(e))
    except HTTPException:
        raise


@router.delete("/comment/{comment_id}")
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
    try:
        success = SocialService.delete_comment(comment_id, current_user["id"])
        if not success:
            raise NotFoundError("Comment not found or you don't own it")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise


@router.get("/comments/{activity_type}/{activity_id}")
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


# User search endpoint
@router.get("/users/search")
@limiter.limit("60/minute")
def search_users(
    request: Request,
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
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

    # Get all users (simple implementation for now)
    all_users = UserRepository.list_all()

    # Filter by query (case-insensitive search in first_name, last_name only)
    query_lower = q.lower()
    filtered_users = [
        user
        for user in all_users
        if (
            query_lower in user.get("first_name", "").lower()
            or query_lower in user.get("last_name", "").lower()
        )
        and user["id"] != current_user["id"]  # Exclude current user
    ]

    # Add follow status and strip sensitive fields
    for user in filtered_users:
        user["is_following"] = SocialService.is_following(
            current_user["id"], user["id"]
        )
        user.pop("email", None)
        user.pop("hashed_password", None)

    return {
        "users": filtered_users[:20],  # Limit to 20 results
        "count": len(filtered_users[:20]),
    }


# Friend recommendations endpoint
@router.get("/users/recommended")
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


# Friend suggestions endpoints
@router.get("/friend-suggestions")
def get_friend_suggestions(
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get friend suggestions based on AI scoring algorithm.

    Scoring:
    - Same primary gym: 40 points
    - Mutual friends: 5 points each (max 25)
    - Same location (city): 15 points
    - Partner name match: 30 points
    - Similar belt rank: 5 points
    - Minimum threshold: 10 points

    Returns:
        List of suggested users with score and reasons
    """
    service = FriendSuggestionsService()
    suggestions = service.get_suggestions(current_user["id"], limit=limit)
    return {
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@router.post("/friend-suggestions/{suggested_user_id}/dismiss")
def dismiss_friend_suggestion(
    suggested_user_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Dismiss a friend suggestion.

    Args:
        suggested_user_id: ID of the suggested user to dismiss

    Returns:
        Success status
    """
    service = FriendSuggestionsService()
    success = service.dismiss_suggestion(current_user["id"], suggested_user_id)
    return {"success": success}


@router.post("/friend-suggestions/regenerate")
def regenerate_friend_suggestions(current_user: dict = Depends(get_current_user)):
    """
    Regenerate friend suggestions.

    This will clear existing suggestions and generate new ones.

    Returns:
        Number of suggestions created
    """
    service = FriendSuggestionsService()
    count = service.generate_suggestions(current_user["id"])
    return {
        "success": True,
        "suggestions_created": count,
    }


# Friend Request System
class FriendRequestBody(BaseModel):
    """Request body for sending a friend request."""

    connection_source: str | None = Field(None, description="How they found each other")
    request_message: str | None = Field(
        None, max_length=500, description="Optional message with request"
    )


@router.post("/friend-requests/{user_id}")
@limiter.limit("20/minute")
def send_friend_request(
    request: Request,
    user_id: int = Path(..., gt=0),
    body: FriendRequestBody = Body(default=FriendRequestBody()),
    current_user: dict = Depends(get_current_user),
):
    """Send a friend request to another user."""
    try:
        connection = SocialConnectionRepository.send_friend_request(
            requester_id=current_user["id"],
            recipient_id=user_id,
            connection_source=body.connection_source,
            request_message=body.request_message,
        )
        return {"success": True, "connection": connection}
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/friend-requests/{connection_id}/accept")
def accept_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Accept a friend request (must be the recipient)."""
    try:
        connection = SocialConnectionRepository.accept_friend_request(
            connection_id=connection_id, recipient_id=current_user["id"]
        )
        return {"success": True, "connection": connection}
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/friend-requests/{connection_id}/decline")
def decline_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Decline a friend request (must be the recipient)."""
    try:
        connection = SocialConnectionRepository.decline_friend_request(
            connection_id=connection_id, recipient_id=current_user["id"]
        )
        return {"success": True, "connection": connection}
    except ValueError as e:
        raise ValidationError(str(e))


@router.delete("/friend-requests/{connection_id}")
def cancel_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Cancel a sent friend request (must be the requester)."""
    success = SocialConnectionRepository.cancel_friend_request(
        connection_id=connection_id,
        requester_id=current_user["id"],
    )
    if not success:
        raise NotFoundError("Friend request not found or already responded")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friend-requests/received")
def get_received_friend_requests(current_user: dict = Depends(get_current_user)):
    """Get pending friend requests received by the current user."""
    requests = SocialConnectionRepository.get_pending_requests_received(
        current_user["id"]
    )
    return {"requests": requests, "count": len(requests)}


@router.get("/friend-requests/sent")
def get_sent_friend_requests(current_user: dict = Depends(get_current_user)):
    """Get pending friend requests sent by the current user."""
    requests = SocialConnectionRepository.get_pending_requests_sent(current_user["id"])
    return {"requests": requests, "count": len(requests)}


@router.get("/friends")
def get_friends(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get list of accepted friends for the current user."""
    friends = SocialConnectionRepository.get_friends(
        user_id=current_user["id"], limit=limit, offset=offset
    )
    return {"friends": friends, "count": len(friends)}


@router.delete("/friends/{user_id}")
def unfriend_user(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Remove a friend connection."""
    success = SocialConnectionRepository.unfriend(
        user_id=current_user["id"],
        friend_user_id=user_id,
    )
    if not success:
        raise NotFoundError("Friend connection not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friends/{user_id}/status")
def get_friendship_status(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Get friendship status with another user."""
    are_friends = SocialConnectionRepository.are_friends(current_user["id"], user_id)

    if not are_friends:
        # Check for pending requests
        received = SocialConnectionRepository.get_pending_requests_received(
            current_user["id"]
        )
        sent = SocialConnectionRepository.get_pending_requests_sent(current_user["id"])

        pending_from_them = any(r["requester_id"] == user_id for r in received)
        pending_from_me = any(r["recipient_id"] == user_id for r in sent)

        if pending_from_them:
            return {"status": "pending_received", "are_friends": False}
        elif pending_from_me:
            return {"status": "pending_sent", "are_friends": False}
        else:
            return {"status": "none", "are_friends": False}

    return {"status": "friends", "are_friends": True}
