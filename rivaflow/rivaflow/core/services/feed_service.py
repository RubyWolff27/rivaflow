"""Feed service for activity feeds (my activities and friends activities)."""

from datetime import date, timedelta
from typing import Any

from rivaflow.cache import CacheKeys, get_redis_client
from rivaflow.core.constants import REST_TYPES
from rivaflow.core.pagination import paginate_with_cursor
from rivaflow.core.services.privacy_service import PrivacyService
from rivaflow.db.repositories import (
    ActivityPhotoRepository,
    SessionRepository,
    UserRelationshipRepository,
    UserRepository,
)
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.feed_repo import FeedRepository


class FeedService:
    """Service for managing activity feeds."""

    @staticmethod
    def get_my_feed(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        cursor: str | None = None,
        days_back: int = 30,
        enrich_social: bool = False,
    ) -> dict[str, Any]:
        """
        Get user's own activity feed with cursor-based pagination.

        Args:
            user_id: User ID
            limit: Maximum items to return
            offset: Pagination offset (deprecated, use cursor instead)
            cursor: Cursor for pagination (format: "date:type:id")
            days_back: Number of days to look back
            enrich_social: Whether to add social data (likes, comments)

        Returns:
            Feed response with items, total, pagination info, and next_cursor
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        session_repo = SessionRepository()
        photo_repo = ActivityPhotoRepository()

        # Get sessions only
        sessions = session_repo.get_by_date_range(user_id, start_date, end_date)

        # Build unified feed items
        feed_items = []
        photo_keys: list[tuple[str, int]] = []

        for session in sessions:
            session_date = session["session_date"]
            if hasattr(session_date, "isoformat"):
                session_date = session_date.isoformat()

            photo_keys.append(("session", session["id"]))

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": session,
                    "summary": f"{session['class_type']} at {session['gym_name']} \u2022 {session['duration_mins']}min \u2022 {session['rolls']} rolls",
                    "thumbnail": None,
                    "photo_count": 0,
                }
            )

        # Get rest-day checkins and merge into feed
        checkins = CheckinRepository.get_checkins_range(user_id, start_date, end_date)
        for checkin in checkins:
            if checkin["checkin_type"] != "rest":
                continue
            check_date = checkin["check_date"]
            if hasattr(check_date, "isoformat"):
                check_date = check_date.isoformat()
            rest_type = checkin.get("rest_type") or ""
            label = REST_TYPES.get(rest_type, rest_type.title() or "Rest")
            feed_items.append(
                {
                    "type": "rest",
                    "date": check_date,
                    "id": checkin["id"],
                    "data": {
                        "rest_type": rest_type,
                        "rest_note": checkin.get("rest_note"),
                        "tomorrow_intention": checkin.get("tomorrow_intention"),
                        "check_date": check_date,
                    },
                    "summary": f"Rest Day \u2014 {label}",
                    "thumbnail": None,
                    "photo_count": 0,
                }
            )

        # Batch load all photos
        if photo_keys:
            photos_map = photo_repo.batch_get_by_activities(user_id, photo_keys)
            for item in feed_items:
                photos = photos_map.get((item["type"], item["id"]), [])
                item["thumbnail"] = photos[0]["file_path"] if photos else None
                item["photo_count"] = len(photos)

        # Sort by date descending, then by type and id for consistent ordering
        feed_items.sort(key=lambda x: (x["date"], x["type"], x["id"]), reverse=True)

        # Enrich with social data if requested
        if enrich_social:
            feed_items = FeedService._enrich_with_social_data(user_id, feed_items)

        # Apply cursor-based pagination
        return paginate_with_cursor(feed_items, limit, offset, cursor)

    @staticmethod
    def get_friends_feed(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        cursor: str | None = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """
        Get activity feed from users that this user follows (friends feed) with cursor-based pagination.
        Only shows activities with visibility_level != 'private' and applies privacy redaction.
        Excludes users who have set activity_visibility to 'private'.

        Args:
            user_id: Current user ID
            limit: Maximum items to return
            offset: Pagination offset (deprecated, use cursor instead)
            cursor: Cursor for pagination (format: "date:type:id")
            days_back: Number of days to look back

        Returns:
            Feed response with items, total, pagination info, and next_cursor
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        # Get list of users this user follows
        following_user_ids = UserRelationshipRepository.get_following_user_ids(user_id)

        if not following_user_ids:
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        # Filter out users who have set activity_visibility to 'private'
        visibility_map = UserRepository.get_activity_visibility_bulk(following_user_ids)
        visible_user_ids = [
            uid
            for uid in following_user_ids
            if visibility_map.get(uid, "friends") != "private"
        ]

        if not visible_user_ids:
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        # Batch load activities from all visible followed users
        feed_items = FeedService._batch_load_friend_activities(
            visible_user_ids, start_date, end_date
        )

        # Sort by date descending, then by type and id for consistent ordering
        feed_items.sort(key=lambda x: (x["date"], x["type"], x["id"]), reverse=True)

        # Enrich with social data (always enabled for friends feed)
        feed_items = FeedService._enrich_with_social_data(user_id, feed_items)

        # Apply cursor-based pagination
        return paginate_with_cursor(feed_items, limit, offset, cursor)

    @staticmethod
    def _enrich_with_social_data(
        user_id: int, feed_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Enrich feed items with social data (like count, comment count, has_liked).
        Also enriches with cached user profiles for feed owners.
        Uses batch queries to avoid N+1 query problem.
        """
        if not feed_items:
            return feed_items

        # Build items_by_type for batch queries
        items_by_type: dict[str, list[int]] = {}
        for item in feed_items:
            activity_type = item["type"]
            if activity_type not in items_by_type:
                items_by_type[activity_type] = []
            items_by_type[activity_type].append(item["id"])

        # Batch load all like counts, comment counts, and user likes
        like_counts = FeedRepository.batch_get_like_counts(items_by_type)
        comment_counts = FeedRepository.batch_get_comment_counts(items_by_type)
        user_likes = FeedRepository.batch_get_user_likes(user_id, items_by_type)

        # Batch load user profiles with caching
        owner_profiles = FeedService._batch_get_user_profiles(feed_items)

        # Enrich items with preloaded data
        for item in feed_items:
            activity_key = (item["type"], item["id"])
            item["like_count"] = like_counts.get(activity_key, 0)
            item["comment_count"] = comment_counts.get(activity_key, 0)
            item["has_liked"] = activity_key in user_likes

            # Add owner profile if available
            owner_user_id = item.get("owner_user_id")
            if owner_user_id and owner_user_id in owner_profiles:
                item["owner"] = owner_profiles[owner_user_id]

        return feed_items

    @staticmethod
    def _batch_load_friend_activities(
        user_ids: list[int], start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Batch load session activities from multiple users in optimized queries."""
        if not user_ids:
            return []

        rows = FeedRepository.batch_load_friend_sessions(user_ids, start_date, end_date)

        feed_items = []
        for session in rows:
            visibility = session.get("visibility_level", "private")

            # Apply privacy redaction
            redacted_session = PrivacyService.redact_session(session, visibility)
            if not redacted_session:
                continue

            session_date = redacted_session.get("session_date")
            if hasattr(session_date, "isoformat"):
                session_date = session_date.isoformat()

            # Build summary based on what's available after redaction
            summary_parts = []
            if redacted_session.get("class_type"):
                summary_parts.append(redacted_session["class_type"])
            if redacted_session.get("gym_name"):
                summary_parts.append(f"at {redacted_session['gym_name']}")
            if redacted_session.get("duration_mins"):
                summary_parts.append(f"{redacted_session['duration_mins']}min")
            if redacted_session.get("rolls") is not None:
                summary_parts.append(f"{redacted_session['rolls']} rolls")

            summary = (
                " \u2022 ".join(summary_parts) if summary_parts else "Training session"
            )

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": redacted_session,
                    "summary": summary,
                    "owner_user_id": session["user_id"],
                }
            )

        return feed_items

    @staticmethod
    def get_user_public_activities(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        requesting_user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Get a user's public activities (for profile viewing).
        """
        session_repo = SessionRepository()

        # Get recent activities (last 90 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

        sessions = session_repo.get_by_date_range(user_id, start_date, end_date)

        # Build unified feed
        feed_items = []

        # Add sessions (only non-private ones)
        for session in sessions:
            visibility = session.get("visibility_level", "summary")
            if visibility == "private":
                continue

            session_date = session["session_date"]
            if hasattr(session_date, "isoformat"):
                session_date = session_date.isoformat()

            # Apply privacy redaction based on visibility
            session_data = PrivacyService.redact_session_for_visibility(
                session, visibility
            )

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": session_data,
                    "summary": f"{session_data.get('class_type', 'Training')} at {session_data.get('gym_name', 'Gym')} \u2022 {session_data.get('duration_mins', 0)}min",
                    "owner_user_id": user_id,
                }
            )

        # Sort by date descending
        feed_items.sort(key=lambda x: x["date"], reverse=True)

        # Enrich with social data if requesting user provided
        if requesting_user_id:
            feed_items = FeedService._enrich_with_social_data(
                requesting_user_id, feed_items
            )

        # Apply pagination
        total_items = len(feed_items)
        paginated_items = feed_items[offset : offset + limit]

        return {
            "items": paginated_items,
            "total": total_items,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_items,
        }

    @staticmethod
    def _batch_get_user_profiles(
        feed_items: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        """Batch load user profiles for feed item owners with Redis caching."""
        cache = get_redis_client()

        # Collect unique owner user IDs
        owner_user_ids = set()
        for item in feed_items:
            owner_user_id = item.get("owner_user_id")
            if owner_user_id:
                owner_user_ids.add(owner_user_id)

        if not owner_user_ids:
            return {}

        profiles: dict[int, dict[str, Any]] = {}
        uncached_user_ids = []

        # Try to get from cache first
        for uid in owner_user_ids:
            cache_key = CacheKeys.user_basic(uid)
            cached_profile = cache.get(cache_key)

            if cached_profile:
                profiles[uid] = {
                    "id": cached_profile.get("id"),
                    "first_name": cached_profile.get("first_name"),
                    "last_name": cached_profile.get("last_name"),
                }
            else:
                uncached_user_ids.append(uid)

        # Batch load uncached users from database
        if uncached_user_ids:
            users = UserRepository.get_users_by_ids(uncached_user_ids)

            for user in users:
                uid = user["id"]

                # Cache full user profile
                cache.set(
                    CacheKeys.user_basic(uid),
                    user,
                    ttl=CacheKeys.TTL_15_MINUTES,
                )

                # Add to profiles (minimal info for feed)
                profiles[uid] = {
                    "id": uid,
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                }

        return profiles
