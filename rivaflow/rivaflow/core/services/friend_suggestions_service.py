"""Service for generating friend suggestions based on multiple signals."""
from typing import Any

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.friend_suggestions_repo import FriendSuggestionsRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.social_connection_repo import SocialConnectionRepository
from rivaflow.db.repositories.user_repo import UserRepository


class FriendSuggestionsService:
    """
    Generate friend suggestions using a transparent scoring algorithm.

    Scoring:
    - Same primary gym: 40 points
    - Mutual friends: 5 points each (max 25)
    - Same location (city): 15 points
    - Partner name match: 30 points
    - Similar belt rank: 5 points
    - Minimum threshold: 10 points
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
        # Clear old suggestions
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

            if score >= 10:  # Minimum threshold
                mutual_count = len([r for r in reasons if r.startswith("mutual_friends")])
                scored_candidates.append({
                    "suggested_user_id": candidate["id"],
                    "score": score,
                    "reasons": reasons,
                    "mutual_friends_count": mutual_count,
                })

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

    def _get_existing_connection_ids(self, user_id: int) -> set[int]:
        """Get IDs of users already connected or with pending requests."""
        existing_ids = set()

        # Get all connections (accepted, pending, blocked)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT requester_id, recipient_id FROM friend_connections
                    WHERE (requester_id = ? OR recipient_id = ?)
                    AND status IN ('accepted', 'pending', 'blocked')
                """),
                (user_id, user_id)
            )
            rows = cursor.fetchall()

            for row in rows:
                if hasattr(row, 'keys'):
                    req_id = row["requester_id"]
                    rec_id = row["recipient_id"]
                else:
                    req_id = row[0]
                    rec_id = row[1]

                if req_id == user_id:
                    existing_ids.add(rec_id)
                else:
                    existing_ids.add(req_id)

        return existing_ids

    def _get_candidate_users(self, user_id: int, exclude_ids: set[int]) -> list[dict[str, Any]]:
        """Get all users who could be suggested (excluding self and connections)."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get all users except self and existing connections
            exclude_list = list(exclude_ids) + [user_id]
            placeholders = ', '.join('?' * len(exclude_list))

            cursor.execute(
                convert_query(f"""
                    SELECT
                        id, username, display_name, belt_rank, belt_stripes,
                        location_city, location_state, primary_gym_id,
                        searchable, profile_visibility
                    FROM users
                    WHERE id NOT IN ({placeholders})
                    AND searchable = TRUE
                    AND profile_visibility IN ('public', 'friends')
                    LIMIT 500
                """),
                exclude_list,
            )
            rows = cursor.fetchall()

            candidates = []
            for row in rows:
                if hasattr(row, 'keys'):
                    candidates.append(dict(row))
                else:
                    candidates.append({
                        "id": row[0],
                        "username": row[1],
                        "display_name": row[2],
                        "belt_rank": row[3],
                        "belt_stripes": row[4],
                        "location_city": row[5],
                        "location_state": row[6],
                        "primary_gym_id": row[7],
                        "searchable": row[8],
                        "profile_visibility": row[9],
                    })

            return candidates

    def _calculate_score(
        self, current_user: dict[str, Any], candidate: dict[str, Any], user_id: int
    ) -> tuple[float, list[str]]:
        """
        Calculate suggestion score and reasons.

        Returns:
            (score, reasons) tuple
        """
        score = 0.0
        reasons = []

        # 1. Same primary gym: 40 points
        if (
            current_user.get("primary_gym_id")
            and candidate.get("primary_gym_id")
            and current_user["primary_gym_id"] == candidate["primary_gym_id"]
        ):
            score += 40
            reasons.append("same_gym")

        # 2. Mutual friends: 5 points each (max 25)
        mutual_count = self._count_mutual_friends(user_id, candidate["id"])
        if mutual_count > 0:
            mutual_points = min(mutual_count * 5, 25)
            score += mutual_points
            reasons.append(f"mutual_friends:{mutual_count}")

        # 3. Same location (city): 15 points
        if (
            current_user.get("location_city")
            and candidate.get("location_city")
            and current_user["location_city"].lower() == candidate["location_city"].lower()
        ):
            score += 15
            reasons.append("same_city")

        # 4. Partner name match: 30 points
        if self._has_partner_name_match(user_id, candidate):
            score += 30
            reasons.append("partner_match")

        # 5. Similar belt rank: 5 points
        if self._has_similar_belt(current_user, candidate):
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
        """Check if two users have similar belt ranks."""
        belt_order = ["white", "blue", "purple", "brown", "black"]

        belt1 = user1.get("belt_rank", "").lower()
        belt2 = user2.get("belt_rank", "").lower()

        if not belt1 or not belt2:
            return False

        try:
            idx1 = belt_order.index(belt1)
            idx2 = belt_order.index(belt2)

            # Within 1 belt rank
            return abs(idx1 - idx2) <= 1
        except ValueError:
            return False
