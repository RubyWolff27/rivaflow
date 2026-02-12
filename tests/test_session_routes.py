"""Integration tests for session management routes."""

from datetime import date, timedelta


class TestCreateSession:
    """Session creation tests."""

    def test_create_session(self, authenticated_client, test_user):
        """Test creating a new session."""
        response = authenticated_client.post(
            "/api/v1/sessions/",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "location": "Test City",
                "duration_mins": 60,
                "intensity": 4,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["class_type"] == "gi"
        assert data["gym_name"] == "Test Gym"

    def test_create_session_missing_fields(self, authenticated_client, test_user):
        """Test creating session with missing required fields fails."""
        response = authenticated_client.post(
            "/api/v1/sessions/",
            json={"session_date": date.today().isoformat()},
        )
        assert response.status_code == 422

    def test_create_session_requires_auth(self, client, temp_db):
        """Test that creating a session requires authentication."""
        response = client.post(
            "/api/v1/sessions/",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "duration_mins": 60,
                "intensity": 3,
            },
        )
        assert response.status_code == 401


class TestListSessions:
    """Session listing tests."""

    def test_list_sessions(self, authenticated_client, test_user, session_factory):
        """Test listing user sessions."""
        session_factory()
        response = authenticated_client.get("/api/v1/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_sessions_empty(self, authenticated_client, test_user):
        """Test listing when no sessions exist."""
        response = authenticated_client.get("/api/v1/sessions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGetSession:
    """Single session retrieval tests."""

    def test_get_session(self, authenticated_client, test_user, session_factory):
        """Test getting a single session by ID."""
        session_id = session_factory()
        response = authenticated_client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id

    def test_get_session_not_found(self, authenticated_client, test_user):
        """Test getting a nonexistent session returns 404."""
        response = authenticated_client.get("/api/v1/sessions/99999")
        assert response.status_code == 404

    def test_get_other_users_session(
        self, authenticated_client, test_user, test_user2, temp_db
    ):
        """Test that accessing another user's session is blocked."""
        from rivaflow.db.repositories.session_repo import SessionRepository

        other_id = SessionRepository.create(
            user_id=test_user2["id"],
            session_date=date.today(),
            class_type="gi",
            gym_name="Other Gym",
            duration_mins=60,
            intensity=3,
        )
        response = authenticated_client.get(f"/api/v1/sessions/{other_id}")
        assert response.status_code in (403, 404)


class TestUpdateSession:
    """Session update tests."""

    def test_update_session(self, authenticated_client, test_user, session_factory):
        """Test updating a session."""
        session_id = session_factory()
        response = authenticated_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"intensity": 5, "notes": "Updated notes"},
        )
        assert response.status_code == 200

        # Re-fetch to verify update (update() may return stale data)
        get_resp = authenticated_client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["notes"] == "Updated notes"


class TestDeleteSession:
    """Session deletion tests."""

    def test_delete_session(self, authenticated_client, test_user, session_factory):
        """Test deleting a session."""
        session_id = session_factory()
        response = authenticated_client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = authenticated_client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 404


class TestSessionRange:
    """Date range query tests."""

    def test_sessions_by_range(self, authenticated_client, test_user, session_factory):
        """Test getting sessions by date range."""
        today = date.today()
        session_factory(session_date=today)

        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
        response = authenticated_client.get(f"/api/v1/sessions/range/{start}/{end}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_sessions_range_empty(self, authenticated_client, test_user):
        """Test date range with no sessions."""
        start = "2020-01-01"
        end = "2020-01-07"
        response = authenticated_client.get(f"/api/v1/sessions/range/{start}/{end}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
