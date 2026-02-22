"""Unit tests for GradingService — belt promotions and grading history."""

from unittest.mock import patch

from rivaflow.core.services.grading_service import GradingService


class TestCreateGrading:
    """Tests for create_grading."""

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_creates_grading_and_updates_profile(
        self, MockGradingRepo, MockProfileRepo
    ):
        """Should create grading and update profile current_grade."""
        mock_grading = {
            "id": 1,
            "user_id": 1,
            "grade": "Blue",
            "date_graded": "2025-01-20",
            "professor": "Professor X",
        }
        MockGradingRepo.return_value.create.return_value = mock_grading
        MockGradingRepo.return_value.get_latest.return_value = mock_grading

        service = GradingService()
        result = service.create_grading(
            user_id=1,
            grade="Blue",
            date_graded="2025-01-20",
            professor="Professor X",
        )

        assert result == mock_grading
        MockProfileRepo.return_value.update.assert_called_once_with(
            1, current_grade="Blue"
        )

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_creates_with_all_fields(self, MockGradingRepo, MockProfileRepo):
        """Should pass all optional fields to repository."""
        mock_grading = {"id": 1, "grade": "Purple"}
        MockGradingRepo.return_value.create.return_value = mock_grading
        MockGradingRepo.return_value.get_latest.return_value = mock_grading

        service = GradingService()
        service.create_grading(
            user_id=1,
            grade="Purple",
            date_graded="2025-06-15",
            professor="Prof Y",
            instructor_id=42,
            notes="Great promotion",
            photo_url="https://example.com/photo.jpg",
        )

        call_kwargs = MockGradingRepo.return_value.create.call_args[1]
        assert call_kwargs["grade"] == "Purple"
        assert call_kwargs["professor"] == "Prof Y"
        assert call_kwargs["instructor_id"] == 42
        assert call_kwargs["notes"] == "Great promotion"

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_profile_updated_to_latest_grading(self, MockGradingRepo, MockProfileRepo):
        """Should update profile to the latest grading by date, not just the created one."""
        created_grading = {
            "id": 2,
            "grade": "White",
            "date_graded": "2020-01-01",
        }
        latest_grading = {
            "id": 1,
            "grade": "Blue",
            "date_graded": "2024-06-15",
        }
        MockGradingRepo.return_value.create.return_value = created_grading
        MockGradingRepo.return_value.get_latest.return_value = latest_grading

        service = GradingService()
        service.create_grading(user_id=1, grade="White", date_graded="2020-01-01")

        # Should use latest grading's grade, not the one just created
        MockProfileRepo.return_value.update.assert_called_once_with(
            1, current_grade="Blue"
        )


class TestListGradings:
    """Tests for list_gradings."""

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_returns_all_gradings(self, MockGradingRepo, MockProfileRepo):
        """Should return all gradings ordered by date desc."""
        mock_gradings = [
            {"id": 2, "grade": "Blue", "date_graded": "2024-06-15"},
            {"id": 1, "grade": "White", "date_graded": "2022-01-01"},
        ]
        MockGradingRepo.return_value.list_all.return_value = mock_gradings

        service = GradingService()
        result = service.list_gradings(user_id=1)

        assert len(result) == 2
        assert result[0]["grade"] == "Blue"
        MockGradingRepo.return_value.list_all.assert_called_once_with(
            1, order_by="date_graded DESC, id DESC"
        )

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_empty_list(self, MockGradingRepo, MockProfileRepo):
        """Should return empty list when no gradings."""
        MockGradingRepo.return_value.list_all.return_value = []

        service = GradingService()
        result = service.list_gradings(user_id=1)

        assert result == []


