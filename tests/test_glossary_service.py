"""Unit tests for GlossaryService — movements glossary CRUD."""

from unittest.mock import MagicMock, patch

import pytest

from rivaflow.core.services.glossary_service import GlossaryService


def _mock_cache():
    """Create a mock cache that behaves like a dict."""
    cache = MagicMock()
    cache.get.return_value = None  # cache miss by default
    return cache


class TestListMovements:
    """Tests for list_movements."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_returns_movements_from_db(self, MockRepo, mock_redis):
        """Should return movements from database on cache miss."""
        mock_redis.return_value = _mock_cache()
        mock_movements = [
            {"id": 1, "name": "armbar", "category": "submission"},
            {"id": 2, "name": "triangle", "category": "submission"},
        ]
        MockRepo.return_value.list_all.return_value = mock_movements

        service = GlossaryService()
        result = service.list_movements(user_id=1)

        assert len(result) == 2
        assert result[0]["name"] == "armbar"

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_search_bypasses_cache(self, MockRepo, mock_redis):
        """Should skip cache when search parameter is provided."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.list_all.return_value = [{"id": 1, "name": "armbar"}]

        service = GlossaryService()
        service.list_movements(user_id=1, search="arm")

        # Should call list_all with search param
        MockRepo.return_value.list_all.assert_called_once_with(
            category=None, search="arm", gi_only=False, nogi_only=False
        )

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_returns_cached_data(self, MockRepo, mock_redis):
        """Should return cached data on cache hit."""
        mock_cache = _mock_cache()
        cached_movements = [{"id": 1, "name": "armbar"}]
        mock_cache.get.return_value = cached_movements
        mock_redis.return_value = mock_cache

        service = GlossaryService()
        result = service.list_movements(user_id=1)

        assert result == cached_movements
        MockRepo.return_value.list_all.assert_not_called()

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_filters_by_category(self, MockRepo, mock_redis):
        """Should pass category filter to repository."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.list_all.return_value = []

        service = GlossaryService()
        service.list_movements(user_id=1, category="guard")

        MockRepo.return_value.list_all.assert_called_once_with(
            category="guard",
            search=None,
            gi_only=False,
            nogi_only=False,
        )


class TestGetMovement:
    """Tests for get_movement."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_returns_movement_by_id(self, MockRepo, mock_redis):
        """Should return a movement by ID."""
        mock_redis.return_value = _mock_cache()
        mock_movement = {"id": 1, "name": "armbar"}
        MockRepo.return_value.get_by_id.return_value = mock_movement

        service = GlossaryService()
        result = service.get_movement(user_id=1, movement_id=1)

        assert result == mock_movement

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_returns_none_when_not_found(self, MockRepo, mock_redis):
        """Should return None when movement does not exist."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.get_by_id.return_value = None

        service = GlossaryService()
        result = service.get_movement(user_id=1, movement_id=999)

        assert result is None

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_custom_videos_bypass_cache(self, MockRepo, mock_redis):
        """Should skip cache when custom videos requested."""
        mock_redis.return_value = _mock_cache()
        mock_movement = {
            "id": 1,
            "name": "armbar",
            "custom_videos": [],
        }
        MockRepo.return_value.get_by_id.return_value = mock_movement

        service = GlossaryService()
        service.get_movement(user_id=1, movement_id=1, include_custom_videos=True)

        MockRepo.return_value.get_by_id.assert_called_once_with(
            1, include_custom_videos=True
        )


class TestCreateCustomMovement:
    """Tests for create_custom_movement."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_creates_movement(self, MockRepo, mock_redis):
        """Should create a custom movement and invalidate cache."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        mock_movement = {"id": 10, "name": "custom sweep"}
        MockRepo.return_value.create_custom.return_value = mock_movement

        service = GlossaryService()
        result = service.create_custom_movement(
            user_id=1, name="custom sweep", category="sweep"
        )

        assert result == mock_movement
        MockRepo.return_value.create_custom.assert_called_once()
        mock_cache.delete_pattern.assert_called_once()


class TestDeleteCustomMovement:
    """Tests for delete_custom_movement."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_deletes_and_invalidates_cache(self, MockRepo, mock_redis):
        """Should delete movement and invalidate cache."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.delete_custom.return_value = True

        service = GlossaryService()
        result = service.delete_custom_movement(user_id=1, movement_id=10)

        assert result is True
        mock_cache.delete_pattern.assert_called_once()

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_does_not_invalidate_on_not_found(self, MockRepo, mock_redis):
        """Should not invalidate cache when movement not found."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.delete_custom.return_value = False

        service = GlossaryService()
        result = service.delete_custom_movement(user_id=1, movement_id=999)

        assert result is False
        mock_cache.delete_pattern.assert_not_called()


class TestDeleteCustomVideo:
    """Tests for delete_custom_video."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_admin_can_delete(self, MockRepo, mock_redis):
        """Should allow admin to delete videos."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.delete_custom_video.return_value = True

        with patch("rivaflow.db.repositories.user_repo.UserRepository") as MockUserRepo:
            MockUserRepo.return_value.get_by_id.return_value = {
                "id": 1,
                "is_admin": True,
            }

            service = GlossaryService()
            result = service.delete_custom_video(user_id=1, video_id=5)

        assert result is True

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_non_admin_raises_permission_error(self, MockRepo, mock_redis):
        """Should raise PermissionError for non-admin users."""
        mock_redis.return_value = _mock_cache()

        with patch("rivaflow.db.repositories.user_repo.UserRepository") as MockUserRepo:
            MockUserRepo.return_value.get_by_id.return_value = {
                "id": 2,
                "is_admin": False,
            }

            service = GlossaryService()
            with pytest.raises(PermissionError, match="Only admins can delete"):
                service.delete_custom_video(user_id=2, video_id=5)


class TestGetCategories:
    """Tests for get_categories."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_returns_categories(self, MockRepo, mock_redis):
        """Should return list of categories."""
        mock_redis.return_value = _mock_cache()
        mock_cats = ["guard", "submission", "sweep", "pass"]
        MockRepo.return_value.get_categories.return_value = mock_cats

        service = GlossaryService()
        result = service.get_categories(user_id=1)

        assert result == mock_cats


class TestTrainedMovements:
    """Tests for list_trained_movements and get_stale_movements."""

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_list_trained(self, MockRepo, mock_redis):
        """Should return movements with training data."""
        mock_redis.return_value = _mock_cache()
        mock_trained = [
            {
                "id": 1,
                "name": "armbar",
                "train_count": 10,
                "last_trained_date": "2025-01-20",
            }
        ]
        MockRepo.return_value.list_with_training_data.return_value = mock_trained

        service = GlossaryService()
        result = service.list_trained_movements(user_id=1, trained_only=True)

        assert len(result) == 1
        assert result[0]["train_count"] == 10

    @patch("rivaflow.core.services.glossary_service.get_redis_client")
    @patch("rivaflow.core.services.glossary_service.GlossaryRepository")
    def test_get_stale(self, MockRepo, mock_redis):
        """Should return stale movements."""
        mock_redis.return_value = _mock_cache()
        mock_stale = [{"id": 1, "name": "triangle", "days_since": 14}]
        MockRepo.return_value.get_stale.return_value = mock_stale

        service = GlossaryService()
        result = service.get_stale_movements(user_id=1, days=7)

        assert len(result) == 1
        MockRepo.return_value.get_stale.assert_called_once_with(user_id=1, days=7)
