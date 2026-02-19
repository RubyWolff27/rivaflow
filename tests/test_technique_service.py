"""Unit tests for TechniqueService — technique tracking with caching."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from rivaflow.core.services.technique_service import TechniqueService


def _mock_cache():
    """Create a mock cache that behaves like a dict."""
    cache = MagicMock()
    cache.get.return_value = None  # cache miss by default
    return cache


class TestAddTechnique:
    """Tests for TechniqueService.add_technique."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_creates_technique_and_returns_id(self, MockRepo, mock_redis):
        """Should create technique and return its ID."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.create.return_value = 7

        service = TechniqueService()
        result = service.add_technique(user_id=1, name="armbar", category="submission")

        assert result == 7
        MockRepo.return_value.create.assert_called_once_with(
            name="armbar", category="submission"
        )

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_invalidates_cache_on_create(self, MockRepo, mock_redis):
        """Should invalidate technique cache after creation."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.create.return_value = 1

        service = TechniqueService()
        service.add_technique(user_id=1, name="triangle")

        mock_cache.delete_pattern.assert_called_once_with("techniques:*")

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_category_defaults_to_none(self, MockRepo, mock_redis):
        """Should pass None for category when not provided."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.create.return_value = 2

        service = TechniqueService()
        service.add_technique(user_id=1, name="sweep")

        MockRepo.return_value.create.assert_called_once_with(
            name="sweep", category=None
        )


class TestGetTechnique:
    """Tests for TechniqueService.get_technique."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_returns_from_cache_on_hit(self, MockRepo, mock_redis):
        """Should return cached technique without DB call."""
        mock_cache = _mock_cache()
        cached_tech = {"id": 1, "name": "armbar"}
        mock_cache.get.return_value = cached_tech
        mock_redis.return_value = mock_cache

        service = TechniqueService()
        result = service.get_technique(user_id=1, technique_id=1)

        assert result == cached_tech
        MockRepo.return_value.get_by_id.assert_not_called()

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_fetches_from_db_on_cache_miss(self, MockRepo, mock_redis):
        """Should fetch from DB and cache the result on miss."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        technique = {"id": 1, "name": "armbar"}
        MockRepo.return_value.get_by_id.return_value = technique

        service = TechniqueService()
        result = service.get_technique(user_id=1, technique_id=1)

        assert result == technique
        mock_cache.set.assert_called_once()

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_returns_none_when_not_found(self, MockRepo, mock_redis):
        """Should return None and not cache when technique missing."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.get_by_id.return_value = None

        service = TechniqueService()
        result = service.get_technique(user_id=1, technique_id=999)

        assert result is None
        mock_cache.set.assert_not_called()


class TestGetTechniqueByName:
    """Tests for TechniqueService.get_technique_by_name."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_returns_technique_by_name(self, MockRepo, mock_redis):
        """Should fetch technique by name from DB on cache miss."""
        mock_redis.return_value = _mock_cache()
        technique = {"id": 5, "name": "kimura"}
        MockRepo.return_value.get_by_name.return_value = technique

        service = TechniqueService()
        result = service.get_technique_by_name(user_id=1, name="kimura")

        assert result["name"] == "kimura"

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_returns_cached_technique_by_name(self, MockRepo, mock_redis):
        """Should return cached technique by name on hit."""
        mock_cache = _mock_cache()
        mock_cache.get.return_value = {"id": 5, "name": "kimura"}
        mock_redis.return_value = mock_cache

        service = TechniqueService()
        result = service.get_technique_by_name(user_id=1, name="kimura")

        assert result["name"] == "kimura"
        MockRepo.return_value.get_by_name.assert_not_called()


class TestListAllTechniques:
    """Tests for TechniqueService.list_all_techniques."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_returns_all_techniques(self, MockRepo, mock_redis):
        """Should return list of all techniques."""
        mock_redis.return_value = _mock_cache()
        techniques = [
            {"id": 1, "name": "armbar"},
            {"id": 2, "name": "triangle"},
        ]
        MockRepo.return_value.list_all.return_value = techniques

        service = TechniqueService()
        result = service.list_all_techniques(user_id=1)

        assert len(result) == 2

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_caches_all_techniques(self, MockRepo, mock_redis):
        """Should cache the full technique list."""
        mock_cache = _mock_cache()
        mock_redis.return_value = mock_cache
        MockRepo.return_value.list_all.return_value = [{"id": 1, "name": "armbar"}]

        service = TechniqueService()
        service.list_all_techniques(user_id=1)

        mock_cache.set.assert_called_once()


class TestSearchAndStale:
    """Tests for search_techniques and get_stale_techniques."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_search_techniques(self, MockRepo, mock_redis):
        """Should search techniques by query string."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.search.return_value = [{"id": 1, "name": "armbar"}]

        service = TechniqueService()
        result = service.search_techniques(user_id=1, query="arm")

        assert len(result) == 1
        MockRepo.return_value.search.assert_called_once_with("arm")

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_get_stale_techniques(self, MockRepo, mock_redis):
        """Should return techniques not trained in N days."""
        mock_redis.return_value = _mock_cache()
        MockRepo.return_value.get_stale.return_value = [
            {"id": 1, "name": "triangle", "days_since": 14}
        ]

        service = TechniqueService()
        result = service.get_stale_techniques(user_id=1, days=7)

        assert len(result) == 1
        MockRepo.return_value.get_stale.assert_called_once_with(7)


class TestFormatAndCalculate:
    """Tests for format_technique_summary and calculate_days_since_trained."""

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_format_with_category_and_date(self, MockRepo, mock_redis):
        """Should format technique with category and last trained info."""
        mock_redis.return_value = _mock_cache()
        tech = {
            "name": "armbar",
            "category": "submission",
            "last_trained_date": date.today() - timedelta(days=3),
        }

        service = TechniqueService()
        result = service.format_technique_summary(tech)

        assert "armbar" in result
        assert "submission" in result
        assert "Days since: 3" in result

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_format_never_trained(self, MockRepo, mock_redis):
        """Should show 'Never' when technique has no last_trained_date."""
        mock_redis.return_value = _mock_cache()
        tech = {"name": "sweep", "category": None, "last_trained_date": None}

        service = TechniqueService()
        result = service.format_technique_summary(tech)

        assert "Never" in result

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_calculate_days_since_trained(self, MockRepo, mock_redis):
        """Should calculate correct days since last training."""
        mock_redis.return_value = _mock_cache()
        tech = {"last_trained_date": date.today() - timedelta(days=5)}

        service = TechniqueService()
        result = service.calculate_days_since_trained(tech)

        assert result == 5

    @patch("rivaflow.core.services.technique_service.get_redis_client")
    @patch("rivaflow.core.services.technique_service.TechniqueRepository")
    def test_calculate_days_returns_none_when_never_trained(self, MockRepo, mock_redis):
        """Should return None when technique was never trained."""
        mock_redis.return_value = _mock_cache()
        tech = {"last_trained_date": None}

        service = TechniqueService()
        result = service.calculate_days_since_trained(tech)

        assert result is None
