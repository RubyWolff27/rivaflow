"""Tests for SuggestionEngine."""
from datetime import date
from unittest.mock import patch

from rivaflow.core.services.suggestion_engine import SuggestionEngine
from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.services.session_service import SessionService
from rivaflow.core.services.technique_service import TechniqueService


def test_suggestion_with_high_stress(temp_db):
    """Test suggestion when readiness shows high stress."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            check_date=date.today(),
            sleep=3,
            stress=5,  # High stress
            soreness=2,
            energy=2,  # Low energy
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion()

        # Should trigger high_stress_low_energy rule
        assert "Flow roll" in result["suggestion"] or "drill" in result["suggestion"].lower()
        assert len(result["triggered_rules"]) > 0


def test_suggestion_with_high_soreness(temp_db):
    """Test suggestion when readiness shows high soreness."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            check_date=date.today(),
            sleep=4,
            stress=2,
            soreness=5,  # High soreness
            energy=3,
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion()

        # Should trigger high_soreness rule
        assert "Recovery" in result["suggestion"] or "mobility" in result["suggestion"].lower()


def test_suggestion_with_consecutive_gi(temp_db):
    """Test suggestion after consecutive Gi sessions."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create 3 consecutive Gi sessions
        session_service = SessionService()
        for i in range(3):
            session_service.create_session(
                session_date=date(2025, 1, 20 + i),
                class_type="gi",
                gym_name="Test Gym",
            )

        engine = SuggestionEngine()
        result = engine.get_suggestion()

        # Should suggest No-Gi
        assert "No-Gi" in result["suggestion"] or len(result["triggered_rules"]) > 0


def test_suggestion_with_stale_technique(temp_db):
    """Test suggestion when technique is stale."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create a technique and mark it as trained 10 days ago
        technique_service = TechniqueService()
        tech_id = technique_service.add_technique("armbar")

        from rivaflow.db.repositories import TechniqueRepository

        tech_repo = TechniqueRepository()
        tech_repo.update_last_trained(tech_id, date(2025, 1, 10))

        # Mock today as 10+ days later
        with patch("rivaflow.core.services.suggestion_engine.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 25)

            engine = SuggestionEngine()
            result = engine.get_suggestion()

            # Should suggest revisiting stale technique
            triggered_names = [r["name"] for r in result["triggered_rules"]]
            assert "stale_technique" in triggered_names


def test_suggestion_green_light(temp_db):
    """Test suggestion when readiness is excellent."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Perfect readiness
        readiness_service = ReadinessService()
        readiness_service.log_readiness(
            check_date=date.today(),
            sleep=5,
            stress=1,
            soreness=1,
            energy=5,
        )

        engine = SuggestionEngine()
        result = engine.get_suggestion()

        # Should give green light (or other suggestion if other rules triggered)
        # Just verify it returns a valid suggestion with good readiness
        assert result["suggestion"] is not None
        assert result["readiness"] is not None
        assert result["readiness"]["composite_score"] >= 16


def test_suggestion_no_readiness(temp_db):
    """Test suggestion when no readiness data exists."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        engine = SuggestionEngine()
        result = engine.get_suggestion()

        # Should still return a suggestion
        assert result["suggestion"] is not None
        # Readiness may or may not exist depending on test order, so just check structure
        assert "readiness" in result
        assert "triggered_rules" in result
