"""
Smoke tests for critical system integrity.

These tests verify that core services can be imported and instantiated.
Run before deploying to ensure no import errors or critical failures.
"""

import os

# Set SECRET_KEY for testing (required by auth module)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-smoke-tests-only")


def test_all_core_services_importable():
    """Verify all core services can be imported without errors."""
    # Session and training services

    # User management
    from rivaflow.core.services.auth_service import AuthService
    from rivaflow.core.services.feed_service import FeedService

    # Content and data
    from rivaflow.core.services.goals_service import GoalsService
    from rivaflow.core.services.milestone_service import MilestoneService
    from rivaflow.core.services.notification_service import NotificationService

    # Social features
    from rivaflow.core.services.privacy_service import PrivacyService
    from rivaflow.core.services.readiness_service import ReadinessService

    # Analytics and reporting
    from rivaflow.core.services.report_service import ReportService
    from rivaflow.core.services.session_service import SessionService
    from rivaflow.core.services.social_service import SocialService
    from rivaflow.core.services.streak_service import StreakService

    # Verify stateful services can be instantiated
    assert SessionService() is not None
    assert ReadinessService() is not None
    assert ReportService() is not None
    assert GoalsService() is not None
    assert StreakService() is not None
    assert MilestoneService() is not None
    assert FeedService() is not None

    # Verify static services exist
    assert PrivacyService is not None
    assert SocialService is not None
    assert NotificationService is not None
    assert AuthService is not None


def test_database_connection_available():
    """Verify database connection can be established."""
    from rivaflow.db.database import get_connection

    with get_connection() as conn:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_repositories_importable():
    """Verify all repositories can be imported."""
    from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository
    from rivaflow.db.repositories.activity_like_repo import ActivityLikeRepository
    from rivaflow.db.repositories.friend_repo import FriendRepository
    from rivaflow.db.repositories.glossary_repo import GlossaryRepository
    from rivaflow.db.repositories.notification_repo import NotificationRepository
    from rivaflow.db.repositories.readiness_repo import ReadinessRepository
    from rivaflow.db.repositories.session_repo import SessionRepository

    # All repositories use static methods, just verify they exist
    assert SessionRepository is not None
    assert ReadinessRepository is not None
    assert NotificationRepository is not None
    assert FriendRepository is not None
    assert GlossaryRepository is not None
    assert ActivityLikeRepository is not None
    assert ActivityCommentRepository is not None


def test_api_routes_importable():
    """Verify all API route modules can be imported."""
    from rivaflow.api.routes import (
        admin,
        auth,
        glossary,
        notifications,
        profile,
        readiness,
        sessions,
        social,
    )

    # Verify routers exist
    assert hasattr(sessions, "router")
    assert hasattr(readiness, "router")
    assert hasattr(auth, "router")
    assert hasattr(profile, "router")
    assert hasattr(social, "router")
    assert hasattr(notifications, "router")
    assert hasattr(glossary, "router")
    assert hasattr(admin, "router")


def test_privacy_service_redaction():
    """Verify privacy redaction works for different visibility levels."""
    from rivaflow.core.services.privacy_service import PrivacyService

    session = {
        "id": 1,
        "session_date": "2026-02-01",
        "class_type": "gi",
        "gym_name": "Test Gym",
        "location": "Sydney, NSW",
        "duration_mins": 90,
        "intensity": 4,
        "rolls": 5,
        "submissions_for": 2,
        "submissions_against": 1,
        "partners": ["Partner A", "Partner B"],
        "techniques": ["armbar", "triangle"],
        "notes": "Great session, worked on passing",
        "visibility_level": "private",
    }

    # Test private redaction
    private = PrivacyService.redact_session(session, "private")
    assert private is None  # Private returns None

    # Test attendance redaction
    attendance = PrivacyService.redact_session(session, "attendance")
    assert attendance is not None
    assert attendance["gym_name"] == "Test Gym"
    assert "notes" not in attendance  # Sensitive field removed

    # Test summary redaction
    summary = PrivacyService.redact_session(session, "summary")
    assert summary is not None
    assert summary["intensity"] == 4
    assert "notes" not in summary  # Sensitive field removed

    # Test full visibility
    full = PrivacyService.redact_session(session, "full")
    assert full is not None
    assert full["notes"] == "Great session, worked on passing"
