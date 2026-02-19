"""Unit tests for UserService -- user profile and stats management."""

from unittest.mock import MagicMock, patch

from rivaflow.core.services.user_service import UserService


def _mock_cache():
    """Create a mock cache that behaves like a dict."""
    cache = MagicMock()
    cache.get.return_value = None  # cache miss by default
    return cache


class TestGetUserById:
    """Tests for get_user_by_id."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_user_from_db(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return user from database on cache miss."""
        mock_redis.return_value = _mock_cache()
        mock_user = {"id": 1, "first_name": "Carlos", "email": "c@test.com"}
        MockUserRepo.return_value.get_by_id.return_value = mock_user

        service = UserService()
        result = service.get_user_by_id(user_id=1)

        assert result == mock_user
        MockUserRepo.return_value.get_by_id.assert_called_once_with(1)

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_cached_user(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return cached data on cache hit."""
        mock_cache = _mock_cache()
        cached_user = {"id": 1, "first_name": "Carlos"}
        mock_cache.get.return_value = cached_user
        mock_redis.return_value = mock_cache

        service = UserService()
        result = service.get_user_by_id(user_id=1)

        assert result == cached_user
        MockUserRepo.return_value.get_by_id.assert_not_called()

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_none_when_not_found(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return None when user does not exist."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = None

        service = UserService()
        result = service.get_user_by_id(user_id=999)

        assert result is None


class TestSearchUsers:
    """Tests for search_users."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_matching_users(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return users matching the query."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.search.return_value = [
            {"id": 1, "first_name": "Carlos"},
            {"id": 2, "first_name": "Carmen"},
        ]

        service = UserService()
        result = service.search_users(query="Car")

        assert len(result) == 2

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_excludes_specified_user(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should exclude user with exclude_user_id."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.search.return_value = [
            {"id": 1, "first_name": "Carlos"},
            {"id": 2, "first_name": "Carmen"},
        ]

        service = UserService()
        result = service.search_users(query="Car", exclude_user_id=1)

        assert len(result) == 1
        assert result[0]["id"] == 2

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_empty_when_no_match(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return empty list when no users match."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.search.return_value = []

        service = UserService()
        result = service.search_users(query="zzz")

        assert result == []


class TestEnrichUsersWithSocialStatus:
    """Tests for enrich_users_with_social_status."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_enriches_with_follow_status(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should add is_following and follower_count to each user."""
        mock_redis.return_value = _mock_cache()
        MockSocialRepo.return_value.is_following.return_value = True
        MockSocialRepo.return_value.get_followers.return_value = [
            {"user_id": 3},
            {"user_id": 4},
        ]

        service = UserService()
        users = [{"id": 2, "first_name": "Carlos"}]
        result = service.enrich_users_with_social_status(users, current_user_id=1)

        assert len(result) == 1
        assert result[0]["is_following"] is True
        assert result[0]["follower_count"] == 2

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_handles_no_followers(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return follower_count=0 when no followers."""
        mock_redis.return_value = _mock_cache()
        MockSocialRepo.return_value.is_following.return_value = False
        MockSocialRepo.return_value.get_followers.return_value = None

        service = UserService()
        users = [{"id": 2, "first_name": "Carlos"}]
        result = service.enrich_users_with_social_status(users, current_user_id=1)

        assert result[0]["follower_count"] == 0
        assert result[0]["is_following"] is False


class TestGetUserProfile:
    """Tests for get_user_profile."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_profile_with_social_stats(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should build public profile with social stats."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "first_name": "Carlos",
            "last_name": "Silva",
            "email": "c@test.com",
            "avatar_url": None,
            "created_at": "2024-01-01",
        }
        MockProfileRepo.return_value.get.return_value = {
            "current_grade": "blue",
            "default_gym": "Alliance",
            "location": "Sydney",
            "state": "NSW",
            "bio": "OSS",
        }
        MockSocialRepo.return_value.get_followers.return_value = [{"user_id": 2}]
        MockSocialRepo.return_value.get_following.return_value = [
            {"user_id": 3},
            {"user_id": 4},
        ]
        MockSocialRepo.return_value.is_following.side_effect = [
            True,
            False,
        ]

        service = UserService()
        result = service.get_user_profile(user_id=1, requesting_user_id=5)

        assert result["first_name"] == "Carlos"
        assert result["follower_count"] == 1
        assert result["following_count"] == 2
        assert result["is_following"] is True
        assert result["is_followed_by"] is False
        assert result["current_grade"] == "blue"
        # Email hidden from other users
        assert result["email"] is None

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_shows_email_to_self(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should show email when user views own profile."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "first_name": "Carlos",
            "email": "c@test.com",
        }
        MockProfileRepo.return_value.get.return_value = None
        MockSocialRepo.return_value.get_followers.return_value = []
        MockSocialRepo.return_value.get_following.return_value = []
        MockSocialRepo.return_value.is_following.return_value = False

        service = UserService()
        result = service.get_user_profile(user_id=1, requesting_user_id=1)

        assert result["email"] == "c@test.com"

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_none_when_user_not_found(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return None when user does not exist."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = None

        service = UserService()
        result = service.get_user_profile(user_id=999, requesting_user_id=1)

        assert result is None


class TestGetUserStats:
    """Tests for get_user_stats."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_computes_stats(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should compute user statistics from sessions."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "created_at": "2024-01-01",
        }
        MockSessionRepo.return_value.list_by_user.return_value = [
            {
                "id": 1,
                "duration_minutes": 60,
                "roll_count": 5,
                "session_date": "2020-01-01T00:00:00",
            },
            {
                "id": 2,
                "duration_minutes": 90,
                "roll_count": 8,
                "session_date": "2020-01-02T00:00:00",
            },
        ]
        MockReadinessRepo.return_value.list_by_user.return_value = [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]

        service = UserService()
        result = service.get_user_stats(user_id=1)

        assert result["total_sessions"] == 2
        assert result["total_hours"] == 2.5
        assert result["total_rolls"] == 13
        assert result["total_check_ins"] == 3
        assert result["member_since"] == "2024-01-01"

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_returns_none_when_user_not_found(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should return None when user does not exist."""
        mock_redis.return_value = _mock_cache()
        MockUserRepo.return_value.get_by_id.return_value = None

        service = UserService()
        result = service.get_user_stats(user_id=999)

        assert result is None


class TestInvalidateUserCache:
    """Tests for invalidate_user_cache."""

    @patch("rivaflow.core.services.user_service.get_redis_client")
    @patch("rivaflow.core.services.user_service.ReadinessRepository")
    @patch("rivaflow.core.services.user_service.SessionRepository")
    @patch("rivaflow.core.services.user_service.UserRelationshipRepository")
    @patch("rivaflow.core.services.user_service.ProfileRepository")
    @patch("rivaflow.core.services.user_service.UserRepository")
    def test_deletes_user_cache_pattern(
        self,
        MockUserRepo,
        MockProfileRepo,
        MockSocialRepo,
        MockSessionRepo,
        MockReadinessRepo,
        mock_redis,
    ):
        """Should call delete_pattern with user-specific pattern."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache

        service = UserService()
        service.invalidate_user_cache(user_id=1)

        mock_cache.delete_pattern.assert_called_once()
