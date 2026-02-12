"""Integration tests for readiness routes."""

from datetime import date, timedelta


class TestLogReadiness:
    """Readiness creation tests."""

    def test_log_readiness(self, authenticated_client, test_user):
        """Test logging readiness."""
        response = authenticated_client.post(
            "/api/v1/readiness/",
            json={
                "check_date": date.today().isoformat(),
                "sleep": 4,
                "stress": 3,
                "soreness": 2,
                "energy": 4,
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["sleep"] == 4
        assert data["energy"] == 4

    def test_log_readiness_with_weight(self, authenticated_client, test_user):
        """Test logging readiness with weight."""
        response = authenticated_client.post(
            "/api/v1/readiness/",
            json={
                "check_date": date.today().isoformat(),
                "sleep": 3,
                "stress": 3,
                "soreness": 3,
                "energy": 3,
                "weight_kg": 80.5,
            },
        )
        assert response.status_code in (200, 201)

    def test_log_readiness_requires_auth(self, client, temp_db):
        """Test that logging readiness requires auth."""
        response = client.post(
            "/api/v1/readiness/",
            json={
                "check_date": date.today().isoformat(),
                "sleep": 3,
                "stress": 3,
                "soreness": 3,
                "energy": 3,
            },
        )
        assert response.status_code == 401


class TestGetReadiness:
    """Readiness retrieval tests."""

    def test_get_latest(self, authenticated_client, test_user, readiness_factory):
        """Test getting latest readiness."""
        readiness_factory()
        response = authenticated_client.get("/api/v1/readiness/latest")
        assert response.status_code == 200
        data = response.json()
        assert "sleep" in data
        assert "energy" in data

    def test_get_latest_no_data(self, authenticated_client, test_user):
        """Test getting latest when no readiness exists."""
        response = authenticated_client.get("/api/v1/readiness/latest")
        assert response.status_code == 200

    def test_get_by_date(self, authenticated_client, test_user, readiness_factory):
        """Test getting readiness by date."""
        today = date.today()
        readiness_factory(check_date=today)
        response = authenticated_client.get(f"/api/v1/readiness/{today.isoformat()}")
        assert response.status_code == 200
        data = response.json()
        assert data["check_date"] == today.isoformat()

    def test_get_by_date_not_found(self, authenticated_client, test_user):
        """Test getting readiness for date with no data."""
        response = authenticated_client.get("/api/v1/readiness/2020-01-01")
        assert response.status_code in (200, 404)

    def test_get_range(self, authenticated_client, test_user, readiness_factory):
        """Test getting readiness by date range."""
        today = date.today()
        readiness_factory(check_date=today)

        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
        response = authenticated_client.get(f"/api/v1/readiness/range/{start}/{end}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestLogWeight:
    """Weight-only logging tests."""

    def test_log_weight(self, authenticated_client, test_user):
        """Test logging weight only."""
        response = authenticated_client.post(
            "/api/v1/readiness/weight",
            json={
                "weight_kg": 82.0,
            },
        )
        assert response.status_code in (200, 201)
