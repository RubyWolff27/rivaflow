"""Integration tests for rest day endpoints."""

from datetime import date


class TestLogRestDay:
    """Tests for POST /api/v1/rest/."""

    def test_log_requires_auth(self, client, temp_db):
        """Unauthenticated log returns 401."""
        response = client.post(
            "/api/v1/rest/",
            json={"rest_type": "full"},
        )
        assert response.status_code == 401

    def test_log_rest_day(self, authenticated_client, test_user):
        """Log a rest day with type and note."""
        response = authenticated_client.post(
            "/api/v1/rest/",
            json={
                "rest_type": "active",
                "rest_note": "Light stretching only",
                "check_date": date.today().isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "checkin_id" in data
        assert data["checkin_type"] == "rest"
        assert data["rest_type"] == "active"

    def test_log_rest_day_minimal(self, authenticated_client, test_user):
        """Log a rest day with no optional fields."""
        response = authenticated_client.post(
            "/api/v1/rest/",
            json={},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["checkin_type"] == "rest"

    def test_log_rest_day_with_intention(self, authenticated_client, test_user):
        """Log a rest day with tomorrow intention."""
        response = authenticated_client.post(
            "/api/v1/rest/",
            json={
                "rest_type": "full",
                "tomorrow_intention": "Morning gi class",
                "check_date": "2026-01-15",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["check_date"] == "2026-01-15"


class TestGetRecentRestDays:
    """Tests for GET /api/v1/rest/recent."""

    def test_recent_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/rest/recent")
        assert response.status_code == 401

    def test_recent_returns_200(self, authenticated_client, test_user):
        """Authenticated request returns 200 with list."""
        response = authenticated_client.get("/api/v1/rest/recent")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_recent_includes_logged_rest(self, authenticated_client, test_user):
        """Logged rest days appear in recent list."""
        today = date.today().isoformat()
        authenticated_client.post(
            "/api/v1/rest/",
            json={
                "rest_type": "injury",
                "rest_note": "Tweaked knee",
                "check_date": today,
            },
        )
        response = authenticated_client.get("/api/v1/rest/recent")
        data = response.json()
        assert len(data) >= 1

    def test_recent_with_days_param(self, authenticated_client, test_user):
        """Custom days parameter is accepted."""
        response = authenticated_client.get("/api/v1/rest/recent?days=7")
        assert response.status_code == 200


class TestGetRestByDate:
    """Tests for GET /api/v1/rest/by-date/{rest_date}."""

    def test_by_date_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/rest/by-date/2026-01-15")
        assert response.status_code == 401

    def test_by_date_not_found(self, authenticated_client, test_user):
        """Get rest day for date with no entry returns 404."""
        response = authenticated_client.get("/api/v1/rest/by-date/2020-01-01")
        assert response.status_code == 404

    def test_by_date_invalid_format(self, authenticated_client, test_user):
        """Invalid date format returns 400."""
        response = authenticated_client.get("/api/v1/rest/by-date/not-a-date")
        assert response.status_code == 400


class TestDeleteRestDay:
    """Tests for DELETE /api/v1/rest/{checkin_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        response = client.delete("/api/v1/rest/1")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Delete non-existent rest day returns 404."""
        response = authenticated_client.delete("/api/v1/rest/999999")
        assert response.status_code == 404

    def test_delete_rest_day(self, authenticated_client, test_user):
        """Delete a rest day that was just logged."""
        create_resp = authenticated_client.post(
            "/api/v1/rest/",
            json={
                "rest_type": "sick",
                "check_date": "2026-02-10",
            },
        )
        assert create_resp.status_code == 201
        checkin_id = create_resp.json()["checkin_id"]

        response = authenticated_client.delete(f"/api/v1/rest/{checkin_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_id"] == checkin_id
