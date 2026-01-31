"""Notifications API routes."""
from fastapi import APIRouter, Depends, Query, Path
from typing import Optional

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/counts")
async def get_notification_counts(current_user: dict = Depends(get_current_user)):
    """
    Get notification counts for the current user.

    Returns:
        - feed_unread: Count of unread likes, comments, and replies
        - friend_requests: Count of new follow notifications
        - total: Total unread notifications
    """
    user_id = current_user["id"]
    try:
        counts = NotificationService.get_notification_counts(user_id)
        return counts
    except Exception as e:
        # Return zero counts if table doesn't exist yet (migration not run)
        return {
            "feed_unread": 0,
            "friend_requests": 0,
            "total": 0,
        }


@router.get("/")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
):
    """
    Get notifications for the current user.

    Args:
        limit: Maximum number of notifications to return (1-100)
        offset: Offset for pagination
        unread_only: If true, only return unread notifications

    Returns:
        List of notifications with actor details
    """
    user_id = current_user["id"]
    notifications = NotificationService.get_notifications(user_id, limit, offset, unread_only)
    return {"notifications": notifications, "count": len(notifications)}


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Mark a single notification as read."""
    user_id = current_user["id"]
    success = NotificationService.mark_as_read(notification_id, user_id)
    return {"success": success}


@router.post("/read-all")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read."""
    user_id = current_user["id"]
    count = NotificationService.mark_all_as_read(user_id)
    return {"success": True, "count": count}


@router.post("/feed/read")
async def mark_feed_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all feed notifications (likes, comments, replies) as read."""
    user_id = current_user["id"]
    count = NotificationService.mark_feed_as_read(user_id)
    return {"success": True, "count": count}


@router.post("/follows/read")
async def mark_follow_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all follow notifications as read."""
    user_id = current_user["id"]
    count = NotificationService.mark_follows_as_read(user_id)
    return {"success": True, "count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Delete a notification."""
    user_id = current_user["id"]
    success = NotificationService.delete_notification(notification_id, user_id)
    return {"success": success}
