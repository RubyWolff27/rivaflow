"""Social features — friend requests, friends list, unfriend, friend suggestions."""

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response, status
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import (
    get_current_user,
    get_friend_suggestions_service,
)
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.friend_suggestions_service import (
    FriendSuggestionsService,
)
from rivaflow.core.services.notification_service import NotificationService
from rivaflow.core.services.social_service import SocialService

router = APIRouter(tags=["social"])


# Friend suggestions endpoints
@router.get("/friend-suggestions")
@route_error_handler(
    "get_friend_suggestions", detail="Failed to get friend suggestions"
)
def get_friend_suggestions(
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions"),
    current_user: dict = Depends(get_current_user),
    service: FriendSuggestionsService = Depends(get_friend_suggestions_service),
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
    service: FriendSuggestionsService = Depends(get_friend_suggestions_service),
):
    """
    Browse all discoverable users on the platform.

    Used as a fallback when scoring produces no suggestions.
    Returns users not already connected, excluding self.
    """
    users = service.get_browsable_users(current_user["id"], limit=limit)
    return {"users": users, "count": len(users)}


@router.post("/friend-suggestions/{suggested_user_id}/dismiss")
@route_error_handler("dismiss_suggestion", detail="Failed to dismiss suggestion")
def dismiss_friend_suggestion(
    suggested_user_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
    service: FriendSuggestionsService = Depends(get_friend_suggestions_service),
):
    """
    Dismiss a friend suggestion.

    Args:
        suggested_user_id: ID of the suggested user to dismiss

    Returns:
        Success status
    """
    dismissed = service.dismiss_suggestion(current_user["id"], suggested_user_id)
    return {"dismissed": dismissed}


@router.post("/friend-suggestions/regenerate")
@route_error_handler(
    "regenerate_suggestions", detail="Failed to regenerate suggestions"
)
def regenerate_friend_suggestions(
    current_user: dict = Depends(get_current_user),
    service: FriendSuggestionsService = Depends(get_friend_suggestions_service),
):
    """
    Regenerate friend suggestions.

    This will clear existing suggestions and generate new ones.

    Returns:
        Number of suggestions created
    """
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
    connection_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
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
    connection_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
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
    connection_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
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
