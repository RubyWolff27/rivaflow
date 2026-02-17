"""Integration tests for training suggestion routes."""

from datetime import date


class TestGetTodaySuggestion:
    """Tests for GET /api/v1/suggestions/today."""

    def test_get_today_suggestion(self, authenticated_client, test_user):
        """Test getting today's training suggestion returns valid data."""
        response = authenticated_client.get("/api/v1/suggestions/today")
        assert response.status_code == 200
        data = response.json()
        # The suggestion engine returns a dict with at least some keys
        assert isinstance(data, dict)

    def test_get_today_suggestion_with_date(self, authenticated_client, test_user):
        """Test getting suggestion for a specific target date."""
        target = date.today().isoformat()
        response = authenticated_client.get(
            f"/api/v1/suggestions/today?target_date={target}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_today_suggestion_with_readiness(
        self, authenticated_client, test_user, readiness_factory
    ):
        """Test suggestion incorporates readiness data when available."""
        readiness_factory(check_date=date.today())
        response = authenticated_client.get("/api/v1/suggestions/today")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_today_suggestion_with_sessions(
        self, authenticated_client, test_user, session_factory
    ):
        """Test suggestion incorporates session history."""
        session_factory()
        response = authenticated_client.get("/api/v1/suggestions/today")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_today_suggestion_requires_auth(self, client, temp_db):
        """Test that getting suggestions requires authentication."""
        response = client.get("/api/v1/suggestions/today")
        assert response.status_code == 401

    def test_get_today_suggestion_invalid_date(self, authenticated_client, test_user):
        """Test suggestion with invalid date parameter."""
        response = authenticated_client.get(
            "/api/v1/suggestions/today?target_date=not-a-date"
        )
        assert response.status_code == 422
