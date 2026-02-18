"""Service for generating friend suggestions based on multiple signals."""

from typing import Any

from rivaflow.db.repositories.friend_suggestions_repo import FriendSuggestionsRepository
from rivaflow.db.repositories.profile_repo import ProfileRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.social_connection_repo import SocialConnectionRepository
from rivaflow.db.repositories.user_repo import UserRepository


class FriendSuggestionsService:
    """
    Generate friend suggestions using a transparent scoring algorithm.

    Scoring:
    - Same default gym (from profile): 40 points
    - Mutual friends: 5 points each (max 25)
    - Same location city (from profile): 15 points
    - Partner name match: 30 points
    - Similar belt rank (from profile current_grade): 5 points
    - Minimum threshold: 5 points
    """

    def __init__(self):
        self.suggestions_repo = FriendSuggestionsRepository()
        self.user_repo = UserRepository()
        self.connections_repo = SocialConnectionRepository()
        self.session_repo = SessionRepository()

    def generate_suggestions(self, user_id: int, limit: int = 50) -> int:
        """
        Generate friend suggestions for a user.

        Returns:
            Number of suggestions created
        """
        # Clear profile cache and old suggestions
        self._profile_cache: dict[int, dict[str, Any] | None] = {}
        self.suggestions_repo.clear_all_suggestions(user_id)

        # Get current user
        current_user = self.user_repo.get_by_id(user_id)
        if not current_user:
            return 0

        # Get users already connected or pending
        existing_connections = self._get_existing_connection_ids(user_id)

        # Get all potential candidates (users except self and existing connections)
        candidates = self._get_candidate_users(user_id, existing_connections)

        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score, reasons = self._calculate_score(current_user, candidate, user_id)

            if score >= 5:  # Minimum threshold
                mutual_count = len(
                    [r for r in reasons if r.startswith("mutual_friends")]
                )
                scored_candidates.append(
                    {
                        "suggested_user_id": candidate["id"],
                        "score": score,
                        "reasons": reasons,
                        "mutual_friends_count": mutual_count,
                    }
                )

        # Sort by score and take top N
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = scored_candidates[:limit]

        # Save to database
        created_count = 0
        for candidate in top_candidates:
            try:
                self.suggestions_repo.create(
                    user_id=user_id,
                    suggested_user_id=candidate["suggested_user_id"],
                    score=candidate["score"],
                    reasons=candidate["reasons"],
                    mutual_friends_count=candidate["mutual_friends_count"],
                )
                created_count += 1
            except Exception:
                # Skip if duplicate or other error
                continue

        return created_count

    def get_suggestions(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        """Get active friend suggestions for a user."""
        # Check if we have recent suggestions
        suggestions = self.suggestions_repo.get_active_suggestions(user_id, limit)

        # If no suggestions exist or very few, regenerate
        if len(suggestions) < 5:
            self.generate_suggestions(user_id)
            suggestions = self.suggestions_repo.get_active_suggestions(user_id, limit)

        return suggestions

    def dismiss_suggestion(self, user_id: int, suggested_user_id: int) -> bool:
        """Dismiss a friend suggestion."""
        return self.suggestions_repo.dismiss_suggestion(user_id, suggested_user_id)

    def get_browsable_users(
        self, user_id: int, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get all discoverable users as a fallback when suggestions are empty."""
        existing_connections = self._get_existing_connection_ids(user_id)
        candidates = self._get_candidate_users(user_id, existing_connections)

        results = []
        for c in candidates[:limit]:
            profile = ProfileRepository.get(c["id"]) or {}
            # Build display name: prefer profile first+last, then users.display_name
            display_name = c.get("display_name")
            if not display_name:
                first = (profile.get("first_name") or "").strip()
                last = (profile.get("last_name") or "").strip()
                if first or last:
                    display_name = f"{first} {last}".strip()
            results.append(
                {
                    "id": c["id"],
                    "username": c.get("username"),
                    "display_name": display_name,
                    "belt_rank": profile.get("current_grade") or c.get("belt_rank"),
                    "location_city": profile.get("city") or c.get("location_city"),
                    "location_state": profile.get("state") or c.get("location_state"),
                    "default_gym": profile.get("default_gym"),
                    "profile_photo_url": c.get("profile_photo_url"),
                }
            )
        return results

    def _get_existing_connection_ids(self, user_id: int) -> set[int]:
        """Get IDs of users already connected or with pending requests."""
        return SocialConnectionRepository.get_existing_connection_ids(user_id)

    def _get_candidate_users(
        self, user_id: int, exclude_ids: set[int]
    ) -> list[dict[str, Any]]:
        """Get all users who could be suggested (excluding self and connections)."""
        return UserRepository.get_candidate_users(user_id, exclude_ids)

    def _calculate_score(
        self, current_user: dict[str, Any], candidate: dict[str, Any], user_id: int
    ) -> tuple[float, list[str]]:
        """
        Calculate suggestion score and reasons.

        Uses profile table data (default_gym, city, current_grade) which
        users actually populate, rather than the users table social columns.

        Returns:
            (score, reasons) tuple
        """
        score = 0.0
        reasons = []

        # Load profiles for both users (cached per generation run)
        if not hasattr(self, "_profile_cache"):
            self._profile_cache: dict[int, dict[str, Any] | None] = {}

        if user_id not in self._profile_cache:
            self._profile_cache[user_id] = ProfileRepository.get(user_id)
        if candidate["id"] not in self._profile_cache:
            self._profile_cache[candidate["id"]] = ProfileRepository.get(
                candidate["id"]
            )

        user_profile = self._profile_cache[user_id] or {}
        candidate_profile = self._profile_cache[candidate["id"]] or {}

        # 1. Same default gym (from profile): 40 points
        user_gym = (user_profile.get("default_gym") or "").strip().lower()
        candidate_gym = (candidate_profile.get("default_gym") or "").strip().lower()
        if user_gym and candidate_gym and user_gym == candidate_gym:
            score += 40
            reasons.append("same_gym")

        # 2. Mutual friends: 5 points each (max 25)
        mutual_count = self._count_mutual_friends(user_id, candidate["id"])
        if mutual_count > 0:
            mutual_points = min(mutual_count * 5, 25)
            score += mutual_points
            reasons.append(f"mutual_friends:{mutual_count}")

        # 3. Same location city (from profile): 15 points
        user_city = (user_profile.get("city") or "").strip().lower()
        candidate_city = (candidate_profile.get("city") or "").strip().lower()
        if user_city and candidate_city and user_city == candidate_city:
            score += 15
            reasons.append("same_city")

        # 4. Partner name match: 30 points
        if self._has_partner_name_match(user_id, candidate):
            score += 30
            reasons.append("partner_match")

        # 5. Similar belt rank (from profile current_grade): 5 points
        if self._has_similar_belt_from_profile(user_profile, candidate_profile):
            score += 5
            reasons.append("similar_belt")

        return score, reasons

    def _count_mutual_friends(self, user1_id: int, user2_id: int) -> int:
        """Count mutual friends between two users."""
        # Get friends of user1
        user1_friends = self._get_friend_ids(user1_id)

        # Get friends of user2
        user2_friends = self._get_friend_ids(user2_id)

        # Count intersection
        mutual = user1_friends.intersection(user2_friends)
        return len(mutual)

    def _get_friend_ids(self, user_id: int) -> set[int]:
        """Get IDs of all accepted friends for a user."""
        friends = self.connections_repo.get_friends(user_id, limit=1000)
        friend_ids = set()

        for friend in friends:
            friend_ids.add(friend["id"])

        return friend_ids

    def _has_partner_name_match(self, user_id: int, candidate: dict[str, Any]) -> bool:
        """Check if candidate's name appears in user's session partners."""
        candidate_name = candidate.get("display_name") or candidate.get("username", "")
        # Also check profile first+last name
        if not candidate_name and hasattr(self, "_profile_cache"):
            cp = self._profile_cache.get(candidate["id"]) or {}
            first = (cp.get("first_name") or "").strip()
            last = (cp.get("last_name") or "").strip()
            if first or last:
                candidate_name = f"{first} {last}".strip()
        if not candidate_name:
            return False

        # Get user's recent sessions
        sessions = self.session_repo.get_recent(user_id, limit=100)

        # Check if candidate name appears in partners field
        for session in sessions:
            partners = session.get("partners", [])
            if partners and isinstance(partners, list):
                for partner in partners:
                    if partner and candidate_name.lower() in partner.lower():
                        return True

        return False

    def _has_similar_belt(self, user1: dict[str, Any], user2: dict[str, Any]) -> bool:
        """Check if two users have similar belt ranks (users table)."""
        belt_order = ["white", "blue", "purple", "brown", "black"]

        belt1 = (user1.get("belt_rank") or "").lower()
        belt2 = (user2.get("belt_rank") or "").lower()

        if not belt1 or not belt2:
            return False

        try:
            idx1 = belt_order.index(belt1)
            idx2 = belt_order.index(belt2)

            # Within 1 belt rank
            return abs(idx1 - idx2) <= 1
        except ValueError:
            return False

    def _has_similar_belt_from_profile(
        self, profile1: dict[str, Any], profile2: dict[str, Any]
    ) -> bool:
        """Check if two users have similar belt ranks using profile current_grade."""
        belt_order = ["white", "blue", "purple", "brown", "black"]

        grade1 = (profile1.get("current_grade") or "").strip().lower()
        grade2 = (profile2.get("current_grade") or "").strip().lower()

        if not grade1 or not grade2:
            return False

        try:
            idx1 = belt_order.index(grade1)
            idx2 = belt_order.index(grade2)
            return abs(idx1 - idx2) <= 1
        except ValueError:
            return False
