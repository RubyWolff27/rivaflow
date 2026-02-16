"""Integration tests for streak endpoints."""


class TestStreakStatus:
    """Streak status endpoint tests."""

    def test_status_requires_auth(self, client, temp_db):
        """Test GET /api/v1/streaks/status requires auth."""
        response = client.get("/api/v1/streaks/status")
        assert response.status_code == 401

    def test_status_returns_200(self, authenticated_client, test_user):
        """Test streak status returns 200 with auth."""
        response = authenticated_client.get("/api/v1/streaks/status")
        assert response.status_code == 200

    def test_status_includes_streak_types(self, authenticated_client, test_user):
        """Test streak status includes all streak types."""
        response = authenticated_client.get("/api/v1/streaks/status")
        data = response.json()
        assert "checkin" in data
        assert "training" in data
        assert "readiness" in data

    def test_status_includes_any_at_risk(self, authenticated_client, test_user):
        """Test streak status includes any_at_risk flag."""
        response = authenticated_client.get("/api/v1/streaks/status")
        data = response.json()
        assert "any_at_risk" in data
        assert isinstance(data["any_at_risk"], bool)


class TestGetStreak:
    """Get specific streak endpoint tests."""

    def test_get_checkin_streak(self, authenticated_client, test_user):
        """Test getting checkin streak."""
        response = authenticated_client.get("/api/v1/streaks/checkin")
        assert response.status_code == 200

    def test_get_training_streak(self, authenticated_client, test_user):
        """Test getting training streak."""
        response = authenticated_client.get("/api/v1/streaks/training")
        assert response.status_code == 200

    def test_get_readiness_streak(self, authenticated_client, test_user):
        """Test getting readiness streak."""
        response = authenticated_client.get("/api/v1/streaks/readiness")
        assert response.status_code == 200

    def test_get_streak_requires_auth(self, client, temp_db):
        """Test getting a streak requires auth."""
        response = client.get("/api/v1/streaks/checkin")
        assert response.status_code == 401
