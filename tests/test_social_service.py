"""Unit tests for SocialService — relationships, likes, and comments."""

from unittest.mock import patch

import pytest

from rivaflow.core.services.social_service import SocialService


class TestFollowUser:
    """Tests for follow_user."""

    @patch("rivaflow.core.services.social_service.NotificationService")
    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_follow_creates_relationship(self, MockRelRepo, MockNotif):
        """Should create a follow relationship and return it."""
        mock_rel = {"id": 1, "follower_user_id": 1, "following_user_id": 2}
        MockRelRepo.follow.return_value = mock_rel

        result = SocialService.follow_user(1, 2)

        assert result == mock_rel
        MockRelRepo.follow.assert_called_once_with(1, 2)
        MockNotif.create_follow_notification.assert_called_once_with(2, 1)

    def test_follow_yourself_raises_error(self):
        """Should raise ValueError when trying to follow yourself."""
        with pytest.raises(ValueError, match="Cannot follow yourself"):
            SocialService.follow_user(1, 1)

    @patch("rivaflow.core.services.social_service.NotificationService")
    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_follow_duplicate_raises_error(self, MockRelRepo, MockNotif):
        """Should raise ValueError when already following."""
        import sqlite3

        MockRelRepo.follow.side_effect = sqlite3.IntegrityError(
            "UNIQUE constraint failed"
        )

        with pytest.raises(ValueError, match="Already following"):
            SocialService.follow_user(1, 2)


class TestUnfollowUser:
    """Tests for unfollow_user."""

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_unfollow_returns_true(self, MockRelRepo):
        """Should return True when successfully unfollowed."""
        MockRelRepo.unfollow.return_value = True
        assert SocialService.unfollow_user(1, 2) is True

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_unfollow_not_following_returns_false(self, MockRelRepo):
        """Should return False when not following."""
        MockRelRepo.unfollow.return_value = False
        assert SocialService.unfollow_user(1, 2) is False


class TestGetFollowersAndFollowing:
    """Tests for get_followers and get_following."""

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_get_followers(self, MockRelRepo):
        """Should return list of followers."""
        followers = [{"id": 2, "first_name": "Alice"}]
        MockRelRepo.get_followers.return_value = followers

        result = SocialService.get_followers(1)
        assert result == followers

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_get_following(self, MockRelRepo):
        """Should return list of following."""
        following = [{"id": 3, "first_name": "Bob"}]
        MockRelRepo.get_following.return_value = following

        result = SocialService.get_following(1)
        assert result == following

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_is_following(self, MockRelRepo):
        """Should delegate is_following check to repo."""
        MockRelRepo.is_following.return_value = True
        assert SocialService.is_following(1, 2) is True

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_count_followers(self, MockRelRepo):
        """Should return follower count."""
        MockRelRepo.count_followers.return_value = 42
        assert SocialService.count_followers(1) == 42

    @patch("rivaflow.core.services.social_service.UserRelationshipRepository")
    def test_count_following(self, MockRelRepo):
        """Should return following count."""
        MockRelRepo.count_following.return_value = 10
        assert SocialService.count_following(1) == 10


