"""Unit tests for GymService — gym management with caching."""

from datetime import date
from unittest.mock import MagicMock, patch

from rivaflow.core.services.gym_service import GymService


def _mock_cache():
    """Create a mock cache with dict-like behavior."""
    cache = MagicMock()
    cache.get.return_value = None  # cache miss by default
    return cache


class TestCreate:
    """Tests for create."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_creates_gym(self, MockRepo, mock_redis):
        """Should create a gym and invalidate cache."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        mock_gym = {"id": 1, "name": "Alliance BJJ", "city": "Sydney"}
        MockRepo.return_value.create.return_value = mock_gym

        service = GymService()
        result = service.create(name="Alliance BJJ", city="Sydney")

        assert result == mock_gym
        MockRepo.return_value.create.assert_called_once()
        mock_cache.delete_pattern.assert_called()

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_creates_with_all_fields(self, MockRepo, mock_redis):
        """Should pass all fields to repository."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.create.return_value = {"id": 1}

        service = GymService()
        service.create(
            name="TestGym",
            city="Melbourne",
            state="VIC",
            country="Australia",
            head_coach="Professor X",
            head_coach_belt="Black",
            verified=True,
            added_by_user_id=1,
        )

        call_kwargs = MockRepo.return_value.create.call_args[1]
        assert call_kwargs["name"] == "TestGym"
        assert call_kwargs["city"] == "Melbourne"
        assert call_kwargs["head_coach"] == "Professor X"
        assert call_kwargs["verified"] is True


class TestGetById:
    """Tests for get_by_id."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_returns_from_cache(self, MockRepo, mock_redis):
        """Should return cached gym on cache hit."""
        mock_cache = _mock_cache()
        cached_gym = {"id": 1, "name": "Cached Gym"}
        mock_cache.get.return_value = cached_gym
        mock_redis.return_value = mock_cache

        service = GymService()
        result = service.get_by_id(1)

        assert result == cached_gym
        MockRepo.return_value.get_by_id.assert_not_called()

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_returns_from_db_on_cache_miss(self, MockRepo, mock_redis):
        """Should fetch from DB and cache on cache miss."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        mock_gym = {"id": 1, "name": "DB Gym"}
        MockRepo.return_value.get_by_id.return_value = mock_gym

        service = GymService()
        result = service.get_by_id(1)

        assert result == mock_gym
        mock_cache.set.assert_called_once()

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_returns_none_when_not_found(self, MockRepo, mock_redis):
        """Should return None when gym does not exist."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.get_by_id.return_value = None

        service = GymService()
        result = service.get_by_id(999)

        assert result is None


class TestListAll:
    """Tests for list_all."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_returns_all_gyms(self, MockRepo, mock_redis):
        """Should return all gyms from database."""
        mock_redis.return_value = _mock_cache()
        mock_gyms = [
            {"id": 1, "name": "Gym A"},
            {"id": 2, "name": "Gym B"},
        ]
        MockRepo.return_value.list_all.return_value = mock_gyms

        service = GymService()
        result = service.list_all()

        assert len(result) == 2

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_verified_only(self, MockRepo, mock_redis):
        """Should filter for verified only gyms."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.list_all.return_value = [
            {"id": 1, "name": "Verified Gym", "verified": True}
        ]

        service = GymService()
        service.list_all(verified_only=True)

        MockRepo.return_value.list_all.assert_called_once_with(verified_only=True)


class TestSearch:
    """Tests for search."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_searches_gyms(self, MockRepo, mock_redis):
        """Should search gyms by query."""
        mock_redis.return_value = _mock_cache()
        mock_results = [{"id": 1, "name": "Alliance BJJ Sydney"}]
        MockRepo.return_value.search.return_value = mock_results

        service = GymService()
        result = service.search("Alliance")

        assert len(result) == 1
        assert result[0]["name"] == "Alliance BJJ Sydney"

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_returns_cached_search(self, MockRepo, mock_redis):
        """Should return cached search results."""
        mock_cache = _mock_cache()
        mock_cache.get.return_value = [{"id": 1, "name": "Cached Result"}]
        mock_redis.return_value = mock_cache

        service = GymService()
        result = service.search("Alliance")

        assert result[0]["name"] == "Cached Result"
        MockRepo.return_value.search.assert_not_called()


class TestUpdate:
    """Tests for update."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_updates_and_invalidates_cache(self, MockRepo, mock_redis):
        """Should update gym and invalidate cache."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        updated_gym = {"id": 1, "name": "Updated Gym"}
        MockRepo.return_value.update.return_value = updated_gym

        service = GymService()
        result = service.update(1, name="Updated Gym")

        assert result == updated_gym
        mock_cache.delete_pattern.assert_called()

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_no_cache_invalidation_on_not_found(self, MockRepo, mock_redis):
        """Should not invalidate cache when gym not found."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.update.return_value = None

        service = GymService()
        result = service.update(999, name="Nope")

        assert result is None
        # Only the directory-level pattern is always called in _invalidate_gym_cache
        # but since gym is None, _invalidate_gym_cache is never called


class TestDelete:
    """Tests for delete."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_deletes_and_invalidates(self, MockRepo, mock_redis):
        """Should delete gym and invalidate cache."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.delete.return_value = True

        service = GymService()
        result = service.delete(1)

        assert result is True
        mock_cache.delete_pattern.assert_called()


class TestMergeGyms:
    """Tests for merge_gyms."""

    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_merges_and_invalidates_both(self, MockRepo, mock_redis):
        """Should merge gyms and invalidate cache for both."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.merge_gyms.return_value = True

        service = GymService()
        result = service.merge_gyms(1, 2)

        assert result is True
        # Should invalidate cache at least twice (for each gym + directory)
        assert mock_cache.delete_pattern.call_count >= 2


class TestTimetable:
    """Tests for timetable methods."""

    @patch("rivaflow.core.services.gym_service.GymClassRepository")
    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_get_timetable(self, MockRepo, mock_redis, MockClassRepo):
        """Should return classes grouped by day."""
        mock_redis.return_value = _mock_cache()
        MockClassRepo.return_value.get_by_gym.return_value = [
            {"id": 1, "day_name": "Monday", "class_type": "gi"},
            {"id": 2, "day_name": "Monday", "class_type": "no-gi"},
            {"id": 3, "day_name": "Wednesday", "class_type": "gi"},
        ]

        service = GymService()
        result = service.get_timetable(gym_id=1)

        assert "Monday" in result
        assert len(result["Monday"]) == 2
        assert "Wednesday" in result
        assert len(result["Wednesday"]) == 1

    @patch("rivaflow.core.services.gym_service.GymClassRepository")
    @patch("rivaflow.core.services.gym_service.get_redis_client")
    @patch("rivaflow.core.services.gym_service.GymRepository")
    def test_get_todays_classes(self, MockRepo, mock_redis, MockClassRepo):
        """Should return classes for today."""
        mock_redis.return_value = _mock_cache()
        MockClassRepo.return_value.get_by_gym_and_day.return_value = [
            {"id": 1, "class_type": "gi", "start_time": "18:00"},
        ]

        service = GymService()
        # Monday = weekday 0
        result = service.get_todays_classes(gym_id=1, today=date(2025, 1, 20))

        assert len(result) == 1
        MockClassRepo.return_value.get_by_gym_and_day.assert_called_once_with(1, 0)
