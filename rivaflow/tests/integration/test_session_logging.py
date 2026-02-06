"""
Integration tests for session logging workflow.

Tests the complete session logging flow from creation through
retrieval, updates, and analytics integration.
"""

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

# Set SECRET_KEY for testing
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-session-integration-tests-32chars"
)

from rivaflow.api.main import app
from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.session_service import SessionService
from rivaflow.core.services.streak_service import StreakService
from rivaflow.db.database import get_connection, init_db


@pytest.fixture(scope="module")
def test_client():
    """Create test client for API testing."""
    init_db()
    return TestClient(app)


@pytest.fixture(scope="function")
def authenticated_user(test_client):
    """Create and authenticate a test user."""
    from datetime import datetime

    email = f"test_session_{datetime.now().timestamp()}@example.com"
    password = "SecurePassword123!"

    # Register user
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 201

    tokens = response.json()
    user_id = tokens["user"]["id"]

    yield {
        "user_id": user_id,
        "email": email,
        "access_token": tokens["access_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
    }

    # Cleanup
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM daily_checkins WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


class TestSessionCreation:
    """Test session creation flow."""

    def test_create_basic_session(self, test_client, authenticated_user):
        """Test creating a basic training session."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["class_type"] == "gi"
        assert data["gym_name"] == "Test Gym"
        assert data["duration_mins"] == 90
        assert "session_id" in data

    def test_create_detailed_session(self, test_client, authenticated_user):
        """Test creating a session with all fields."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "no-gi",
                "gym_name": "Advanced Gym",
                "location": "Sydney, NSW",
                "duration_mins": 120,
                "intensity": 5,
                "rolls": 8,
                "submissions_for": 3,
                "submissions_against": 2,
                "partners": ["Partner A", "Partner B", "Partner C"],
                "techniques": ["armbar", "triangle", "kimura"],
                "notes": "Great session, worked on guard passing",
                "visibility_level": "full",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["submissions_for"] == 3
        assert data["submissions_against"] == 2
        assert len(data["partners"]) == 3
        assert len(data["techniques"]) == 3
        assert data["notes"] == "Great session, worked on guard passing"

    def test_create_session_future_date_rejected(self, test_client, authenticated_user):
        """Test sessions cannot be created in the future."""
        future_date = (date.today() + timedelta(days=1)).isoformat()

        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": future_date,
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )

        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()

    def test_create_session_invalid_class_type(self, test_client, authenticated_user):
        """Test invalid class type is rejected."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "invalid_type",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )

        assert response.status_code == 422  # Validation error


class TestSessionRetrieval:
    """Test session retrieval and listing."""

    @pytest.fixture
    def user_with_sessions(self, test_client, authenticated_user):
        """Create user with multiple sessions."""
        # Create 3 sessions over the past week
        for i in range(3):
            test_client.post(
                "/api/v1/sessions",
                headers=authenticated_user["headers"],
                json={
                    "session_date": (date.today() - timedelta(days=i)).isoformat(),
                    "class_type": "gi" if i % 2 == 0 else "no-gi",
                    "gym_name": f"Gym {i}",
                    "duration_mins": 90 + (i * 10),
                    "intensity": 3 + i,
                    "rolls": 5 + i,
                },
            )
        return authenticated_user

    def test_list_sessions(self, test_client, user_with_sessions):
        """Test listing all user sessions."""
        response = test_client.get(
            "/api/v1/sessions", headers=user_with_sessions["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        # Should be sorted by date descending
        dates = [s["session_date"] for s in data]
        assert dates == sorted(dates, reverse=True)

    def test_get_session_by_id(self, test_client, authenticated_user):
        """Test retrieving specific session by ID."""
        # Create a session
        create_response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )
        session_id = create_response.json()["id"]

        # Retrieve it
        response = test_client.get(
            f"/api/v1/sessions/{session_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["gym_name"] == "Test Gym"

    def test_get_session_wrong_user(self, test_client, authenticated_user):
        """Test users cannot access other users' sessions."""
        # Create a second user
        from datetime import datetime

        email2 = f"test_session2_{datetime.now().timestamp()}@example.com"

        response2 = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": email2,
                "password": "SecurePassword123!",
                "first_name": "Other",
                "last_name": "User",
            },
        )
        user2_token = response2.json()["access_token"]
        user2_id = response2.json()["user"]["id"]

        # User 1 creates a session
        create_response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )
        session_id = create_response.json()["id"]

        # User 2 tries to access it
        response = test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        assert response.status_code == 404  # Not found (or 403 Forbidden)

        # Cleanup user 2
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user2_id,))
            conn.commit()


