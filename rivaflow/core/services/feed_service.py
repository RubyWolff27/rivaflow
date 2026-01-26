"""Feed service for activity feeds (my activities and contacts activities)."""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from rivaflow.db.repositories import (
    SessionRepository,
    ReadinessRepository,
    UserRelationshipRepository,
    ActivityLikeRepository,
    ActivityCommentRepository,
)
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.core.services.privacy_service import PrivacyService


class FeedService:
    """Service for managing activity feeds."""

    @staticmethod
    def get_my_feed(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        days_back: int = 30,
        enrich_social: bool = False,
    ) -> Dict[str, Any]:
        """
        Get user's own activity feed.

        Args:
            user_id: User ID
            limit: Maximum items to return
            offset: Pagination offset
            days_back: Number of days to look back
            enrich_social: Whether to add social data (likes, comments)

        Returns:
            Feed response with items, total, pagination info
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        session_repo = SessionRepository()
        readiness_repo = ReadinessRepository()
        checkin_repo = CheckinRepository()

        # Get all activity
        sessions = session_repo.get_by_date_range(user_id, start_date, end_date)
        readiness_entries = readiness_repo.get_by_date_range(user_id, start_date, end_date)
        checkins = checkin_repo.get_checkins_range(user_id, start_date, end_date)

        # Build unified feed
        feed_items = []

        # Add sessions
        for session in sessions:
            session_date = session["session_date"]
            if hasattr(session_date, "isoformat"):
                session_date = session_date.isoformat()

            feed_items.append(
                {
                    "type": "session",
                    "date": session_date,
                    "id": session["id"],
                    "data": session,
                    "summary": f"{session['class_type']} at {session['gym_name']} • {session['duration_mins']}min • {session['rolls']} rolls",
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
                feed_items.append(
                    {
                        "type": "readiness",
                        "date": readiness_date,
                        "id": readiness["id"],
                        "data": readiness,
                        "summary": f"Readiness check-in • Score: {composite}/20 • Sleep: {readiness['sleep']}/5",
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

                feed_items.append(
                    {
                        "type": "rest",
                        "date": checkin_date,
                        "id": checkin["id"],
                        "data": checkin,
                        "summary": summary,
                    }
                )

        # Sort by date descending
        feed_items.sort(key=lambda x: x["date"], reverse=True)

        # Enrich with social data if requested
        if enrich_social:
            feed_items = FeedService._enrich_with_social_data(user_id, feed_items)

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
    def get_contacts_feed(
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Get activity feed from users that this user follows (contacts feed).
        Only shows activities with visibility_level != 'private' and applies privacy redaction.

        Args:
            user_id: Current user ID
            limit: Maximum items to return
            offset: Pagination offset
            days_back: Number of days to look back

        Returns:
            Feed response with items, total, pagination info
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

        session_repo = SessionRepository()
        readiness_repo = ReadinessRepository()
        checkin_repo = CheckinRepository()

        feed_items = []

        # Get sessions from followed users (only non-private)
        for followed_user_id in following_user_ids:
            sessions = session_repo.get_by_date_range(followed_user_id, start_date, end_date)

            # Filter out private sessions and apply privacy redaction
            for session in sessions:
                visibility = session.get("visibility_level", "private")
                if visibility == "private":
                    continue

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
                        "owner_user_id": followed_user_id,
                    }
                )

        # For readiness and rest, we'll assume they're shareable for now
        # (Can add visibility controls later if needed)
        for followed_user_id in following_user_ids:
            readiness_entries = readiness_repo.get_by_date_range(followed_user_id, start_date, end_date)

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
                        "owner_user_id": followed_user_id,
                    }
                )

            checkins = checkin_repo.get_checkins_range(followed_user_id, start_date, end_date)
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
                            "owner_user_id": followed_user_id,
                        }
                    )

        # Sort by date descending
        feed_items.sort(key=lambda x: x["date"], reverse=True)

        # Enrich with social data (always enabled for contacts feed)
        feed_items = FeedService._enrich_with_social_data(user_id, feed_items)

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
    def _enrich_with_social_data(user_id: int, feed_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich feed items with social data (like count, comment count, has_liked).

        Args:
            user_id: Current user ID (to check if they liked)
            feed_items: List of feed items

        Returns:
            Enriched feed items with social data
        """
        for item in feed_items:
            activity_type = item["type"]
            activity_id = item["id"]

            # Add like count
            item["like_count"] = ActivityLikeRepository.get_like_count(activity_type, activity_id)

            # Add comment count
            item["comment_count"] = ActivityCommentRepository.get_comment_count(activity_type, activity_id)

            # Add has_liked
            item["has_liked"] = ActivityLikeRepository.has_user_liked(user_id, activity_type, activity_id)

        return feed_items
