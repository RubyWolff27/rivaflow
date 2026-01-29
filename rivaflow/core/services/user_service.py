"""User service for user profile management."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from rivaflow.db.repositories import UserRepository, ProfileRepository, UserRelationshipRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.readiness_repo import ReadinessRepository


class UserService:
    """Business logic for user profile operations."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.profile_repo = ProfileRepository()
        self.social_repo = UserRelationshipRepository()
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get basic user info by ID."""
        return self.user_repo.get_by_id(user_id)

    def search_users(self, query: str, limit: int = 20, exclude_user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for users by name or email.

        Args:
            query: Search query string
            limit: Maximum number of results
            exclude_user_id: User ID to exclude from results

        Returns:
            List of matching users with basic info
        """
        users = self.user_repo.search(query=query, limit=limit)

        # Filter out excluded user
        if exclude_user_id:
            users = [u for u in users if u.get("id") != exclude_user_id]

        return users

    def enrich_users_with_social_status(
        self,
        users: List[Dict[str, Any]],
        current_user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Enrich user list with social relationship status.

        Args:
            users: List of user dictionaries
            current_user_id: ID of the current user

        Returns:
            Users enriched with is_following and follower_count
        """
        enriched = []
        for user in users:
            user_id = user.get("id")

            # Check if current user is following this user
            is_following = self.social_repo.is_following(
                follower_id=current_user_id,
                following_id=user_id
            )

            # Get follower count
            followers = self.social_repo.get_followers(user_id=user_id)
            follower_count = len(followers) if followers else 0

            enriched.append({
                **user,
                "is_following": is_following,
                "follower_count": follower_count
            })

        return enriched

    def get_user_profile(
        self,
        user_id: int,
        requesting_user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's public profile.

        Args:
            user_id: ID of user whose profile to retrieve
            requesting_user_id: ID of user requesting the profile

        Returns:
            User profile with public information, or None if not found
        """
        # Get basic user info
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # Get profile data
        profile = self.profile_repo.get_by_user_id(user_id)

        # Get social stats
        followers = self.social_repo.get_followers(user_id=user_id)
        following = self.social_repo.get_following(user_id=user_id)
        follower_count = len(followers) if followers else 0
        following_count = len(following) if following else 0

        # Check if requesting user is following this user
        is_following = self.social_repo.is_following(
            follower_id=requesting_user_id,
            following_id=user_id
        )

        # Check if this user is following the requester (mutual follow)
        is_followed_by = self.social_repo.is_following(
            follower_id=user_id,
            following_id=requesting_user_id
        )

        # Build public profile
        public_profile = {
            "id": user["id"],
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "email": user.get("email"),  # May want to make this conditional
            "created_at": user.get("created_at"),
            "follower_count": follower_count,
            "following_count": following_count,
            "is_following": is_following,
            "is_followed_by": is_followed_by,
        }

        # Add profile data if exists
        if profile:
            public_profile.update({
                "current_grade": profile.get("current_grade"),
                "default_gym": profile.get("default_gym"),
                "location": profile.get("location"),
                "state": profile.get("state"),
                "bio": profile.get("bio"),  # Will add this field later if needed
            })

        return public_profile

    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's public statistics.

        Args:
            user_id: ID of user

        Returns:
            Dictionary of user stats, or None if user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # Calculate time periods
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        # Get session stats
        all_sessions = self.session_repo.list_by_user(user_id=user_id)
        total_sessions = len(all_sessions) if all_sessions else 0

        # Calculate total training time (hours)
        total_minutes = sum(s.get("duration_minutes", 0) for s in (all_sessions or []))
        total_hours = round(total_minutes / 60, 1)

        # Calculate total rolls
        total_rolls = sum(s.get("roll_count", 0) for s in (all_sessions or []))

        # Recent activity counts
        recent_sessions = [
            s for s in (all_sessions or [])
            if s.get("session_date") and
            datetime.fromisoformat(s["session_date"].replace("Z", "+00:00")) >= week_ago
        ]
        sessions_this_week = len(recent_sessions)

        # Get readiness check-in stats
        all_readiness = self.readiness_repo.list_by_user(user_id=user_id)
        total_check_ins = len(all_readiness) if all_readiness else 0

        return {
            "user_id": user_id,
            "total_sessions": total_sessions,
            "total_hours": total_hours,
            "total_rolls": total_rolls,
            "sessions_this_week": sessions_this_week,
            "total_check_ins": total_check_ins,
            "member_since": user.get("created_at"),
        }
