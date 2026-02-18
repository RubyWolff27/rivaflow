"""Unit tests for NotificationService — notification creation and management."""

from unittest.mock import patch


from rivaflow.core.services.notification_service import NotificationService


class TestCreateLikeNotification:
    """Tests for create_like_notification."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_creates_like_notification(self, MockRepo):
        """Should create a like notification."""
        mock_notif = {
            "id": 1,
            "notification_type": "like",
            "message": "liked your session",
        }
        MockRepo.check_duplicate.return_value = False
        MockRepo.create.return_value = mock_notif

        result = NotificationService.create_like_notification(
            activity_owner_id=2,
            liker_id=1,
            activity_type="session",
            activity_id=10,
        )

        assert result == mock_notif
        MockRepo.create.assert_called_once_with(
            user_id=2,
            actor_id=1,
            notification_type="like",
            activity_type="session",
            activity_id=10,
            message="liked your session",
        )

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_self_like_returns_none(self, MockRepo):
        """Should return None when user likes their own content."""
        result = NotificationService.create_like_notification(
            activity_owner_id=1,
            liker_id=1,
            activity_type="session",
            activity_id=10,
        )
        assert result is None
        MockRepo.create.assert_not_called()

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_duplicate_returns_none(self, MockRepo):
        """Should return None for duplicate like notification."""
        MockRepo.check_duplicate.return_value = True

        result = NotificationService.create_like_notification(
            activity_owner_id=2,
            liker_id=1,
            activity_type="session",
            activity_id=10,
        )
        assert result is None
        MockRepo.create.assert_not_called()


class TestCreateCommentNotification:
    """Tests for create_comment_notification."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_creates_comment_notification(self, MockRepo):
        """Should create a comment notification."""
        mock_notif = {"id": 2, "notification_type": "comment"}
        MockRepo.create.return_value = mock_notif

        result = NotificationService.create_comment_notification(
            activity_owner_id=2,
            commenter_id=1,
            activity_type="session",
            activity_id=10,
            comment_id=5,
        )

        assert result == mock_notif
        MockRepo.create.assert_called_once_with(
            user_id=2,
            actor_id=1,
            notification_type="comment",
            activity_type="session",
            activity_id=10,
            comment_id=5,
            message="commented on your session",
        )

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_self_comment_returns_none(self, MockRepo):
        """Should return None when user comments on own content."""
        result = NotificationService.create_comment_notification(
            activity_owner_id=1,
            commenter_id=1,
            activity_type="session",
            activity_id=10,
            comment_id=5,
        )
        assert result is None


class TestCreateReplyNotification:
    """Tests for create_reply_notification."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_creates_reply_notification(self, MockRepo):
        """Should create a reply notification."""
        mock_notif = {"id": 3, "notification_type": "reply"}
        MockRepo.create.return_value = mock_notif

        result = NotificationService.create_reply_notification(
            parent_comment_owner_id=2,
            replier_id=1,
            activity_type="session",
            activity_id=10,
            comment_id=7,
        )

        assert result == mock_notif

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_self_reply_returns_none(self, MockRepo):
        """Should return None when user replies to own comment."""
        result = NotificationService.create_reply_notification(
            parent_comment_owner_id=1,
            replier_id=1,
            activity_type="session",
            activity_id=10,
            comment_id=7,
        )
        assert result is None


class TestCreateFollowNotification:
    """Tests for create_follow_notification."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_creates_follow_notification(self, MockRepo):
        """Should create a follow notification."""
        mock_notif = {"id": 4, "notification_type": "follow"}
        MockRepo.check_duplicate.return_value = False
        MockRepo.create.return_value = mock_notif

        result = NotificationService.create_follow_notification(
            followed_user_id=2, follower_id=1
        )

        assert result == mock_notif

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_duplicate_follow_returns_none(self, MockRepo):
        """Should return None for duplicate follow notification."""
        MockRepo.check_duplicate.return_value = True

        result = NotificationService.create_follow_notification(
            followed_user_id=2, follower_id=1
        )
        assert result is None


class TestCreateStreakNotification:
    """Tests for create_streak_notification."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_notable_streak_creates_notification(self, MockRepo):
        """Should create notification for notable streak milestones."""
        mock_notif = {"id": 5, "notification_type": "streak"}
        MockRepo.create.return_value = mock_notif

        result = NotificationService.create_streak_notification(
            user_id=1, streak_type="checkin", streak_length=7
        )

        assert result == mock_notif

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_non_notable_streak_returns_none(self, MockRepo):
        """Should return None for non-notable streak length."""
        result = NotificationService.create_streak_notification(
            user_id=1, streak_type="checkin", streak_length=5
        )
        assert result is None
        MockRepo.create.assert_not_called()

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_all_notable_thresholds(self, MockRepo):
        """Should only create notifications for specific notable streaks."""
        MockRepo.create.return_value = {"id": 1}

        notable = {7, 14, 21, 30, 50, 75, 100, 150, 200, 365}
        for length in range(1, 400):
            MockRepo.create.reset_mock()
            NotificationService.create_streak_notification(
                user_id=1, streak_type="training", streak_length=length
            )
            if length in notable:
                MockRepo.create.assert_called_once()
            else:
                MockRepo.create.assert_not_called()


class TestGetNotificationCounts:
    """Tests for get_notification_counts."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_returns_counts(self, MockRepo):
        """Should return feed_unread, friend_requests, and total."""
        MockRepo.get_feed_unread_count.return_value = 3
        MockRepo.get_unread_count_by_type.return_value = 1
        MockRepo.get_unread_count.return_value = 4

        result = NotificationService.get_notification_counts(user_id=1)

        assert result["feed_unread"] == 3
        assert result["friend_requests"] == 1
        assert result["total"] == 4


class TestNotificationManagement:
    """Tests for get, mark_as_read, mark_all_as_read, delete."""

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_get_notifications(self, MockRepo):
        """Should delegate to repo with params."""
        mock_notifs = [{"id": 1}, {"id": 2}]
        MockRepo.get_by_user.return_value = mock_notifs

        result = NotificationService.get_notifications(
            user_id=1, limit=10, offset=0, unread_only=True
        )

        assert result == mock_notifs
        MockRepo.get_by_user.assert_called_once_with(1, 10, 0, True)

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_mark_as_read(self, MockRepo):
        """Should mark a notification as read."""
        MockRepo.mark_as_read.return_value = True

        result = NotificationService.mark_as_read(notification_id=1, user_id=1)
        assert result is True

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_mark_all_as_read(self, MockRepo):
        """Should mark all notifications as read and return count."""
        MockRepo.mark_all_as_read.return_value = 5

        result = NotificationService.mark_all_as_read(user_id=1)
        assert result == 5

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_delete_notification(self, MockRepo):
        """Should delete notification."""
        MockRepo.delete_by_id.return_value = True

        result = NotificationService.delete_notification(notification_id=1, user_id=1)
        assert result is True

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_mark_feed_as_read(self, MockRepo):
        """Should mark feed notifications as read."""
        MockRepo.mark_feed_as_read.return_value = 3

        result = NotificationService.mark_feed_as_read(user_id=1)
        assert result == 3

    @patch("rivaflow.core.services.notification_service.NotificationRepository")
    def test_mark_follows_as_read(self, MockRepo):
        """Should mark follow notifications as read."""
        MockRepo.mark_follows_as_read.return_value = 2

        result = NotificationService.mark_follows_as_read(user_id=1)
        assert result == 2