class TestGetLatestGrading:
    """Tests for get_latest_grading."""

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_returns_latest(self, MockGradingRepo, MockProfileRepo):
        """Should return the most recent grading."""
        mock_grading = {
            "id": 2,
            "grade": "Purple",
            "date_graded": "2025-06-15",
        }
        MockGradingRepo.return_value.get_latest.return_value = mock_grading

        service = GradingService()
        result = service.get_latest_grading(user_id=1)

        assert result == mock_grading

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_returns_none_when_no_gradings(self, MockGradingRepo, MockProfileRepo):
        """Should return None when no gradings exist."""
        MockGradingRepo.return_value.get_latest.return_value = None

        service = GradingService()
        result = service.get_latest_grading(user_id=1)

        assert result is None


class TestUpdateGrading:
    """Tests for update_grading."""

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_updates_and_refreshes_profile(self, MockGradingRepo, MockProfileRepo):
        """Should update grading and refresh profile grade."""
        updated = {
            "id": 1,
            "grade": "Purple",
            "date_graded": "2025-06-15",
        }
        MockGradingRepo.return_value.update.return_value = updated
        MockGradingRepo.return_value.get_latest.return_value = updated

        service = GradingService()
        result = service.update_grading(user_id=1, grading_id=1, grade="Purple")

        assert result == updated
        MockProfileRepo.return_value.update.assert_called_once_with(
            1, current_grade="Purple"
        )

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_returns_none_when_not_found(self, MockGradingRepo, MockProfileRepo):
        """Should return None when grading not found."""
        MockGradingRepo.return_value.update.return_value = None

        service = GradingService()
        result = service.update_grading(user_id=1, grading_id=999, grade="Black")

        assert result is None
        MockProfileRepo.return_value.update.assert_not_called()

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_passes_all_update_fields(self, MockGradingRepo, MockProfileRepo):
        """Should pass all update fields to repository."""
        MockGradingRepo.return_value.update.return_value = {"id": 1}
        MockGradingRepo.return_value.get_latest.return_value = {
            "id": 1,
            "grade": "Brown",
        }

        service = GradingService()
        service.update_grading(
            user_id=1,
            grading_id=1,
            grade="Brown",
            date_graded="2025-12-01",
            professor="Master Z",
            notes="Deserved",
        )

        call_kwargs = MockGradingRepo.return_value.update.call_args[1]
        assert call_kwargs["grade"] == "Brown"
        assert call_kwargs["date_graded"] == "2025-12-01"
        assert call_kwargs["professor"] == "Master Z"
        assert call_kwargs["notes"] == "Deserved"


class TestDeleteGrading:
    """Tests for delete_grading."""

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_deletes_and_updates_profile(self, MockGradingRepo, MockProfileRepo):
        """Should delete grading and update profile to remaining latest."""
        MockGradingRepo.return_value.delete.return_value = True
        MockGradingRepo.return_value.get_latest.return_value = {
            "id": 1,
            "grade": "White",
        }

        service = GradingService()
        result = service.delete_grading(user_id=1, grading_id=2)

        assert result is True
        MockProfileRepo.return_value.update.assert_called_once_with(
            1, current_grade="White"
        )

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_clears_grade_when_last_deleted(self, MockGradingRepo, MockProfileRepo):
        """Should clear current_grade when last grading is deleted."""
        MockGradingRepo.return_value.delete.return_value = True
        MockGradingRepo.return_value.get_latest.return_value = None

        service = GradingService()
        result = service.delete_grading(user_id=1, grading_id=1)

        assert result is True
        MockProfileRepo.return_value.update.assert_called_once_with(
            1, current_grade=None
        )

    @patch("rivaflow.core.services.grading_service.ProfileRepository")
    @patch("rivaflow.core.services.grading_service.GradingRepository")
    def test_returns_false_when_not_found(self, MockGradingRepo, MockProfileRepo):
        """Should return False when grading not found."""
        MockGradingRepo.return_value.delete.return_value = False

        service = GradingService()
        result = service.delete_grading(user_id=1, grading_id=999)

        assert result is False
        MockProfileRepo.return_value.update.assert_not_called()
