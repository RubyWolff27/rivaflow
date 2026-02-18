"""Social features service for relationships, likes, and comments."""

import sqlite3
from typing import Any

from rivaflow.core.services.notification_service import NotificationService
from rivaflow.db.repositories import (
    ActivityCommentRepository,
    ActivityLikeRepository,
    SessionRepository,
    UserRelationshipRepository,
)
from rivaflow.db.repositories.readiness_repo import ReadinessRepository

try:
    import psycopg2

    _PG_INTEGRITY_ERROR = psycopg2.IntegrityError
except ImportError:
    _PG_INTEGRITY_ERROR = type(None)


class SocialService:
    """Business logic for social features: relationships, likes, and comments."""

    # Valid activity types
    VALID_ACTIVITY_TYPES = {"session", "readiness", "rest"}

    @staticmethod
    def follow_user(follower_user_id: int, following_user_id: int) -> dict[str, Any]:
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
            relationship = UserRelationshipRepository.follow(
                follower_user_id, following_user_id
            )

            # Create notification for the followed user
            NotificationService.create_follow_notification(
                following_user_id, follower_user_id
            )

            return relationship
        except (sqlite3.IntegrityError, _PG_INTEGRITY_ERROR) as e:
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
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
    def get_followers(
        user_id: int,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get users who follow this user, with optional pagination."""
        return UserRelationshipRepository.get_followers(
            user_id, limit=limit, offset=offset
        )

    @staticmethod
    def get_following(
        user_id: int,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get users that this user follows, with optional pagination."""
        return UserRelationshipRepository.get_following(
            user_id, limit=limit, offset=offset
        )

    @staticmethod
    def count_followers(user_id: int) -> int:
        """Count total followers for a user."""
        return UserRelationshipRepository.count_followers(user_id)

    @staticmethod
    def count_following(user_id: int) -> int:
        """Count total following for a user."""
        return UserRelationshipRepository.count_following(user_id)

    @staticmethod
    def is_following(follower_user_id: int, following_user_id: int) -> bool:
        """Check if follower_user_id follows following_user_id."""
        return UserRelationshipRepository.is_following(
            follower_user_id, following_user_id
        )

    @staticmethod
    def get_follower_count(user_id: int) -> int:
        """Get count of followers for a user."""
        return UserRelationshipRepository.get_follower_count(user_id)

    @staticmethod
    def get_following_count(user_id: int) -> int:
        """Get count of users this user follows."""
        return UserRelationshipRepository.get_following_count(user_id)

    @staticmethod
    def like_activity(
        user_id: int, activity_type: str, activity_id: int
    ) -> dict[str, Any]:
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

            # Create notification for the activity owner
            activity_owner_id = activity.get("user_id")
            if activity_owner_id:
                NotificationService.create_like_notification(
                    activity_owner_id, user_id, activity_type, activity_id
                )

            return like
        except (sqlite3.IntegrityError, _PG_INTEGRITY_ERROR) as e:
            if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
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
    def get_activity_likes(
        activity_type: str, activity_id: int
    ) -> list[dict[str, Any]]:
        """Get all likes for an activity with user information."""
        return ActivityLikeRepository.get_by_activity(activity_type, activity_id)

    @staticmethod
    def get_like_count(activity_type: str, activity_id: int) -> int:
        """Get count of likes for an activity."""
        return ActivityLikeRepository.get_like_count(activity_type, activity_id)

    @staticmethod
    def has_user_liked(user_id: int, activity_type: str, activity_id: int) -> bool:
        """Check if user has liked an activity."""
        return ActivityLikeRepository.has_user_liked(
            user_id, activity_type, activity_id
        )

    @staticmethod
    def add_comment(
        user_id: int,
        activity_type: str,
        activity_id: int,
        comment_text: str,
        parent_comment_id: int | None = None,
    ) -> dict[str, Any]:
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

        # Create notification for the activity owner
        activity_owner_id = activity.get("user_id")
        if activity_owner_id and comment.get("id"):
            NotificationService.create_comment_notification(
                activity_owner_id, user_id, activity_type, activity_id, comment["id"]
            )

        # If this is a reply, also notify the parent comment author
        if parent_comment_id:
            parent_comment = ActivityCommentRepository.get_by_id(parent_comment_id)
            if parent_comment and parent_comment.get("user_id"):
                parent_author_id = parent_comment["user_id"]
                # Only notify if different from activity owner (to avoid duplicate notifications)
                if parent_author_id != activity_owner_id and comment.get("id"):
                    NotificationService.create_reply_notification(
                        parent_author_id,
                        user_id,
                        activity_type,
                        activity_id,
                        comment["id"],
                    )

        return comment

    @staticmethod
    def get_activity_comments(
        activity_type: str, activity_id: int
    ) -> list[dict[str, Any]]:
        """Get all comments for an activity with user information."""
        return ActivityCommentRepository.get_by_activity(activity_type, activity_id)

    @staticmethod
    def get_comment_count(activity_type: str, activity_id: int) -> int:
        """Get count of comments for an activity."""
        return ActivityCommentRepository.get_comment_count(activity_type, activity_id)

    @staticmethod
    def update_comment(
        comment_id: int, user_id: int, comment_text: str
    ) -> dict[str, Any] | None:
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

        return ActivityCommentRepository.update(
            comment_id, user_id, comment_text.strip()
        )

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

    # ── Friend Connection methods ──

    @staticmethod
    def send_friend_request(
        requester_id: int,
        recipient_id: int,
        connection_source: str | None = None,
        request_message: str | None = None,
    ) -> dict[str, Any]:
        """Send a friend request to another user."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.send_friend_request(
            requester_id=requester_id,
            recipient_id=recipient_id,
            connection_source=connection_source,
            request_message=request_message,
        )

    @staticmethod
    def accept_friend_request(connection_id: int, recipient_id: int) -> dict[str, Any]:
        """Accept a friend request (must be the recipient)."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.accept_friend_request(
            connection_id=connection_id, recipient_id=recipient_id
        )

    @staticmethod
    def decline_friend_request(connection_id: int, recipient_id: int) -> dict[str, Any]:
        """Decline a friend request (must be the recipient)."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.decline_friend_request(
            connection_id=connection_id, recipient_id=recipient_id
        )

    @staticmethod
    def cancel_friend_request(connection_id: int, requester_id: int) -> bool:
        """Cancel a sent friend request (must be the requester)."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.cancel_friend_request(
            connection_id=connection_id, requester_id=requester_id
        )

    @staticmethod
    def get_friends(
        user_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get list of accepted friends for a user."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.get_friends(
            user_id=user_id, limit=limit, offset=offset
        )

    @staticmethod
    def unfriend(user_id: int, friend_user_id: int) -> bool:
        """Remove a friend connection."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.unfriend(
            user_id=user_id, friend_user_id=friend_user_id
        )

    @staticmethod
    def get_pending_requests_received(user_id: int) -> list[dict[str, Any]]:
        """Get pending friend requests received by user."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.get_pending_requests_received(user_id)

    @staticmethod
    def get_pending_requests_sent(user_id: int) -> list[dict[str, Any]]:
        """Get pending friend requests sent by user."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.get_pending_requests_sent(user_id)

    @staticmethod
    def are_friends(user_id: int, other_user_id: int) -> bool:
        """Check if two users are friends."""
        from rivaflow.db.repositories.social_connection_repo import (
            SocialConnectionRepository,
        )

        return SocialConnectionRepository.are_friends(user_id, other_user_id)

    @staticmethod
    def _get_activity(activity_type: str, activity_id: int) -> dict[str, Any] | None:
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

    @staticmethod
    def get_friend_recommendations(user_id: int) -> list[dict[str, Any]]:
        """
        Get friend recommendations based on gym overlap.

        Recommendations prioritize:
        1. Same default gym (from profile)
        2. Same primary session gym
        3. Recent session gym overlap (last 30 days)
        Excludes existing friends (friend_connections).
        """
        from collections import Counter
        from datetime import date, timedelta

        from rivaflow.db.database import convert_query, get_connection
        from rivaflow.db.repositories.profile_repo import ProfileRepository
        from rivaflow.db.repositories.user_repo import UserRepository

        # Get current user's profile gym
        user_profile = ProfileRepository.get(user_id)
        user_default_gym = (user_profile or {}).get("default_gym") or ""

        # Get current user's sessions (last 90 days)
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        user_sessions = SessionRepository.get_by_date_range(
            user_id, start_date, end_date
        )

        # Find user's most frequent session gym
        gym_counts = Counter(
            [s.get("gym_name") for s in user_sessions if s.get("gym_name")]
        )
        user_primary_gym = gym_counts.most_common(1)[0][0] if gym_counts else None

        # Collect all user gym names for recent overlap
        recent_start_str = (date.today() - timedelta(days=30)).isoformat()
        user_recent_gyms = {
            s.get("gym_name")
            for s in user_sessions
            if s.get("gym_name")
            and str(s.get("session_date", ""))[:10] >= recent_start_str
        }

        # Get existing friend IDs from friend_connections
        existing_friend_ids: set[int] = set()
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query(
                        "SELECT requester_id, recipient_id "
                        "FROM friend_connections "
                        "WHERE (requester_id = ? OR recipient_id = ?) "
                        "AND status IN ('accepted', 'pending')"
                    ),
                    (user_id, user_id),
                )
                for row in cursor.fetchall():
                    req_id = row["requester_id"] if hasattr(row, "keys") else row[0]
                    rec_id = row["recipient_id"] if hasattr(row, "keys") else row[1]
                    existing_friend_ids.add(rec_id if req_id == user_id else req_id)
        except Exception:
            pass

        # Get all other users
        all_users = UserRepository.list_all()
        recommendations = []

        for other_user in all_users:
            if other_user["id"] == user_id:
                continue
            if other_user["id"] in existing_friend_ids:
                continue

            reason = None
            score = 0

            # 1. Check default gym from profile
            if user_default_gym:
                other_profile = ProfileRepository.get(other_user["id"])
                other_default_gym = (other_profile or {}).get("default_gym") or ""
                if (
                    other_default_gym
                    and user_default_gym.strip().lower()
                    == other_default_gym.strip().lower()
                ):
                    reason = f"Trains at {user_default_gym}"
                    score = 100

            # 2. Check session-based primary gym overlap
            if not reason:
                other_sessions = SessionRepository.get_by_date_range(
                    other_user["id"], start_date, end_date
                )
                if other_sessions:
                    other_gym_counts = Counter(
                        [s.get("gym_name") for s in other_sessions if s.get("gym_name")]
                    )
                    other_primary_gym = (
                        other_gym_counts.most_common(1)[0][0]
                        if other_gym_counts
                        else None
                    )

                    if (
                        user_primary_gym
                        and other_primary_gym
                        and user_primary_gym == other_primary_gym
                    ):
                        reason = f"Trains at {user_primary_gym}"
                        score = 100

                    # 3. Recent gym overlap (last 30 days)
                    if not reason and user_recent_gyms:
                        other_recent_gyms = {
                            s.get("gym_name")
                            for s in other_sessions
                            if s.get("gym_name")
                            and str(s.get("session_date", ""))[:10] >= recent_start_str
                        }
                        overlap_gyms = user_recent_gyms & other_recent_gyms
                        if overlap_gyms:
                            reason = (
                                "Recently trained at "
                                f"{', '.join(list(overlap_gyms)[:2])}"
                            )
                            score = 80

            if reason:
                recommendations.append(
                    {
                        "id": other_user["id"],
                        "first_name": other_user.get("first_name", ""),
                        "last_name": other_user.get("last_name", ""),
                        "email": other_user.get("email", ""),
                        "reason": reason,
                        "score": score,
                    }
                )

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:10]
