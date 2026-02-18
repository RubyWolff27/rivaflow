"""Social features API routes (relationships, likes, comments)."""

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.friend_suggestions_service import FriendSuggestionsService
from rivaflow.core.services.notification_service import NotificationService
from rivaflow.core.services.social_service import SocialService
from rivaflow.core.services.user_service import UserService

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
    parent_comment_id: int | None = None


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment."""

    comment_text: str = Field(..., min_length=1, max_length=1000)


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


# User search endpoint
@router.get("/users/search")
@limiter.limit("60/minute")
@route_error_handler("search_users", detail="Failed to search users")
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

    # SQL-level search with LIMIT (avoids loading all users into memory)
    user_service = UserService()
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


# Friend suggestions endpoints
@router.get("/friend-suggestions")
@route_error_handler(
    "get_friend_suggestions", detail="Failed to get friend suggestions"
)
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


@router.get("/friend-suggestions/browse")
@route_error_handler("browse_all_users", detail="Failed to browse users")
def browse_all_users(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """
    Browse all discoverable users on the platform.

    Used as a fallback when scoring produces no suggestions.
    Returns users not already connected, excluding self.
    """
    service = FriendSuggestionsService()
    users = service.get_browsable_users(current_user["id"], limit=limit)
    return {"users": users, "count": len(users)}


@router.post("/friend-suggestions/{suggested_user_id}/dismiss")
@route_error_handler("dismiss_suggestion", detail="Failed to dismiss suggestion")
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
    dismissed = service.dismiss_suggestion(current_user["id"], suggested_user_id)
    return {"dismissed": dismissed}


@router.post("/friend-suggestions/regenerate")
@route_error_handler(
    "regenerate_suggestions", detail="Failed to regenerate suggestions"
)
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
@route_error_handler("send_friend_request", detail="Failed to send friend request")
def send_friend_request(
    request: Request,
    user_id: int = Path(..., gt=0),
    body: FriendRequestBody = Body(default=FriendRequestBody()),
    current_user: dict = Depends(get_current_user),
):
    """Send a friend request to another user."""
    try:
        connection = SocialService.send_friend_request(
            requester_id=current_user["id"],
            recipient_id=user_id,
            connection_source=body.connection_source,
            request_message=body.request_message,
        )
        NotificationService.create_friend_request_notification(
            user_id, current_user["id"]
        )
        return connection
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/friend-requests/{connection_id}/accept")
@route_error_handler("accept_friend_request", detail="Failed to accept friend request")
def accept_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Accept a friend request (must be the recipient)."""
    try:
        connection = SocialService.accept_friend_request(
            connection_id=connection_id, recipient_id=current_user["id"]
        )
        # Notify the requester that their request was accepted
        requester_id = connection.get("requester_id")
        if requester_id:
            NotificationService.create_friend_accepted_notification(
                requester_id, current_user["id"]
            )
        return connection
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/friend-requests/{connection_id}/decline")
@route_error_handler(
    "decline_friend_request", detail="Failed to decline friend request"
)
def decline_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Decline a friend request (must be the recipient)."""
    try:
        connection = SocialService.decline_friend_request(
            connection_id=connection_id, recipient_id=current_user["id"]
        )
        return connection
    except ValueError as e:
        raise ValidationError(str(e))


@router.delete("/friend-requests/{connection_id}")
@route_error_handler("cancel_friend_request", detail="Failed to cancel friend request")
def cancel_friend_request(
    connection_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Cancel a sent friend request (must be the requester)."""
    success = SocialService.cancel_friend_request(
        connection_id=connection_id,
        requester_id=current_user["id"],
    )
    if not success:
        raise NotFoundError("Friend request not found or already responded")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friend-requests/received")
@route_error_handler("get_received_requests", detail="Failed to get friend requests")
def get_received_friend_requests(current_user: dict = Depends(get_current_user)):
    """Get pending friend requests received by the current user."""
    requests = SocialService.get_pending_requests_received(current_user["id"])
    return {"requests": requests, "count": len(requests)}


@router.get("/friend-requests/sent")
@route_error_handler("get_sent_requests", detail="Failed to get sent requests")
def get_sent_friend_requests(current_user: dict = Depends(get_current_user)):
    """Get pending friend requests sent by the current user."""
    requests = SocialService.get_pending_requests_sent(current_user["id"])
    return {"requests": requests, "count": len(requests)}


@router.get("/friends")
@route_error_handler("get_friends", detail="Failed to get friends")
def get_friends(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Get list of accepted friends for the current user."""
    friends = SocialService.get_friends(
        user_id=current_user["id"], limit=limit, offset=offset
    )
    return {"friends": friends, "count": len(friends)}


@router.delete("/friends/{user_id}")
@route_error_handler("unfriend_user", detail="Failed to unfriend user")
def unfriend_user(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Remove a friend connection."""
    success = SocialService.unfriend(
        user_id=current_user["id"],
        friend_user_id=user_id,
    )
    if not success:
        raise NotFoundError("Friend connection not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friends/{user_id}/status")
@route_error_handler("get_friendship_status", detail="Failed to get friendship status")
def get_friendship_status(
    user_id: int = Path(..., gt=0), current_user: dict = Depends(get_current_user)
):
    """Get friendship status with another user."""
    are_friends = SocialService.are_friends(current_user["id"], user_id)

    if not are_friends:
        # Check for pending requests
        received = SocialService.get_pending_requests_received(current_user["id"])
        sent = SocialService.get_pending_requests_sent(current_user["id"])

        pending_from_them = any(r["requester_id"] == user_id for r in received)
        pending_from_me = any(r["recipient_id"] == user_id for r in sent)

        if pending_from_them:
            return {"status": "pending_received", "are_friends": False}
        elif pending_from_me:
            return {"status": "pending_sent", "are_friends": False}
        else:
            return {"status": "none", "are_friends": False}

    return {"status": "friends", "are_friends": True}
