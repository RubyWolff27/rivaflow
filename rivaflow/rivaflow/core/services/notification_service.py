"""Service layer for notifications."""

from typing import Any

from rivaflow.db.repositories.notification_repo import NotificationRepository


class NotificationService:
    """Service for managing user notifications."""

    @staticmethod
    def create_like_notification(
        activity_owner_id: int,
        liker_id: int,
        activity_type: str,
        activity_id: int,
    ) -> dict[str, Any] | None:
        """
        Create a notification when someone likes an activity.

        Args:
            activity_owner_id: User who owns the activity
            liker_id: User who liked the activity
            activity_type: Type of activity (session, readiness, rest)
            activity_id: ID of the activity

        Returns:
            Created notification or None if duplicate/self-like
        """
        # Don't notify if user likes their own content
        if activity_owner_id == liker_id:
            return None

        # Check for duplicate notification (same person liking same thing within 1 hour)
        if NotificationRepository.check_duplicate(
            activity_owner_id, liker_id, "like", activity_type, activity_id
        ):
            return None

        return NotificationRepository.create(
            user_id=activity_owner_id,
            actor_id=liker_id,
            notification_type="like",
            activity_type=activity_type,
            activity_id=activity_id,
            message=f"liked your {activity_type}",
        )

    @staticmethod
    def create_comment_notification(
        activity_owner_id: int,
        commenter_id: int,
        activity_type: str,
        activity_id: int,
        comment_id: int,
    ) -> dict[str, Any] | None:
        """
        Create a notification when someone comments on an activity.

        Args:
            activity_owner_id: User who owns the activity
            commenter_id: User who commented
            activity_type: Type of activity
            activity_id: ID of the activity
            comment_id: ID of the comment

        Returns:
            Created notification or None if self-comment
        """
        # Don't notify if user comments on their own content
        if activity_owner_id == commenter_id:
            return None

        # Don't check for duplicates on comments - each comment should notify

        return NotificationRepository.create(
            user_id=activity_owner_id,
            actor_id=commenter_id,
            notification_type="comment",
            activity_type=activity_type,
            activity_id=activity_id,
            comment_id=comment_id,
            message=f"commented on your {activity_type}",
        )

    @staticmethod
    def create_reply_notification(
        parent_comment_owner_id: int,
        replier_id: int,
        activity_type: str,
        activity_id: int,
        comment_id: int,
    ) -> dict[str, Any] | None:
        """
        Create a notification when someone replies to a comment.

        Args:
            parent_comment_owner_id: User who wrote the parent comment
            replier_id: User who replied
            activity_type: Type of activity
            activity_id: ID of the activity
            comment_id: ID of the reply comment

        Returns:
            Created notification or None if self-reply
        """
        # Don't notify if user replies to their own comment
        if parent_comment_owner_id == replier_id:
            return None

        return NotificationRepository.create(
            user_id=parent_comment_owner_id,
            actor_id=replier_id,
            notification_type="reply",
            activity_type=activity_type,
            activity_id=activity_id,
            comment_id=comment_id,
            message="replied to your comment",
        )

    @staticmethod
    def create_follow_notification(
        followed_user_id: int, follower_id: int
    ) -> dict[str, Any] | None:
        """
        Create a notification when someone follows a user.

        Args:
            followed_user_id: User being followed
            follower_id: User who followed

        Returns:
            Created notification or None if duplicate
        """
        # Check for duplicate follow notification within 1 hour
        if NotificationRepository.check_duplicate(
            followed_user_id, follower_id, "follow", None, None
        ):
            return None

        return NotificationRepository.create(
            user_id=followed_user_id,
            actor_id=follower_id,
            notification_type="follow",
            message="started following you",
        )

    @staticmethod
    def create_friend_request_notification(
        recipient_id: int, requester_id: int
    ) -> dict[str, Any] | None:
        """Create a notification when someone sends a friend request."""
        if recipient_id == requester_id:
            return None

        if NotificationRepository.check_duplicate(
            recipient_id, requester_id, "follow", None, None
        ):
            return None

        return NotificationRepository.create(
            user_id=recipient_id,
            actor_id=requester_id,
            notification_type="follow",
            message="sent you a friend request",
        )

    @staticmethod
    def create_friend_accepted_notification(
        requester_id: int, accepter_id: int
    ) -> dict[str, Any] | None:
        """Create a notification when someone accepts a friend request."""
        return NotificationRepository.create(
            user_id=requester_id,
            actor_id=accepter_id,
            notification_type="follow",
            message="accepted your friend request",
        )

    @staticmethod
    def create_milestone_notification(
        user_id: int, milestone_label: str
    ) -> dict[str, Any] | None:
        """Create a notification for a newly achieved milestone."""
        return NotificationRepository.create(
            user_id=user_id,
            actor_id=user_id,
            notification_type="milestone",
            message=f"Milestone: {milestone_label}",
        )

    @staticmethod
    def create_streak_notification(
        user_id: int, streak_type: str, streak_length: int
    ) -> dict[str, Any] | None:
        """Create a notification for a notable streak threshold."""
        notable = {7, 14, 21, 30, 50, 75, 100, 150, 200, 365}
        if streak_length not in notable:
            return None
        return NotificationRepository.create(
            user_id=user_id,
            actor_id=user_id,
            notification_type="streak",
            message=f"{streak_length}-day {streak_type} streak!",
        )

    @staticmethod
    def get_notification_counts(user_id: int) -> dict[str, int]:
        """
        Get notification counts for a user.

        Returns:
            Dict with feed_unread, friend_requests (follows), and total
        """
        feed_unread = NotificationRepository.get_feed_unread_count(user_id)
        follow_unread = NotificationRepository.get_unread_count_by_type(
            user_id, "follow"
        )
        total_unread = NotificationRepository.get_unread_count(user_id)

        return {
            "feed_unread": feed_unread,
            "friend_requests": follow_unread,
            "total": total_unread,
        }

    @staticmethod
    def get_notifications(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Get notifications for a user with pagination."""
        return NotificationRepository.get_by_user(user_id, limit, offset, unread_only)

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a single notification as read."""
        return NotificationRepository.mark_as_read(notification_id, user_id)

    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Mark all notifications as read. Returns count marked."""
        return NotificationRepository.mark_all_as_read(user_id)

    @staticmethod
    def mark_feed_as_read(user_id: int) -> int:
        """Mark all feed notifications as read. Returns count marked."""
        return NotificationRepository.mark_feed_as_read(user_id)

    @staticmethod
    def mark_follows_as_read(user_id: int) -> int:
        """Mark all follow notifications as read. Returns count marked."""
        return NotificationRepository.mark_follows_as_read(user_id)

    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        return NotificationRepository.delete_by_id(notification_id, user_id)
