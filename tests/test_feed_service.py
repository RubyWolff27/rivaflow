"""Unit tests for FeedService — activity feed building."""

from unittest.mock import patch

from rivaflow.core.services.feed_service import FeedService


class TestGetMyFeed:
    """Tests for get_my_feed."""

    @patch("rivaflow.core.services.feed_service.CheckinRepository")
    @patch("rivaflow.core.services.feed_service.ActivityPhotoRepository")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    @patch("rivaflow.core.services.feed_service.paginate_with_cursor")
    def test_returns_feed_with_sessions(
        self, mock_paginate, MockSessionRepo, MockPhotoRepo, MockCheckinRepo
    ):
        """Should build feed items from sessions."""
        mock_sessions = [
            {
                "id": 1,
                "session_date": "2025-01-20",
                "class_type": "gi",
                "gym_name": "Alliance",
                "duration_mins": 60,
                "rolls": 5,
            },
        ]
        MockSessionRepo.return_value.get_by_date_range.return_value = mock_sessions
        MockPhotoRepo.return_value.batch_get_by_activities.return_value = {}
        MockCheckinRepo.get_checkins_range.return_value = []

        mock_paginate.return_value = {
            "items": [{"type": "session"}],
            "total": 1,
        }

        result = FeedService.get_my_feed(user_id=1)

        assert result["total"] == 1
        MockSessionRepo.return_value.get_by_date_range.assert_called_once()

    @patch("rivaflow.core.services.feed_service.CheckinRepository")
    @patch("rivaflow.core.services.feed_service.ActivityPhotoRepository")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    @patch("rivaflow.core.services.feed_service.paginate_with_cursor")
    def test_empty_feed(
        self, mock_paginate, MockSessionRepo, MockPhotoRepo, MockCheckinRepo
    ):
        """Should return empty feed when no sessions exist."""
        MockSessionRepo.return_value.get_by_date_range.return_value = []
        MockPhotoRepo.return_value.batch_get_by_activities.return_value = {}
        MockCheckinRepo.get_checkins_range.return_value = []

        mock_paginate.return_value = {
            "items": [],
            "total": 0,
            "has_more": False,
        }

        result = FeedService.get_my_feed(user_id=1)
        assert result["total"] == 0

    @patch("rivaflow.core.services.feed_service.CheckinRepository")
    @patch("rivaflow.core.services.feed_service.ActivityPhotoRepository")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    @patch("rivaflow.core.services.feed_service.paginate_with_cursor")
    def test_includes_rest_day_checkins(
        self, mock_paginate, MockSessionRepo, MockPhotoRepo, MockCheckinRepo
    ):
        """Should include rest-day checkins in the feed."""
        MockSessionRepo.return_value.get_by_date_range.return_value = []
        MockPhotoRepo.return_value.batch_get_by_activities.return_value = {}
        MockCheckinRepo.get_checkins_range.return_value = [
            {
                "id": 5,
                "checkin_type": "rest",
                "check_date": "2025-01-20",
                "rest_type": "active_recovery",
                "rest_note": "Light stretching",
                "tomorrow_intention": "Train",
            },
        ]

        captured_items = []

        def capture_paginate(items, limit, offset, cursor):
            captured_items.extend(items)
            return {"items": items, "total": len(items), "has_more": False}

        mock_paginate.side_effect = capture_paginate

        FeedService.get_my_feed(user_id=1)

        rest_items = [i for i in captured_items if i["type"] == "rest"]
        assert len(rest_items) == 1
        assert rest_items[0]["data"]["rest_type"] == "active_recovery"

    @patch("rivaflow.core.services.feed_service.FeedService._enrich_with_social_data")
    @patch("rivaflow.core.services.feed_service.CheckinRepository")
    @patch("rivaflow.core.services.feed_service.ActivityPhotoRepository")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    @patch("rivaflow.core.services.feed_service.paginate_with_cursor")
    def test_enrich_social_called_when_enabled(
        self,
        mock_paginate,
        MockSessionRepo,
        MockPhotoRepo,
        MockCheckinRepo,
        mock_enrich,
    ):
        """Should enrich with social data when enrich_social=True."""
        MockSessionRepo.return_value.get_by_date_range.return_value = []
        MockPhotoRepo.return_value.batch_get_by_activities.return_value = {}
        MockCheckinRepo.get_checkins_range.return_value = []
        mock_enrich.return_value = []
        mock_paginate.return_value = {"items": [], "total": 0}

        FeedService.get_my_feed(user_id=1, enrich_social=True)

        mock_enrich.assert_called_once()


