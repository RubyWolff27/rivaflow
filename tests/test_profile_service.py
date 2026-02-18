"""Unit tests for ProfileService — profile get/update operations."""

from unittest.mock import MagicMock, patch

import pytest

from rivaflow.core.services.profile_service import ProfileService


class TestGetProfile:
    """Tests for get_profile."""

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_returns_profile_with_stats(self, MockProfileRepo, MockUserRepo):
        """Should return profile enriched with promotion stats."""
        mock_profile = {
            "user_id": 1,
            "first_name": "Test",
            "default_gym": None,
            "primary_gym_id": None,
            "current_grade": "Blue",
        }
        MockProfileRepo.return_value.get.return_value = mock_profile

        with (
            patch(
                "rivaflow.db.repositories.grading_repo.GradingRepository"
            ) as MockGradingRepo,
            patch(
                "rivaflow.db.repositories.session_repo.SessionRepository"
            ) as MockSessionRepo,
        ):
            MockGradingRepo.return_value.get_latest.return_value = {
                "date_graded": "2024-06-01",
                "grade": "Blue",
            }
            MockSessionRepo.return_value.get_by_date_range.return_value = [
                {"duration_mins": 60},
                {"duration_mins": 90},
            ]

            service = ProfileService()
            result = service.get_profile(user_id=1)

        assert result is not None
        assert result["sessions_since_promotion"] == 2
        assert result["hours_since_promotion"] == 2.5
        assert result["promotion_date"] == "2024-06-01"

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_returns_none_when_no_profile(self, MockProfileRepo, MockUserRepo):
        """Should return None when no profile exists."""
        MockProfileRepo.return_value.get.return_value = None

        service = ProfileService()
        result = service.get_profile(user_id=999)
        assert result is None

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_no_grading_counts_all_sessions(self, MockProfileRepo, MockUserRepo):
        """Should count all sessions when no grading exists."""
        mock_profile = {
            "user_id": 1,
            "default_gym": None,
            "primary_gym_id": None,
            "current_grade": "White",
        }
        MockProfileRepo.return_value.get.return_value = mock_profile

        with (
            patch(
                "rivaflow.db.repositories.grading_repo.GradingRepository"
            ) as MockGradingRepo,
            patch(
                "rivaflow.db.repositories.session_repo.SessionRepository"
            ) as MockSessionRepo,
        ):
            MockGradingRepo.return_value.get_latest.return_value = None
            MockSessionRepo.return_value.get_by_date_range.return_value = [
                {"duration_mins": 60},
                {"duration_mins": 60},
                {"duration_mins": 60},
            ]

            service = ProfileService()
            result = service.get_profile(user_id=1)

        assert result["sessions_since_promotion"] == 3
        assert result["hours_since_promotion"] == 3.0
        assert result["promotion_date"] is None

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_resolves_gym_id_from_default_gym(self, MockProfileRepo, MockUserRepo):
        """Should auto-resolve primary_gym_id from default_gym."""
        mock_profile = {
            "user_id": 1,
            "default_gym": "Alliance, Sydney, NSW, Australia",
            "primary_gym_id": None,
            "current_grade": "White",
        }
        MockProfileRepo.return_value.get.return_value = mock_profile

        with (
            patch(
                "rivaflow.db.repositories.grading_repo.GradingRepository"
            ) as MockGradingRepo,
            patch(
                "rivaflow.db.repositories.session_repo.SessionRepository"
            ) as MockSessionRepo,
            patch("rivaflow.db.repositories.gym_repo.GymRepository") as MockGymRepo,
        ):
            MockGradingRepo.return_value.get_latest.return_value = None
            MockSessionRepo.return_value.get_by_date_range.return_value = []
            MockGymRepo.search.return_value = [{"id": 42, "name": "Alliance"}]

            service = ProfileService()
            service.get_profile(user_id=1)

        MockUserRepo.return_value.update_primary_gym.assert_called_once_with(1, 42)