class TestLikeActivity:
    """Tests for like_activity."""

    @patch("rivaflow.core.services.social_service.NotificationService")
    @patch("rivaflow.core.services.social_service.ActivityLikeRepository")
    @patch("rivaflow.core.services.social_service.SessionRepository")
    def test_like_session(self, MockSessionRepo, MockLikeRepo, MockNotif):
        """Should create a like on a public session."""
        mock_session = {
            "id": 10,
            "user_id": 2,
            "visibility_level": "full",
        }
        MockSessionRepo.get_by_id_any_user.return_value = mock_session

        mock_like = {"id": 1, "user_id": 1, "activity_type": "session"}
        MockLikeRepo.create.return_value = mock_like

        result = SocialService.like_activity(1, "session", 10)

        assert result == mock_like
        MockNotif.create_like_notification.assert_called_once_with(2, 1, "session", 10)

    def test_like_invalid_activity_type(self):
        """Should raise ValueError for invalid activity type."""
        with pytest.raises(ValueError, match="Invalid activity type"):
            SocialService.like_activity(1, "invalid_type", 10)

    @patch("rivaflow.core.services.social_service.SessionRepository")
    def test_like_nonexistent_activity(self, MockSessionRepo):
        """Should raise ValueError when activity not found."""
        MockSessionRepo.get_by_id_any_user.return_value = None

        with pytest.raises(ValueError, match="Activity not found"):
            SocialService.like_activity(1, "session", 999)

    @patch("rivaflow.core.services.social_service.SessionRepository")
    def test_like_private_session_raises(self, MockSessionRepo):
        """Should raise ValueError when liking a private session."""
        mock_session = {
            "id": 10,
            "user_id": 2,
            "visibility_level": "private",
        }
        MockSessionRepo.get_by_id_any_user.return_value = mock_session

        with pytest.raises(ValueError, match="Cannot like private"):
            SocialService.like_activity(1, "session", 10)


class TestAddComment:
    """Tests for add_comment."""

    @patch("rivaflow.core.services.social_service.NotificationService")
    @patch("rivaflow.core.services.social_service.ActivityCommentRepository")
    @patch("rivaflow.core.services.social_service.SessionRepository")
    def test_add_comment_to_session(self, MockSessionRepo, MockCommentRepo, MockNotif):
        """Should create a comment on a public session."""
        mock_session = {
            "id": 10,
            "user_id": 2,
            "visibility_level": "full",
        }
        MockSessionRepo.get_by_id_any_user.return_value = mock_session

        mock_comment = {
            "id": 1,
            "user_id": 1,
            "comment_text": "Nice roll!",
        }
        MockCommentRepo.create.return_value = mock_comment

        result = SocialService.add_comment(1, "session", 10, "Nice roll!")

        assert result == mock_comment
        MockNotif.create_comment_notification.assert_called_once()

    def test_add_empty_comment_raises(self):
        """Should raise ValueError for empty comment text."""
        with pytest.raises(ValueError, match="Comment text cannot be empty"):
            SocialService.add_comment(1, "session", 10, "")

    def test_add_long_comment_raises(self):
        """Should raise ValueError for comment exceeding 1000 chars."""
        with pytest.raises(ValueError, match="Comment text cannot exceed 1000"):
            SocialService.add_comment(1, "session", 10, "x" * 1001)

    @patch("rivaflow.core.services.social_service.SessionRepository")
    def test_add_comment_to_private_session_raises(self, MockSessionRepo):
        """Should raise ValueError when commenting on private session."""
        mock_session = {
            "id": 10,
            "user_id": 2,
            "visibility_level": "private",
        }
        MockSessionRepo.get_by_id_any_user.return_value = mock_session

        with pytest.raises(ValueError, match="Cannot comment on private"):
            SocialService.add_comment(1, "session", 10, "Hello!")


class TestFriendRequests:
    """Tests for friend request methods."""

    @patch("rivaflow.db.repositories.social_connection_repo.SocialConnectionRepository")
    def test_send_friend_request(self, MockConnRepo):
        """Should delegate to SocialConnectionRepository."""
        mock_result = {"id": 1, "status": "pending"}
        MockConnRepo.send_friend_request.return_value = mock_result

        result = SocialService.send_friend_request(1, 2)
        assert result == mock_result

    @patch("rivaflow.db.repositories.social_connection_repo.SocialConnectionRepository")
    def test_accept_friend_request(self, MockConnRepo):
        """Should accept and return the connection."""
        mock_result = {"id": 1, "status": "accepted"}
        MockConnRepo.accept_friend_request.return_value = mock_result

        result = SocialService.accept_friend_request(1, 2)
        assert result == mock_result

    @patch("rivaflow.db.repositories.social_connection_repo.SocialConnectionRepository")
    def test_are_friends(self, MockConnRepo):
        """Should delegate are_friends check."""
        MockConnRepo.are_friends.return_value = True
        assert SocialService.are_friends(1, 2) is True
