"""Notifications API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/counts")
async def get_notification_counts(
    request: Request, current_user: dict = Depends(get_current_user)
):
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
    except Exception:
        # Return zero counts if table doesn't exist yet (migration not run)
        return {
            "feed_unread": 0,
            "friend_requests": 0,
            "total": 0,
        }


@router.get("/")
async def get_notifications(
    request: Request,
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
    try:
        notifications = NotificationService.get_notifications(
            user_id, limit, offset, unread_only
        )
        return {"notifications": notifications, "count": len(notifications)}
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(f"Error getting notifications: {e}", exc_info=True)
        return {"notifications": [], "count": 0}


@router.post("/read-all")
async def mark_all_notifications_as_read(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read."""
    user_id = current_user["id"]
    try:
        count = NotificationService.mark_all_as_read(user_id)
        return {"success": True, "count": count}
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
        return {"success": True, "count": 0}


@router.post("/feed/read", status_code=status.HTTP_200_OK)
async def mark_feed_notifications_as_read(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Mark all feed notifications (likes, comments, replies) as read."""
    try:
        logger.info(
            f"mark_feed_notifications_as_read called for user {current_user.get('id', 'UNKNOWN')}"
        )
        user_id = current_user.get("id")
        if not user_id:
            logger.error("No user_id in current_user dict")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        count = NotificationService.mark_feed_as_read(user_id)
        logger.info(
            f"Successfully marked {count} feed notifications as read for user {user_id}"
        )
        return {"success": True, "count": count}
    except HTTPException:
        raise
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(
            f"Error marking feed notifications as read for user {current_user.get('id', 'UNKNOWN')}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        # Return success anyway to prevent frontend errors
        return {"success": True, "count": 0}


@router.post("/follows/read", status_code=status.HTTP_200_OK)
async def mark_follow_notifications_as_read(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Mark all follow notifications as read."""
    try:
        logger.info(
            f"mark_follow_notifications_as_read called for user {current_user.get('id', 'UNKNOWN')}"
        )
        user_id = current_user.get("id")
        if not user_id:
            logger.error("No user_id in current_user dict")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        count = NotificationService.mark_follows_as_read(user_id)
        logger.info(
            f"Successfully marked {count} follow notifications as read for user {user_id}"
        )
        return {"success": True, "count": count}
    except HTTPException:
        raise
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(
            f"Error marking follow notifications as read for user {current_user.get('id', 'UNKNOWN')}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        return {"success": True, "count": 0}


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    request: Request,
    notification_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Mark a single notification as read."""
    user_id = current_user["id"]
    try:
        success = NotificationService.mark_as_read(notification_id, user_id)
        return {"success": success}
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return {"success": False}


@router.delete("/{notification_id}")
async def delete_notification(
    request: Request,
    notification_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Delete a notification."""
    user_id = current_user["id"]
    try:
        success = NotificationService.delete_notification(notification_id, user_id)
        return {"success": success}
    except Exception as e:
        # Gracefully handle if notifications table doesn't exist yet
        logger.error(f"Error deleting notification: {e}", exc_info=True)
        return {"success": False}