class TestGetFriendsFeed:
    """Tests for get_friends_feed."""

    @patch("rivaflow.core.services.feed_service.UserRepository")
    @patch("rivaflow.core.services.feed_service.UserRelationshipRepository")
    def test_empty_when_no_following(self, MockRelRepo, MockUserRepo):
        """Should return empty feed when user follows nobody."""
        MockRelRepo.get_following_user_ids.return_value = []

        result = FeedService.get_friends_feed(user_id=1)

        assert result["items"] == []
        assert result["total"] == 0

    @patch("rivaflow.core.services.feed_service.FeedService._enrich_with_social_data")
    @patch("rivaflow.core.services.feed_service.FeedRepository")
    @patch("rivaflow.core.services.feed_service.paginate_with_cursor")
    @patch("rivaflow.core.services.feed_service.UserRepository")
    @patch("rivaflow.core.services.feed_service.UserRelationshipRepository")
    def test_filters_private_users(
        self,
        MockRelRepo,
        MockUserRepo,
        mock_paginate,
        MockFeedRepo,
        mock_enrich,
    ):
        """Should filter out users with private activity visibility."""
        MockRelRepo.get_following_user_ids.return_value = [2, 3]
        MockUserRepo.get_activity_visibility_bulk.return_value = {
            2: "friends",
            3: "private",
        }

        MockFeedRepo.batch_load_friend_sessions.return_value = []
        mock_enrich.return_value = []
        mock_paginate.return_value = {"items": [], "total": 0}

        FeedService.get_friends_feed(user_id=1)

        # batch_load should only receive user 2 (not 3 who is private)
        MockFeedRepo.batch_load_friend_sessions.assert_called_once()
        call_args = MockFeedRepo.batch_load_friend_sessions.call_args
        assert call_args[0][0] == [2]

    @patch("rivaflow.core.services.feed_service.UserRepository")
    @patch("rivaflow.core.services.feed_service.UserRelationshipRepository")
    def test_empty_when_all_users_private(self, MockRelRepo, MockUserRepo):
        """Should return empty when all followed users are private."""
        MockRelRepo.get_following_user_ids.return_value = [2]
        MockUserRepo.get_activity_visibility_bulk.return_value = {
            2: "private",
        }

        result = FeedService.get_friends_feed(user_id=1)

        assert result["items"] == []
        assert result["total"] == 0


class TestGetUserPublicActivities:
    """Tests for get_user_public_activities."""

    @patch("rivaflow.core.services.feed_service.PrivacyService")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    def test_excludes_private_sessions(self, MockSessionRepo, MockPrivacy):
        """Should not include private sessions in public activities."""
        mock_sessions = [
            {
                "id": 1,
                "session_date": "2025-01-20",
                "class_type": "gi",
                "gym_name": "Alliance",
                "duration_mins": 60,
                "rolls": 5,
                "visibility_level": "private",
                "user_id": 1,
            },
            {
                "id": 2,
                "session_date": "2025-01-21",
                "class_type": "no-gi",
                "gym_name": "Alliance",
                "duration_mins": 90,
                "rolls": 8,
                "visibility_level": "summary",
                "user_id": 1,
            },
        ]
        MockSessionRepo.return_value.get_by_date_range.return_value = mock_sessions
        MockPrivacy.redact_session_for_visibility.return_value = {
            "class_type": "no-gi",
            "gym_name": "Alliance",
            "duration_mins": 90,
        }

        result = FeedService.get_user_public_activities(user_id=1)

        # Only 1 session should appear (private excluded)
        assert result["total"] == 1
        assert len(result["items"]) == 1

    @patch("rivaflow.core.services.feed_service.PrivacyService")
    @patch("rivaflow.core.services.feed_service.SessionRepository")
    def test_pagination(self, MockSessionRepo, MockPrivacy):
        """Should respect limit and offset."""
        mock_sessions = []
        for i in range(10):
            mock_sessions.append(
                {
                    "id": i,
                    "session_date": f"2025-01-{10 + i}",
                    "class_type": "gi",
                    "gym_name": "Gym",
                    "duration_mins": 60,
                    "rolls": 5,
                    "visibility_level": "full",
                    "user_id": 1,
                }
            )
        MockSessionRepo.return_value.get_by_date_range.return_value = mock_sessions
        MockPrivacy.redact_session_for_visibility.side_effect = lambda s, v: s

        result = FeedService.get_user_public_activities(user_id=1, limit=3, offset=0)

        assert result["total"] == 10
        assert len(result["items"]) == 3
        assert result["has_more"] is True


class TestEnrichWithSocialData:
    """Tests for _enrich_with_social_data."""

    @patch("rivaflow.core.services.feed_service.FeedService._batch_get_user_profiles")
    @patch("rivaflow.core.services.feed_service.FeedRepository")
    def test_enriches_items(self, MockFeedRepo, mock_profiles):
        """Should add like_count, comment_count, has_liked to items."""
        MockFeedRepo.batch_get_like_counts.return_value = {("session", 1): 5}
        MockFeedRepo.batch_get_comment_counts.return_value = {("session", 1): 2}
        MockFeedRepo.batch_get_user_likes.return_value = {("session", 1)}
        mock_profiles.return_value = {}

        items = [{"type": "session", "id": 1}]
        result = FeedService._enrich_with_social_data(1, items)

        assert result[0]["like_count"] == 5
        assert result[0]["comment_count"] == 2
        assert result[0]["has_liked"] is True

    @patch("rivaflow.core.services.feed_service.FeedService._batch_get_user_profiles")
    @patch("rivaflow.core.services.feed_service.FeedRepository")
    def test_empty_items_returned_unchanged(self, MockFeedRepo, mock_profiles):
        """Should return empty list unchanged."""
        result = FeedService._enrich_with_social_data(1, [])
        assert result == []
