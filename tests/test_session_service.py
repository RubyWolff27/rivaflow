"""Tests for SessionService."""
from datetime import date
from unittest.mock import patch

from rivaflow.core.services.session_service import SessionService


def test_create_session(temp_db, test_user):
    """Test creating a session."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        session_id = service.create_session(
            user_id=test_user["id"],
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=60,
            intensity=4,
            rolls=5,
            submissions_for=2,
            submissions_against=1,
        )

        assert session_id > 0

        # Verify session was created
        session = service.get_session(user_id=test_user["id"], session_id=session_id)
        assert session is not None
        assert session["gym_name"] == "Test Gym"
        assert session["rolls"] == 5


def test_create_session_with_techniques(temp_db, test_user):
    """Test creating a session with techniques updates technique tracking."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        session_id = service.create_session(
            user_id=test_user["id"],
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
            techniques=["armbar", "triangle"],
        )

        # Verify techniques were created and updated
        from rivaflow.db.repositories import TechniqueRepository

        tech_repo = TechniqueRepository()
        armbar = tech_repo.get_by_name(name="armbar")
        assert armbar is not None
        assert armbar["last_trained_date"] == date(2025, 1, 20)


def test_get_autocomplete_data(temp_db, test_user):
    """Test getting autocomplete data."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        # Create some sessions
        service.create_session(
            user_id=test_user["id"],
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Gym A",
            location="City A",
            partners=["Partner1", "Partner2"],
            techniques=["armbar"],
        )

        autocomplete = service.get_autocomplete_data(user_id=test_user["id"])

        assert "Gym A" in autocomplete["gyms"]
        assert "City A" in autocomplete["locations"]
        assert "Partner1" in autocomplete["partners"]
        assert "armbar" in autocomplete["techniques"]


def test_is_sparring_class(temp_db):
    """Test sparring class detection."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        assert service.is_sparring_class("gi") is True
        assert service.is_sparring_class("no-gi") is True
        assert service.is_sparring_class("mobility") is False
        assert service.is_sparring_class("yoga") is False


def test_consecutive_class_type_count(temp_db, test_user):
    """Test counting consecutive class types."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        # Create consecutive Gi sessions
        for i in range(3):
            service.create_session(
                user_id=test_user["id"],
                session_date=date(2025, 1, 20 + i),
                class_type="gi",
                gym_name="Test Gym",
            )

        counts = service.get_consecutive_class_type_count(user_id=test_user["id"])
        assert counts["gi"] == 3
        assert counts["no-gi"] == 0


def test_format_session_summary(temp_db, test_user):
    """Test session summary formatting."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = SessionService()

        session_id = service.create_session(
            user_id=test_user["id"],
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
            rolls=5,
            submissions_for=2,
            submissions_against=1,
        )

        session = service.get_session(user_id=test_user["id"], session_id=session_id)
        summary = service.format_session_summary(session)

        assert "Test Gym" in summary
        assert "gi" in summary
        assert "Rolls: 5" in summary
