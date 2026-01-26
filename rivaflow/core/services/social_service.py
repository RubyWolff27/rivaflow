"""Social features service for relationships, likes, and comments."""
from typing import List, Optional, Dict, Any
import sqlite3

from rivaflow.db.repositories import (
    UserRelationshipRepository,
    ActivityLikeRepository,
    ActivityCommentRepository,
    SessionRepository,
)
from rivaflow.db.repositories.readiness_repo import ReadinessRepository


class SocialService:
    """Business logic for social features: relationships, likes, and comments."""

    # Valid activity types
    VALID_ACTIVITY_TYPES = {"session", "readiness", "rest"}

    @staticmethod
    def follow_user(follower_user_id: int, following_user_id: int) -> Dict[str, Any]:
        """
        Follow another user.

        Args:
            follower_user_id: User who is following
            following_user_id: User to follow

        Returns:
            The created relationship

        Raises:
            ValueError: If trying to follow yourself or user doesn't exist
            sqlite3.IntegrityError: If already following
        """
        # Validate: can't follow yourself
        if follower_user_id == following_user_id:
            raise ValueError("Cannot follow yourself")

        # Create the relationship
        try:
            relationship = UserRelationshipRepository.follow(follower_user_id, following_user_id)
            return relationship
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("Already following this user")
            raise

    @staticmethod
    def unfollow_user(follower_user_id: int, following_user_id: int) -> bool:
        """
        Unfollow a user.

        Args:
            follower_user_id: User who is unfollowing
            following_user_id: User to unfollow

        Returns:
            True if unfollowed, False if wasn't following
        """
        return UserRelationshipRepository.unfollow(follower_user_id, following_user_id)

    @staticmethod
    def get_followers(user_id: int) -> List[Dict[str, Any]]:
        """Get all users who follow this user."""
        return UserRelationshipRepository.get_followers(user_id)

    @staticmethod
    def get_following(user_id: int) -> List[Dict[str, Any]]:
        """Get all users that this user follows."""
        return UserRelationshipRepository.get_following(user_id)

    @staticmethod
    def is_following(follower_user_id: int, following_user_id: int) -> bool:
        """Check if follower_user_id follows following_user_id."""
        return UserRelationshipRepository.is_following(follower_user_id, following_user_id)

    @staticmethod
    def get_follower_count(user_id: int) -> int:
        """Get count of followers for a user."""
        return UserRelationshipRepository.get_follower_count(user_id)

    @staticmethod
    def get_following_count(user_id: int) -> int:
        """Get count of users this user follows."""
        return UserRelationshipRepository.get_following_count(user_id)

    @staticmethod
    def like_activity(user_id: int, activity_type: str, activity_id: int) -> Dict[str, Any]:
        """
        Like an activity.

        Args:
            user_id: User who is liking
            activity_type: Type of activity ('session', 'readiness', 'rest')
            activity_id: ID of the activity

        Returns:
            The created like

        Raises:
            ValueError: If activity type is invalid, activity doesn't exist, or is private
            sqlite3.IntegrityError: If already liked
        """
        # Validate activity type
        if activity_type not in SocialService.VALID_ACTIVITY_TYPES:
            raise ValueError(f"Invalid activity type: {activity_type}")

        # Validate activity exists and is not private
        activity = SocialService._get_activity(activity_type, activity_id)
        if not activity:
            raise ValueError(f"Activity not found: {activity_type} {activity_id}")

        # Check if activity is private (can't like private activities)
        if activity_type == "session":
            visibility = activity.get("visibility_level", "private")
            if visibility == "private":
                raise ValueError("Cannot like private activities")

        # Create the like
        try:
            like = ActivityLikeRepository.create(user_id, activity_type, activity_id)
            return like
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("Already liked this activity")
            raise

    @staticmethod
    def unlike_activity(user_id: int, activity_type: str, activity_id: int) -> bool:
        """
        Remove a like from an activity.

        Args:
            user_id: User who is unliking
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            True if unliked, False if wasn't liked
        """
        return ActivityLikeRepository.delete(user_id, activity_type, activity_id)

    @staticmethod
    def get_activity_likes(activity_type: str, activity_id: int) -> List[Dict[str, Any]]:
        """Get all likes for an activity with user information."""
        return ActivityLikeRepository.get_by_activity(activity_type, activity_id)

    @staticmethod
    def get_like_count(activity_type: str, activity_id: int) -> int:
        """Get count of likes for an activity."""
        return ActivityLikeRepository.get_like_count(activity_type, activity_id)

    @staticmethod
    def has_user_liked(user_id: int, activity_type: str, activity_id: int) -> bool:
        """Check if user has liked an activity."""
        return ActivityLikeRepository.has_user_liked(user_id, activity_type, activity_id)

    @staticmethod
    def add_comment(
        user_id: int,
        activity_type: str,
        activity_id: int,
        comment_text: str,
        parent_comment_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a comment to an activity.

        Args:
            user_id: User who is commenting
            activity_type: Type of activity
            activity_id: ID of the activity
            comment_text: The comment text (1-1000 characters)
            parent_comment_id: Optional parent comment for nested replies

        Returns:
            The created comment

        Raises:
            ValueError: If activity type is invalid, activity doesn't exist, is private, or text is invalid
        """
        # Validate activity type
        if activity_type not in SocialService.VALID_ACTIVITY_TYPES:
            raise ValueError(f"Invalid activity type: {activity_type}")

        # Validate comment text
        if not comment_text or len(comment_text.strip()) == 0:
            raise ValueError("Comment text cannot be empty")
        if len(comment_text) > 1000:
            raise ValueError("Comment text cannot exceed 1000 characters")

        # Validate activity exists and is not private
        activity = SocialService._get_activity(activity_type, activity_id)
        if not activity:
            raise ValueError(f"Activity not found: {activity_type} {activity_id}")

        # Check if activity is private (can't comment on private activities)
        if activity_type == "session":
            visibility = activity.get("visibility_level", "private")
            if visibility == "private":
                raise ValueError("Cannot comment on private activities")

        # Create the comment
        comment = ActivityCommentRepository.create(
            user_id, activity_type, activity_id, comment_text.strip(), parent_comment_id
        )
        return comment

    @staticmethod
    def get_activity_comments(activity_type: str, activity_id: int) -> List[Dict[str, Any]]:
        """Get all comments for an activity with user information."""
        return ActivityCommentRepository.get_by_activity(activity_type, activity_id)

    @staticmethod
    def get_comment_count(activity_type: str, activity_id: int) -> int:
        """Get count of comments for an activity."""
        return ActivityCommentRepository.get_comment_count(activity_type, activity_id)

    @staticmethod
    def update_comment(comment_id: int, user_id: int, comment_text: str) -> Optional[Dict[str, Any]]:
        """
        Update a comment (user can only update their own comments).

        Args:
            comment_id: The comment ID to update
            user_id: User attempting the update (must be comment owner)
            comment_text: New comment text

        Returns:
            Updated comment or None if not found or user doesn't own it

        Raises:
            ValueError: If comment text is invalid
        """
        # Validate comment text
        if not comment_text or len(comment_text.strip()) == 0:
            raise ValueError("Comment text cannot be empty")
        if len(comment_text) > 1000:
            raise ValueError("Comment text cannot exceed 1000 characters")

        return ActivityCommentRepository.update(comment_id, user_id, comment_text.strip())

    @staticmethod
    def delete_comment(comment_id: int, user_id: int) -> bool:
        """
        Delete a comment (user can only delete their own comments).

        Args:
            comment_id: The comment ID to delete
            user_id: User attempting the deletion (must be comment owner)

        Returns:
            True if deleted, False if not found or user doesn't own it
        """
        return ActivityCommentRepository.delete(comment_id, user_id)

    @staticmethod
    def _get_activity(activity_type: str, activity_id: int) -> Optional[Dict[str, Any]]:
        """
        Internal helper to fetch an activity.

        Args:
            activity_type: Type of activity
            activity_id: ID of the activity

        Returns:
            Activity dict or None if not found
        """
        if activity_type == "session":
            return SessionRepository.get_by_id_any_user(activity_id)
        elif activity_type == "readiness":
            return ReadinessRepository.get_by_id_any_user(activity_id)
        elif activity_type == "rest":
            # For now, rest days don't have a repository, so we'll return a stub
            # This can be implemented when RestDayRepository is created
            return {"id": activity_id, "visibility_level": "full"}
        return None
