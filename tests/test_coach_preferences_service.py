"""Unit tests for CoachPreferencesService — Grapple AI personalization."""

from unittest.mock import patch

from rivaflow.core.services.coach_preferences_service import (
    CoachPreferencesService,
)


class TestGet:
    """Tests for CoachPreferencesService.get."""

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_returns_preferences_when_found(self, MockRepo):
        """Should return preferences dict for user."""
        expected = {
            "user_id": 1,
            "coaching_style": "encouraging",
            "focus_areas": ["guard", "submissions"],
            "experience_level": "intermediate",
        }
        MockRepo.get.return_value = expected

        service = CoachPreferencesService()
        result = service.get(user_id=1)

        assert result == expected
        MockRepo.get.assert_called_once_with(1)

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_returns_none_when_no_preferences(self, MockRepo):
        """Should return None when user has no preferences."""
        MockRepo.get.return_value = None

        service = CoachPreferencesService()
        result = service.get(user_id=999)

        assert result is None

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_delegates_to_static_repo_method(self, MockRepo):
        """Should call the static get method on CoachPreferencesRepository."""
        MockRepo.get.return_value = {"user_id": 5}

        service = CoachPreferencesService()
        service.get(user_id=5)

        MockRepo.get.assert_called_once_with(5)


class TestUpsert:
    """Tests for CoachPreferencesService.upsert."""

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_upserts_and_returns_preferences(self, MockRepo):
        """Should upsert preferences and return updated dict."""
        updated = {
            "user_id": 1,
            "coaching_style": "technical",
            "focus_areas": ["guard"],
        }
        MockRepo.upsert.return_value = updated

        service = CoachPreferencesService()
        result = service.upsert(
            user_id=1,
            coaching_style="technical",
            focus_areas=["guard"],
        )

        assert result == updated
        MockRepo.upsert.assert_called_once_with(
            1, coaching_style="technical", focus_areas=["guard"]
        )

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_upsert_creates_new_when_none_exists(self, MockRepo):
        """Should create new preferences when user has none."""
        new_prefs = {
            "user_id": 2,
            "coaching_style": "motivational",
        }
        MockRepo.upsert.return_value = new_prefs

        service = CoachPreferencesService()
        result = service.upsert(user_id=2, coaching_style="motivational")

        assert result["user_id"] == 2
        assert result["coaching_style"] == "motivational"

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_upsert_returns_none_on_failure(self, MockRepo):
        """Should return None when upsert fails."""
        MockRepo.upsert.return_value = None

        service = CoachPreferencesService()
        result = service.upsert(user_id=1, coaching_style="strict")

        assert result is None

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_upsert_passes_arbitrary_fields(self, MockRepo):
        """Should forward all keyword arguments to the repository."""
        MockRepo.upsert.return_value = {"user_id": 1}

        service = CoachPreferencesService()
        service.upsert(
            user_id=1,
            coaching_style="encouraging",
            experience_level="advanced",
            goals="competition",
            preferred_language="en",
        )

        call_kwargs = MockRepo.upsert.call_args[1]
        assert call_kwargs["coaching_style"] == "encouraging"
        assert call_kwargs["experience_level"] == "advanced"
        assert call_kwargs["goals"] == "competition"
        assert call_kwargs["preferred_language"] == "en"

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_upsert_with_single_field_update(self, MockRepo):
        """Should allow updating a single field."""
        MockRepo.upsert.return_value = {
            "user_id": 3,
            "experience_level": "beginner",
        }

        service = CoachPreferencesService()
        result = service.upsert(user_id=3, experience_level="beginner")

        assert result["experience_level"] == "beginner"
        MockRepo.upsert.assert_called_once_with(3, experience_level="beginner")

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_get_then_upsert_workflow(self, MockRepo):
        """Should support get-then-upsert pattern."""
        MockRepo.get.return_value = None
        MockRepo.upsert.return_value = {
            "user_id": 10,
            "coaching_style": "balanced",
        }

        service = CoachPreferencesService()

        # First call: no existing preferences
        existing = service.get(user_id=10)
        assert existing is None

        # Second call: create preferences
        result = service.upsert(user_id=10, coaching_style="balanced")
        assert result["coaching_style"] == "balanced"

    @patch(
        "rivaflow.core.services.coach_preferences_service.CoachPreferencesRepository"
    )
    def test_get_returns_all_fields(self, MockRepo):
        """Should return complete preferences with all fields."""
        full_prefs = {
            "user_id": 1,
            "coaching_style": "technical",
            "focus_areas": ["guard", "takedowns"],
            "experience_level": "advanced",
            "goals": "competition prep",
            "preferred_language": "en",
            "created_at": "2025-01-01",
            "updated_at": "2025-01-20",
        }
        MockRepo.get.return_value = full_prefs

        service = CoachPreferencesService()
        result = service.get(user_id=1)

        assert result["coaching_style"] == "technical"
        assert len(result["focus_areas"]) == 2
        assert result["experience_level"] == "advanced"