class TestUpdateProfile:
    """Tests for update_profile."""

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_updates_profile_fields(self, MockProfileRepo, MockUserRepo):
        """Should update profile and return result."""
        updated = {
            "user_id": 1,
            "first_name": "Updated",
            "city": "Melbourne",
        }
        MockProfileRepo.return_value.update.return_value = updated

        service = ProfileService()
        result = service.update_profile(
            user_id=1, first_name="Updated", city="Melbourne"
        )

        assert result["first_name"] == "Updated"
        assert result["city"] == "Melbourne"

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_updates_activity_visibility(self, MockProfileRepo, MockUserRepo):
        """Should update activity_visibility on users table."""
        MockProfileRepo.return_value.update.return_value = {"user_id": 1}

        service = ProfileService()
        result = service.update_profile(user_id=1, activity_visibility="private")

        MockUserRepo.return_value.update_activity_visibility.assert_called_once_with(
            1, "private"
        )
        assert result["activity_visibility"] == "private"

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_resolves_gym_id_on_update(self, MockProfileRepo, MockUserRepo):
        """Should resolve gym_id when default_gym is updated."""
        MockProfileRepo.return_value.update.return_value = {"user_id": 1}

        with patch("rivaflow.db.repositories.gym_repo.GymRepository") as MockGymRepo:
            MockGymRepo.search.return_value = [{"id": 99, "name": "New Gym"}]

            service = ProfileService()
            service.update_profile(user_id=1, default_gym="New Gym, City")

        MockUserRepo.return_value.update_primary_gym.assert_called_once_with(1, 99)


class TestGetDefaultGym:
    """Tests for get_default_gym."""

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_returns_default_gym(self, MockProfileRepo, MockUserRepo):
        """Should return the default gym string."""
        mock_profile = {
            "user_id": 1,
            "default_gym": "Alliance BJJ",
            "primary_gym_id": None,
            "current_grade": "White",
        }
        MockProfileRepo.return_value.get.return_value = mock_profile

        with (
            patch(
                "rivaflow.db.repositories.grading_repo.GradingRepository"
            ) as MockGradingRepo,
            patch(
                "rivaflow.db.repositories.session_repo.SessionRepository"
            ) as MockSessionRepo,
        ):
            MockGradingRepo.return_value.get_latest.return_value = None
            MockSessionRepo.return_value.get_by_date_range.return_value = []

            service = ProfileService()
            result = service.get_default_gym(user_id=1)

        assert result == "Alliance BJJ"

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_returns_none_when_no_profile(self, MockProfileRepo, MockUserRepo):
        """Should return None when no profile."""
        MockProfileRepo.return_value.get.return_value = None

        service = ProfileService()
        result = service.get_default_gym(user_id=999)
        assert result is None


class TestUploadProfilePhoto:
    """Tests for upload_profile_photo."""

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_rejects_invalid_extension(self, MockProfileRepo, MockUserRepo):
        """Should raise ValidationError for invalid file extension."""
        from rivaflow.core.exceptions import ValidationError

        service = ProfileService()
        with pytest.raises(ValidationError, match="Invalid file type"):
            service.upload_profile_photo(
                user_id=1,
                file_content=b"fake",
                filename="photo.exe",
            )

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_rejects_oversized_file(self, MockProfileRepo, MockUserRepo):
        """Should raise ValidationError for files exceeding max size."""
        from rivaflow.core.exceptions import ValidationError

        service = ProfileService()
        oversized = b"x" * (6 * 1024 * 1024)  # 6MB
        with pytest.raises(ValidationError, match="File too large"):
            service.upload_profile_photo(
                user_id=1,
                file_content=oversized,
                filename="photo.jpg",
            )


class TestDeleteProfilePhoto:
    """Tests for delete_profile_photo."""

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_raises_when_no_photo(self, MockProfileRepo, MockUserRepo):
        """Should raise NotFoundError when no photo exists."""
        from rivaflow.core.exceptions import NotFoundError

        MockUserRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "avatar_url": None,
        }

        service = ProfileService()
        with pytest.raises(NotFoundError, match="No profile photo"):
            service.delete_profile_photo(user_id=1)

    @patch("rivaflow.core.services.profile_service.UserRepository")
    @patch("rivaflow.core.services.profile_service.ProfileRepository")
    def test_deletes_existing_photo(self, MockProfileRepo, MockUserRepo):
        """Should delete photo and clear avatar_url."""
        MockUserRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "avatar_url": "https://storage.example.com/avatars/photo.jpg",
        }

        with patch(
            "rivaflow.core.services.storage_service.get_storage"
        ) as mock_get_storage:
            mock_storage = MagicMock()
            mock_get_storage.return_value = mock_storage

            service = ProfileService()
            result = service.delete_profile_photo(user_id=1)

        assert result["message"] == "Profile photo deleted successfully"
        MockUserRepo.return_value.update_avatar.assert_called_once_with(1, None)
