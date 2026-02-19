"""Unit tests for FeedbackService -- user feedback operations."""

from unittest.mock import patch

from rivaflow.core.services.feedback_service import FeedbackService


class TestCreate:
    """Tests for create."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_creates_feedback_and_returns_id(self, MockRepo):
        """Should create feedback and return its ID."""
        MockRepo.return_value.create.return_value = 10

        service = FeedbackService()
        result = service.create(user_id=1, category="bug", message="Something broke")

        assert result == 10
        MockRepo.return_value.create.assert_called_once_with(
            user_id=1, category="bug", message="Something broke"
        )

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_passes_all_kwargs(self, MockRepo):
        """Should pass all keyword arguments to repository."""
        MockRepo.return_value.create.return_value = 11

        service = FeedbackService()
        service.create(
            user_id=2,
            category="feature",
            message="Add dark mode",
            priority="low",
        )

        MockRepo.return_value.create.assert_called_once_with(
            user_id=2,
            category="feature",
            message="Add dark mode",
            priority="low",
        )


class TestGetById:
    """Tests for get_by_id."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_feedback(self, MockRepo):
        """Should return feedback dict when found."""
        mock_feedback = {
            "id": 10,
            "category": "bug",
            "message": "Issue",
            "status": "open",
        }
        MockRepo.return_value.get_by_id.return_value = mock_feedback

        service = FeedbackService()
        result = service.get_by_id(feedback_id=10)

        assert result == mock_feedback

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when feedback does not exist."""
        MockRepo.return_value.get_by_id.return_value = None

        service = FeedbackService()
        result = service.get_by_id(feedback_id=999)

        assert result is None


class TestListByUser:
    """Tests for list_by_user."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_user_feedback(self, MockRepo):
        """Should return feedback list for a user."""
        mock_feedback = [
            {"id": 1, "category": "bug"},
            {"id": 2, "category": "feature"},
        ]
        MockRepo.return_value.list_by_user.return_value = mock_feedback

        service = FeedbackService()
        result = service.list_by_user(user_id=1)

        assert len(result) == 2
        MockRepo.return_value.list_by_user.assert_called_once_with(1, limit=50)

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_respects_custom_limit(self, MockRepo):
        """Should pass custom limit to repository."""
        MockRepo.return_value.list_by_user.return_value = []

        service = FeedbackService()
        service.list_by_user(user_id=1, limit=10)

        MockRepo.return_value.list_by_user.assert_called_once_with(1, limit=10)

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_empty_list(self, MockRepo):
        """Should return empty list when user has no feedback."""
        MockRepo.return_value.list_by_user.return_value = []

        service = FeedbackService()
        result = service.list_by_user(user_id=99)

        assert result == []


class TestListAll:
    """Tests for list_all."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_lists_all_feedback(self, MockRepo):
        """Should return all feedback with default parameters."""
        mock_feedback = [{"id": 1}, {"id": 2}, {"id": 3}]
        MockRepo.return_value.list_all.return_value = mock_feedback

        service = FeedbackService()
        result = service.list_all()

        assert len(result) == 3
        MockRepo.return_value.list_all.assert_called_once_with(
            status=None, category=None, limit=100, offset=0
        )

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_filters_by_status_and_category(self, MockRepo):
        """Should pass status and category filters to repository."""
        MockRepo.return_value.list_all.return_value = []

        service = FeedbackService()
        service.list_all(status="open", category="bug", limit=20, offset=10)

        MockRepo.return_value.list_all.assert_called_once_with(
            status="open", category="bug", limit=20, offset=10
        )


class TestGetStats:
    """Tests for get_stats."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_stats(self, MockRepo):
        """Should return feedback statistics."""
        mock_stats = {
            "total": 50,
            "open": 10,
            "resolved": 35,
            "closed": 5,
        }
        MockRepo.return_value.get_stats.return_value = mock_stats

        service = FeedbackService()
        result = service.get_stats()

        assert result == mock_stats
        assert result["total"] == 50


class TestUpdateStatus:
    """Tests for update_status."""

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_updates_status(self, MockRepo):
        """Should update feedback status and return True."""
        MockRepo.return_value.update_status.return_value = True

        service = FeedbackService()
        result = service.update_status(
            feedback_id=10, status="resolved", admin_notes="Fixed in v2"
        )

        assert result is True
        MockRepo.return_value.update_status.assert_called_once_with(
            feedback_id=10, status="resolved", admin_notes="Fixed in v2"
        )

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_returns_false_when_not_found(self, MockRepo):
        """Should return False when feedback does not exist."""
        MockRepo.return_value.update_status.return_value = False

        service = FeedbackService()
        result = service.update_status(feedback_id=999, status="closed")

        assert result is False

    @patch("rivaflow.core.services.feedback_service.FeedbackRepository")
    def test_updates_without_admin_notes(self, MockRepo):
        """Should allow updating status without admin notes."""
        MockRepo.return_value.update_status.return_value = True

        service = FeedbackService()
        service.update_status(feedback_id=5, status="in_progress")

        MockRepo.return_value.update_status.assert_called_once_with(
            feedback_id=5, status="in_progress", admin_notes=None
        )
