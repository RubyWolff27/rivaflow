"""Notifications API routes."""
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta

from rivaflow.core.dependencies import get_current_user
from rivaflow.db.repositories.activity_repo import ActivityLikeRepository, ActivityCommentRepository
from rivaflow.db.repositories.user_relationship_repo import UserRelationshipRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/counts")
async def get_notification_counts(current_user: dict = Depends(get_current_user)):
    """
    Get notification counts for the current user.

    Returns:
        - feed_unread: Count of new likes and comments on user's activities (last 7 days)
        - friend_requests: Count of new followers (last 30 days)
    """
    user_id = current_user["id"]

    # Get unread feed activity (likes + comments on user's posts from last 7 days)
    # This is a simple implementation - in production you'd track "last_seen" timestamps
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    like_repo = ActivityLikeRepository()
    comment_repo = ActivityCommentRepository()
    relationship_repo = UserRelationshipRepository()

    # Count recent likes on user's activities
    # This would need session activities owned by the user
    # For now, just return 0 - we'll implement properly with a notifications table later

    # Count new followers (followers who followed in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    followers = relationship_repo.get_followers(user_id)

    # Filter for recent followers (would need created_at column)
    # For now, just count all pending if status field exists
    new_followers = len(followers)  # Simplified for now

    return {
        "feed_unread": 0,  # Placeholder - needs proper implementation with last_seen tracking
        "friend_requests": new_followers if new_followers > 0 else 0,
        "total": new_followers,
    }
