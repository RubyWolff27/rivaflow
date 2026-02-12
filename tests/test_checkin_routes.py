"""Integration tests for daily check-in routes."""


class TestTodayCheckin:
    """Today's check-in tests."""

    def test_get_today(self, authenticated_client, test_user):
        """Test getting today's check-in status."""
        response = authenticated_client.get("/api/v1/checkins/today")
        assert response.status_code == 200
        data = response.json()
        assert "checked_in" in data or "date" in data or "morning" in data

    def test_get_today_requires_auth(self, client, temp_db):
        """Test that today's check-in requires auth."""
        response = client.get("/api/v1/checkins/today")
        assert response.status_code == 401


class TestWeekCheckins:
    """Week check-in summary tests."""

    def test_get_week(self, authenticated_client, test_user):
        """Test getting week check-in summary."""
        response = authenticated_client.get("/api/v1/checkins/week")
        assert response.status_code == 200
        data = response.json()
        assert "week_start" in data
        assert "checkins" in data


class TestTomorrowIntention:
    """Tomorrow intention update tests."""

    def test_update_tomorrow(self, authenticated_client, test_user):
        """Test setting tomorrow's intention (requires existing checkin)."""
        # Create a midday checkin first to satisfy the prerequisite
        authenticated_client.post(
            "/api/v1/checkins/midday",
            json={"energy_level": 3},
        )
        response = authenticated_client.put(
            "/api/v1/checkins/today/tomorrow",
            json={"tomorrow_intention": "Train hard"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_tomorrow_no_checkin(self, authenticated_client, test_user):
        """Test setting tomorrow intention when no checkin exists."""
        response = authenticated_client.put(
            "/api/v1/checkins/today/tomorrow",
            json={"tomorrow_intention": "Train hard"},
        )
        assert response.status_code in (404, 400)


class TestMiddayCheckin:
    """Midday check-in tests."""

    def test_create_midday(self, authenticated_client, test_user):
        """Test creating a midday check-in."""
        response = authenticated_client.post(
            "/api/v1/checkins/midday",
            json={"energy_level": 4, "midday_note": "Feeling good"},
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["success"] is True
        assert "id" in data

    def test_create_midday_minimal(self, authenticated_client, test_user):
        """Test creating midday check-in with only required fields."""
        response = authenticated_client.post(
            "/api/v1/checkins/midday",
            json={"energy_level": 3},
        )
        assert response.status_code in (200, 201)


class TestEveningCheckin:
    """Evening check-in tests."""

    def test_create_evening(self, authenticated_client, test_user):
        """Test creating an evening check-in."""
        response = authenticated_client.post(
            "/api/v1/checkins/evening",
            json={
                "training_quality": 4,
                "recovery_note": "Good recovery",
                "tomorrow_intention": "Drilling focus",
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["success"] is True
        assert "id" in data

    def test_create_evening_minimal(self, authenticated_client, test_user):
        """Test creating evening check-in with no optional fields."""
        response = authenticated_client.post(
            "/api/v1/checkins/evening",
            json={},
        )
        assert response.status_code in (200, 201)
