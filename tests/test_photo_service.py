"""Unit tests for PhotoService — activity photo CRUD + storage."""

from unittest.mock import MagicMock, patch

from rivaflow.core.services.photo_service import PhotoService


class TestCreate:
    """Tests for PhotoService.create."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_creates_photo_and_returns_id(self, MockRepo):
        """Should delegate to repo and return new photo ID."""
        MockRepo.return_value.create.return_value = 42

        service = PhotoService()
        result = service.create(
            user_id=1, activity_type="session", activity_id=10, url="https://img/1.jpg"
        )

        assert result == 42
        MockRepo.return_value.create.assert_called_once_with(
            user_id=1, activity_type="session", activity_id=10, url="https://img/1.jpg"
        )

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_passes_all_kwargs_to_repo(self, MockRepo):
        """Should forward arbitrary kwargs to the repository."""
        MockRepo.return_value.create.return_value = 5

        service = PhotoService()
        service.create(
            user_id=2,
            activity_type="checkin",
            activity_id=7,
            url="https://img/2.jpg",
            caption="My photo",
        )

        call_kwargs = MockRepo.return_value.create.call_args[1]
        assert call_kwargs["caption"] == "My photo"


class TestGetById:
    """Tests for PhotoService.get_by_id."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_photo_when_found(self, MockRepo):
        """Should return photo dict when it exists."""
        expected = {"id": 1, "url": "https://img/1.jpg", "caption": "Test"}
        MockRepo.return_value.get_by_id.return_value = expected

        service = PhotoService()
        result = service.get_by_id(user_id=1, photo_id=1)

        assert result == expected
        MockRepo.return_value.get_by_id.assert_called_once_with(1, 1)

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when photo does not exist."""
        MockRepo.return_value.get_by_id.return_value = None

        service = PhotoService()
        result = service.get_by_id(user_id=1, photo_id=999)

        assert result is None


class TestGetByActivity:
    """Tests for PhotoService.get_by_activity."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_photos_for_activity(self, MockRepo):
        """Should return list of photos for a given activity."""
        photos = [
            {"id": 1, "url": "https://img/1.jpg"},
            {"id": 2, "url": "https://img/2.jpg"},
        ]
        MockRepo.return_value.get_by_activity.return_value = photos

        service = PhotoService()
        result = service.get_by_activity(
            user_id=1, activity_type="session", activity_id=10
        )

        assert len(result) == 2
        MockRepo.return_value.get_by_activity.assert_called_once_with(1, "session", 10)

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_empty_list_when_no_photos(self, MockRepo):
        """Should return empty list when no photos exist."""
        MockRepo.return_value.get_by_activity.return_value = []

        service = PhotoService()
        result = service.get_by_activity(
            user_id=1, activity_type="session", activity_id=10
        )

        assert result == []


class TestCountByActivity:
    """Tests for PhotoService.count_by_activity."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_count(self, MockRepo):
        """Should return count of photos for activity."""
        MockRepo.return_value.count_by_activity.return_value = 3

        service = PhotoService()
        result = service.count_by_activity(
            user_id=1, activity_type="session", activity_id=10
        )

        assert result == 3

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_zero_when_no_photos(self, MockRepo):
        """Should return 0 when no photos exist."""
        MockRepo.return_value.count_by_activity.return_value = 0

        service = PhotoService()
        result = service.count_by_activity(
            user_id=1, activity_type="session", activity_id=99
        )

        assert result == 0


class TestUpdateCaption:
    """Tests for PhotoService.update_caption."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_updates_caption_returns_true(self, MockRepo):
        """Should return True when caption update succeeds."""
        MockRepo.return_value.update_caption.return_value = True

        service = PhotoService()
        result = service.update_caption(
            user_id=1, photo_id=1, caption="Updated caption"
        )

        assert result is True
        MockRepo.return_value.update_caption.assert_called_once_with(
            1, 1, "Updated caption"
        )

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_false_when_photo_not_found(self, MockRepo):
        """Should return False when photo does not exist."""
        MockRepo.return_value.update_caption.return_value = False

        service = PhotoService()
        result = service.update_caption(
            user_id=1, photo_id=999, caption="Does not matter"
        )

        assert result is False


class TestDelete:
    """Tests for PhotoService.delete."""

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_deletes_and_returns_true(self, MockRepo):
        """Should delete photo and return True."""
        MockRepo.return_value.delete.return_value = True

        service = PhotoService()
        result = service.delete(user_id=1, photo_id=1)

        assert result is True
        MockRepo.return_value.delete.assert_called_once_with(1, 1)

    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_returns_false_when_not_found(self, MockRepo):
        """Should return False when photo to delete does not exist."""
        MockRepo.return_value.delete.return_value = False

        service = PhotoService()
        result = service.delete(user_id=1, photo_id=999)

        assert result is False


class TestDeleteFile:
    """Tests for PhotoService.delete_file."""

    @patch("rivaflow.core.services.photo_service.get_storage")
    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_deletes_file_from_storage(self, MockRepo, mock_get_storage):
        """Should call storage.delete with correct folder and filename."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        service = PhotoService()
        service.delete_file(folder="photos/user_1", filename="img.jpg")

        mock_storage.delete.assert_called_once_with("photos/user_1", "img.jpg")


class TestUploadFile:
    """Tests for PhotoService.upload_file."""

    @patch("rivaflow.core.services.photo_service.get_storage")
    @patch("rivaflow.core.services.photo_service.ActivityPhotoRepository")
    def test_uploads_file_and_returns_url(self, MockRepo, mock_get_storage):
        """Should upload file and return URL from storage."""
        mock_storage = MagicMock()
        mock_storage.upload.return_value = "https://cdn.example.com/photos/img.jpg"
        mock_get_storage.return_value = mock_storage

        service = PhotoService()
        result = service.upload_file(
            folder="photos/user_1", filename="img.jpg", content=b"image-data"
        )

        assert result == "https://cdn.example.com/photos/img.jpg"
        mock_storage.upload.assert_called_once_with(
            "photos/user_1", "img.jpg", b"image-data"
        )
