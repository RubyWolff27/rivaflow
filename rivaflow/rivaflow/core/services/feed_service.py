"""Feed service for activity feeds (my activities and friends activities)."""
from datetime import date, timedelta
from typing import Any

from rivaflow.cache import CacheKeys, get_redis_client
from rivaflow.core.pagination import paginate_with_cursor
from rivaflow.core.services.privacy_service import PrivacyService
from rivaflow.db.repositories import (
    ActivityPhotoRepository,
    ReadinessRepository,
    SessionRepository,
    UserRelationshipRepository,
    UserRepository,
)
from rivaflow.db.repositories.checkin_repo import CheckinRepository


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
        readiness_repo = ReadinessRepository()
        checkin_repo = CheckinRepository()
        photo_repo = ActivityPhotoRepository()

        # Get all activity
        sessions = session_repo.get_by_date_range(user_id, start_date, end_date)
        readiness_entries = readiness_repo.get_by_date_range(user_id, start_date, end_date)
        checkins = checkin_repo.get_checkins_range(user_id, start_date, end_date)

        # Build unified feed
        feed_items = []

        # Add sessions with photos
        for session in sessions:
            session_date = session["session_date"]
            if hasattr(session_date, "isoformat"):
                session_date = session_date.isoformat()

            # Get photos for this session
            photos = photo_repo.get_by_activity(user_id, "session", session["id"])
            thumbnail = photos[0]["file_path"] if photos else None

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": session,
                    "summary": f"{session['class_type']} at {session['gym_name']} • {session['duration_mins']}min • {session['rolls']} rolls",
                    "thumbnail": thumbnail,
                    "photo_count": len(photos),
                }
            )

        # Add readiness check-ins (only if not already covered by session/rest check-in)
        session_dates = {s["session_date"] for s in sessions}
        rest_dates = {c["check_date"] for c in checkins if c["checkin_type"] == "rest"}

        for readiness in readiness_entries:
            readiness_date = readiness["check_date"]
            if hasattr(readiness_date, "isoformat"):
                readiness_date = readiness_date.isoformat()

            if readiness_date not in session_dates and readiness_date not in rest_dates:
                composite = readiness.get("composite_score", 0)

                # Get photos for this readiness entry
                photos = photo_repo.get_by_activity(user_id, "readiness", readiness["id"])
                thumbnail = photos[0]["file_path"] if photos else None

                feed_items.append(
                    {
                        "type": "readiness",
                        "date": readiness_date,
                        "id": readiness["id"],
                        "data": readiness,
                        "summary": f"Readiness check-in • Score: {composite}/20 • Sleep: {readiness['sleep']}/5",
                        "thumbnail": thumbnail,
                        "photo_count": len(photos),
                    }
                )

        # Add rest days
        for checkin in checkins:
            if checkin["checkin_type"] == "rest":
                checkin_date = checkin["check_date"]
                if hasattr(checkin_date, "isoformat"):
                    checkin_date = checkin_date.isoformat()

                rest_type_label = {
                    "recovery": "Active recovery",
                    "life": "Life got in the way",
                    "injury": "Injury/rehab",
                    "travel": "Traveling",
                }.get(checkin["rest_type"], checkin["rest_type"])

                summary = f"Rest day • {rest_type_label}"
                if checkin.get("rest_note"):
                    summary += f" • {checkin['rest_note']}"

                # Get photos for this rest day
                photos = photo_repo.get_by_activity(user_id, "rest", checkin["id"])
                thumbnail = photos[0]["file_path"] if photos else None

                feed_items.append(
                    {
                        "type": "rest",
                        "date": checkin_date,
                        "id": checkin["id"],
                        "data": checkin,
                        "summary": summary,
                        "thumbnail": thumbnail,
                        "photo_count": len(photos),
                    }
                )

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

        # Batch load activities from all followed users to avoid N+1 queries
        feed_items = FeedService._batch_load_friend_activities(
            following_user_ids, start_date, end_date
        )

        # Sort by date descending, then by type and id for consistent ordering
        feed_items.sort(key=lambda x: (x["date"], x["type"], x["id"]), reverse=True)

        # Enrich with social data (always enabled for friends feed)
        feed_items = FeedService._enrich_with_social_data(user_id, feed_items)

        # Apply cursor-based pagination
        return paginate_with_cursor(feed_items, limit, offset, cursor)

    @staticmethod
    def _enrich_with_social_data(user_id: int, feed_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Enrich feed items with social data (like count, comment count, has_liked).
        Also enriches with cached user profiles for feed owners.
        Uses batch queries to avoid N+1 query problem.

        Args:
            user_id: Current user ID (to check if they liked)
            feed_items: List of feed items

        Returns:
            Enriched feed items with social data and user profiles
        """
        if not feed_items:
            return feed_items

        # Batch load all like counts, comment counts, and user likes in single queries
        like_counts = FeedService._batch_get_like_counts(feed_items)
        comment_counts = FeedService._batch_get_comment_counts(feed_items)
        user_likes = FeedService._batch_get_user_likes(user_id, feed_items)

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
        """
        Batch load activities from multiple users in optimized queries.

        Args:
            user_ids: List of user IDs to load activities from
            start_date: Start date for activity range
            end_date: End date for activity range

        Returns:
            List of feed items from all users
        """
        from rivaflow.db.database import convert_query, get_connection

        if not user_ids:
            return []

        feed_items = []
        placeholders = ",".join("?" * len(user_ids))

        with get_connection() as conn:
            cursor = conn.cursor()

            # Batch load sessions from all followed users
            query = convert_query(f"""
                SELECT
                    id, user_id, session_date, class_type, gym_name, location,
                    duration_mins, intensity, rolls, submissions_for, submissions_against,
                    partners, techniques, notes, visibility_level, instructor_name
                FROM sessions
                WHERE user_id IN ({placeholders})
                    AND session_date BETWEEN ? AND ?
                    AND visibility_level != 'private'
                ORDER BY session_date DESC
            """)
            cursor.execute(query, user_ids + [start_date, end_date])

            for row in cursor.fetchall():
                session = dict(row)
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

                summary = " • ".join(summary_parts) if summary_parts else "Training session"

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

            # Batch load readiness entries
            query = convert_query(f"""
                SELECT
                    id, user_id, check_date, sleep, stress, soreness, energy,
                    composite_score, hotspot_note, weight_kg
                FROM readiness
                WHERE user_id IN ({placeholders})
                    AND check_date BETWEEN ? AND ?
                ORDER BY check_date DESC
            """)
            cursor.execute(query, user_ids + [start_date, end_date])

            for row in cursor.fetchall():
                readiness = dict(row)
                readiness_date = readiness["check_date"]
                if hasattr(readiness_date, "isoformat"):
                    readiness_date = readiness_date.isoformat()

                composite = readiness.get("composite_score", 0)
                feed_items.append(
                    {
                        "type": "readiness",
                        "date": readiness_date,
                        "id": readiness["id"],
                        "data": readiness,
                        "summary": f"Readiness check-in • Score: {composite}/20",
                        "owner_user_id": readiness["user_id"],
                    }
                )

            # Batch load rest day check-ins
            query = convert_query(f"""
                SELECT
                    id, user_id, check_date, checkin_type, rest_type, rest_note
                FROM daily_checkins
                WHERE user_id IN ({placeholders})
                    AND check_date BETWEEN ? AND ?
                    AND checkin_type = 'rest'
                ORDER BY check_date DESC
            """)
            cursor.execute(query, user_ids + [start_date, end_date])

            for row in cursor.fetchall():
                checkin = dict(row)
                checkin_date = checkin["check_date"]
                if hasattr(checkin_date, "isoformat"):
                    checkin_date = checkin_date.isoformat()

                rest_type_label = {
                    "recovery": "Active recovery",
                    "life": "Life got in the way",
                    "injury": "Injury/rehab",
                    "travel": "Traveling",
                }.get(checkin["rest_type"], checkin["rest_type"])

                feed_items.append(
                    {
                        "type": "rest",
                        "date": checkin_date,
                        "id": checkin["id"],
                        "data": checkin,
                        "summary": f"Rest day • {rest_type_label}",
                        "owner_user_id": checkin["user_id"],
                    }
                )

        return feed_items

    @staticmethod
    def _batch_get_like_counts(feed_items: list[dict[str, Any]]) -> dict[tuple, int]:
        """
        Batch load like counts for all feed items in a single query.

        Args:
            feed_items: List of feed items

        Returns:
            Dictionary mapping (activity_type, activity_id) to like count
        """
        from rivaflow.db.database import convert_query, get_connection

        if not feed_items:
            return {}

        # Group items by type for efficient querying
        items_by_type = {}
        for item in feed_items:
            activity_type = item["type"]
            if activity_type not in items_by_type:
                items_by_type[activity_type] = []
            items_by_type[activity_type].append(item["id"])

        like_counts = {}
        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_id, COUNT(*) as count
                    FROM activity_likes
                    WHERE activity_type = ? AND activity_id IN ({placeholders})
                    GROUP BY activity_id
                """)
                cursor.execute(query, [activity_type] + activity_ids)
                for row in cursor.fetchall():
                    like_counts[(activity_type, row["activity_id"])] = row["count"]

        return like_counts

    @staticmethod
    def _batch_get_comment_counts(feed_items: list[dict[str, Any]]) -> dict[tuple, int]:
        """
        Batch load comment counts for all feed items in a single query.

        Args:
            feed_items: List of feed items

        Returns:
            Dictionary mapping (activity_type, activity_id) to comment count
        """
        from rivaflow.db.database import convert_query, get_connection

        if not feed_items:
            return {}

        # Group items by type for efficient querying
        items_by_type = {}
        for item in feed_items:
            activity_type = item["type"]
            if activity_type not in items_by_type:
                items_by_type[activity_type] = []
            items_by_type[activity_type].append(item["id"])

        comment_counts = {}
        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_id, COUNT(*) as count
                    FROM activity_comments
                    WHERE activity_type = ? AND activity_id IN ({placeholders})
                    GROUP BY activity_id
                """)
                cursor.execute(query, [activity_type] + activity_ids)
                for row in cursor.fetchall():
                    comment_counts[(activity_type, row["activity_id"])] = row["count"]

        return comment_counts

    @staticmethod
    def _batch_get_user_likes(user_id: int, feed_items: list[dict[str, Any]]) -> set:
        """
        Batch load user's likes for all feed items in a single query.

        Args:
            user_id: User ID to check likes for
            feed_items: List of feed items

        Returns:
            Set of (activity_type, activity_id) tuples that the user has liked
        """
        from rivaflow.db.database import convert_query, get_connection

        if not feed_items:
            return set()

        # Group items by type for efficient querying
        items_by_type = {}
        for item in feed_items:
            activity_type = item["type"]
            if activity_type not in items_by_type:
                items_by_type[activity_type] = []
            items_by_type[activity_type].append(item["id"])

        user_likes = set()
        with get_connection() as conn:
            cursor = conn.cursor()
            for activity_type, activity_ids in items_by_type.items():
                if not activity_ids:
                    continue

                placeholders = ",".join("?" * len(activity_ids))
                query = convert_query(f"""
                    SELECT activity_type, activity_id
                    FROM activity_likes
                    WHERE user_id = ? AND activity_type = ? AND activity_id IN ({placeholders})
                """)
                cursor.execute(query, [user_id, activity_type] + activity_ids)
                for row in cursor.fetchall():
                    user_likes.add((row["activity_type"], row["activity_id"]))

        return user_likes

    @staticmethod
    def get_user_public_activities(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        requesting_user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Get a user's public activities (for profile viewing).

        Args:
            user_id: ID of user whose activities to retrieve
            limit: Maximum items to return
            offset: Pagination offset
            requesting_user_id: ID of user requesting the activities

        Returns:
            Feed response with public items only
        """
        session_repo = SessionRepository()
        readiness_repo = ReadinessRepository()
        checkin_repo = CheckinRepository()

        # Get recent activities (last 90 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=90)

        # Get all activity
        sessions = session_repo.get_by_date_range(user_id, start_date, end_date)
        readiness_entries = readiness_repo.get_by_date_range(user_id, start_date, end_date)
        checkins = checkin_repo.get_checkins_range(user_id, start_date, end_date)

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
            session_data = PrivacyService.redact_session_for_visibility(session, visibility)

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": session_data,
                    "summary": f"{session_data.get('class_type', 'Training')} at {session_data.get('gym_name', 'Gym')} • {session_data.get('duration_mins', 0)}min",
                    "owner_user_id": user_id,
                }
            )

        # Add readiness check-ins (only public ones)
        for readiness in readiness_entries:
            readiness_date = readiness["check_date"]
            if hasattr(readiness_date, "isoformat"):
                readiness_date = readiness_date.isoformat()

            composite = readiness.get("composite_score", 0)
            feed_items.append(
                {
                    "type": "readiness",
                    "date": readiness_date,
                    "id": readiness["id"],
                    "data": readiness,
                    "summary": f"Readiness check-in • Score: {composite}/20",
                    "owner_user_id": user_id,
                }
            )

        # Add rest days (public)
        for checkin in checkins:
            if checkin["checkin_type"] == "rest":
                checkin_date = checkin["check_date"]
                if hasattr(checkin_date, "isoformat"):
                    checkin_date = checkin_date.isoformat()

                rest_type_label = {
                    "recovery": "Active recovery",
                    "life": "Life got in the way",
                    "injury": "Injury/rehab",
                    "travel": "Traveling",
                }.get(checkin["rest_type"], checkin["rest_type"])

                feed_items.append(
                    {
                        "type": "rest",
                        "date": checkin_date,
                        "id": checkin["id"],
                        "data": checkin,
                        "summary": f"Rest day • {rest_type_label}",
                        "owner_user_id": user_id,
                    }
                )

        # Sort by date descending
        feed_items.sort(key=lambda x: x["date"], reverse=True)

        # Enrich with social data if requesting user provided
        if requesting_user_id:
            feed_items = FeedService._enrich_with_social_data(requesting_user_id, feed_items)

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
    def _batch_get_user_profiles(feed_items: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
        """
        Batch load user profiles for feed item owners with Redis caching.

        Args:
            feed_items: List of feed items

        Returns:
            Dictionary mapping user_id to user profile info
        """
        cache = get_redis_client()
        UserRepository()

        # Collect unique owner user IDs
        owner_user_ids = set()
        for item in feed_items:
            owner_user_id = item.get("owner_user_id")
            if owner_user_id:
                owner_user_ids.add(owner_user_id)

        if not owner_user_ids:
            return {}

        profiles = {}
        uncached_user_ids = []

        # Try to get from cache first
        for user_id in owner_user_ids:
            cache_key = CacheKeys.user_basic(user_id)
            cached_profile = cache.get(cache_key)

            if cached_profile:
                profiles[user_id] = {
                    "id": cached_profile.get("id"),
                    "first_name": cached_profile.get("first_name"),
                    "last_name": cached_profile.get("last_name"),
                }
            else:
                uncached_user_ids.append(user_id)

        # Batch load uncached users from database
        if uncached_user_ids:
            from rivaflow.db.database import convert_query, get_connection

            with get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" * len(uncached_user_ids))
                query = convert_query(f"""
                    SELECT id, first_name, last_name, email
                    FROM users
                    WHERE id IN ({placeholders})
                """)
                cursor.execute(query, uncached_user_ids)

                for row in cursor.fetchall():
                    user = dict(row)
                    user_id = user["id"]

                    # Cache full user profile
                    cache.set(CacheKeys.user_basic(user_id), user, ttl=CacheKeys.TTL_15_MINUTES)

                    # Add to profiles (minimal info for feed)
                    profiles[user_id] = {
                        "id": user_id,
                        "first_name": user.get("first_name"),
                        "last_name": user.get("last_name"),
                    }

        return profiles
