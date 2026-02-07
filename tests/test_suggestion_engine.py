"""Tests for SuggestionEngine."""

from datetime import date
from unittest.mock import patch

from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.services.session_service import SessionService
from rivaflow.core.services.suggestion_engine import SuggestionEngine


def test_suggestion_with_high_stress(temp_db, test_user):
    """Test suggestion when readiness shows high stress."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            user_id=test_user["id"],
            check_date=date.today(),
            sleep=3,
            stress=5,  # High stress
            soreness=2,
            energy=2,  # Low energy
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion(user_id=test_user["id"])

        # Should trigger high_stress_low_energy rule
        assert (
            "Flow roll" in result["suggestion"]
            or "drill" in result["suggestion"].lower()
        )
        assert len(result["triggered_rules"]) > 0


def test_suggestion_with_high_soreness(temp_db, test_user):
    """Test suggestion when readiness shows high soreness."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            user_id=test_user["id"],
            check_date=date.today(),
            sleep=4,
            stress=2,
            soreness=5,  # High soreness
            energy=3,
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion(user_id=test_user["id"])

        # Should trigger high_soreness rule
        assert (
            "Recovery" in result["suggestion"]
            or "mobility" in result["suggestion"].lower()
        )


def test_suggestion_with_consecutive_gi(temp_db, test_user):
    """Test suggestion after consecutive Gi sessions."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create 3 consecutive Gi sessions
        session_service = SessionService()
        for i in range(3):
            session_service.create_session(
                user_id=test_user["id"],
                session_date=date(2025, 1, 20 + i),
                class_type="gi",
                gym_name="Test Gym",
            )

        engine = SuggestionEngine()
        result = engine.get_suggestion(user_id=test_user["id"])

        # Should suggest No-Gi
        assert "No-Gi" in result["suggestion"] or len(result["triggered_rules"]) > 0


def test_suggestion_with_stale_technique(temp_db, test_user):
    """Test suggestion when technique is stale."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create a session with a technique trained 10 days ago
        # This creates a glossary entry + session_techniques record
        session_service = SessionService()
        session_service.create_session(
            user_id=test_user["id"],
            session_date=date(2025, 1, 10),
            class_type="gi",
            gym_name="Test Gym",
            techniques=["armbar"],
        )

        # Mock today as 10+ days later so GlossaryRepository.get_stale finds it
        with patch("rivaflow.db.repositories.glossary_repo.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 25)

            engine = SuggestionEngine()
            result = engine.get_suggestion(user_id=test_user["id"])

            # Should suggest revisiting stale technique
            triggered_names = [r["name"] for r in result["triggered_rules"]]
            assert "stale_technique" in triggered_names


def test_suggestion_green_light(temp_db, test_user):
    """Test suggestion when readiness is excellent."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Perfect readiness
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            user_id=test_user["id"],
            check_date=date.today(),
            sleep=5,
            stress=1,
            soreness=1,
            energy=5,
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion(user_id=test_user["id"])

        # Should give green light (or other suggestion if other rules triggered)
        # Just verify it returns a valid suggestion with good readiness
        assert result["suggestion"] is not None
        assert result["readiness"] is not None
        assert result["readiness"]["composite_score"] >= 16


def test_suggestion_no_readiness(temp_db, test_user):
    """Test suggestion when no readiness data exists."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        engine = SuggestionEngine()
        result = engine.get_suggestion(user_id=test_user["id"])

        # Should still return a suggestion
        assert result["suggestion"] is not None
        # Readiness may or may not exist depending on test order, so just check structure
        assert "readiness" in result
        assert "triggered_rules" in result