class TestSessionUpdate:
    """Test session update functionality."""

    def test_update_session(self, test_client, authenticated_user):
        """Test updating an existing session."""
        # Create a session
        create_response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )
        session_id = create_response.json()["id"]

        # Update it
        response = test_client.put(
            f"/api/v1/sessions/{session_id}",
            headers=authenticated_user["headers"],
            json={
                "duration_mins": 120,
                "intensity": 5,
                "notes": "Updated notes",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["duration_mins"] == 120
        assert data["intensity"] == 5
        assert data["notes"] == "Updated notes"

    def test_update_nonexistent_session(self, test_client, authenticated_user):
        """Test updating non-existent session fails."""
        response = test_client.put(
            "/api/v1/sessions/99999",
            headers=authenticated_user["headers"],
            json={
                "duration_mins": 120,
            },
        )

        assert response.status_code == 404


class TestSessionDeletion:
    """Test session deletion."""

    def test_delete_session(self, test_client, authenticated_user):
        """Test deleting a session."""
        # Create a session
        create_response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )
        session_id = create_response.json()["id"]

        # Delete it
        response = test_client.delete(
            f"/api/v1/sessions/{session_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 200

        # Verify it's gone
        get_response = test_client.get(
            f"/api/v1/sessions/{session_id}", headers=authenticated_user["headers"]
        )
        assert get_response.status_code == 404


class TestSessionAnalyticsIntegration:
    """Test session logging integrates with analytics."""

    def test_session_counted_in_analytics(self, authenticated_user):
        """Test logged sessions appear in analytics."""
        user_id = authenticated_user["user_id"]
        service = SessionService()
        analytics = AnalyticsService()

        # Log a session
        service.create_session(
            user_id=user_id,
            session_date=date.today(),
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=4,
            rolls=5,
        )

        # Check analytics
        stats = analytics.get_weekly_summary(user_id)
        assert stats["sessions_this_week"] >= 1

    def test_session_updates_streak(self, authenticated_user):
        """Test logged sessions update training streaks."""
        user_id = authenticated_user["user_id"]
        service = SessionService()
        streak_service = StreakService()

        # Log sessions on consecutive days
        for i in range(3):
            service.create_session(
                user_id=user_id,
                session_date=date.today() - timedelta(days=i),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=90,
                intensity=4,
                rolls=5,
            )

        # Check streak
        streak = streak_service.get_streak(user_id, "session")
        assert streak["current_streak"] >= 3


class TestSessionValidation:
    """Test session data validation."""

    def test_negative_duration_rejected(self, test_client, authenticated_user):
        """Test negative duration is rejected."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": -10,
                "intensity": 4,
                "rolls": 5,
            },
        )

        assert response.status_code == 422

    def test_intensity_out_of_range_rejected(self, test_client, authenticated_user):
        """Test intensity outside 1-5 range is rejected."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 90,
                "intensity": 10,  # Invalid
                "rolls": 5,
            },
        )

        assert response.status_code == 422

    def test_empty_gym_name_rejected(self, test_client, authenticated_user):
        """Test empty gym name is rejected."""
        response = test_client.post(
            "/api/v1/sessions",
            headers=authenticated_user["headers"],
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "",  # Empty
                "duration_mins": 90,
                "intensity": 4,
                "rolls": 5,
            },
        )

        assert response.status_code == 400
