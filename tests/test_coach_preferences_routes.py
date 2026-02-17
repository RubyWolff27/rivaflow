"""Integration tests for coach preferences routes."""


class TestGetCoachPreferences:
    """Tests for GET /api/v1/coach-preferences/."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/coach-preferences/")
        assert resp.status_code == 401

    def test_get_returns_defaults_when_none_set(self, authenticated_client, test_user):
        """Returns default preferences for new user."""
        resp = authenticated_client.get("/api/v1/coach-preferences/")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        prefs = data["data"]
        assert prefs["belt_level"] == "white"
        assert prefs["training_mode"] == "lifestyle"
        assert prefs["coaching_style"] == "balanced"
        assert prefs["primary_position"] == "both"
        assert prefs["competition_experience"] == "none"
        assert prefs["available_days_per_week"] == 4

    def test_get_returns_saved_preferences(self, authenticated_client, test_user):
        """After updating, GET returns saved values."""
        # First update
        authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"belt_level": "blue"},
        )
        # Then read back
        resp = authenticated_client.get("/api/v1/coach-preferences/")
        assert resp.status_code == 200
        prefs = resp.json()["data"]
        assert prefs["belt_level"] == "blue"


class TestUpdateCoachPreferences:
    """Tests for PUT /api/v1/coach-preferences/."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.put(
            "/api/v1/coach-preferences/",
            json={"belt_level": "blue"},
        )
        assert resp.status_code == 401

    def test_update_belt_level(self, authenticated_client, test_user):
        """Can update belt level."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"belt_level": "purple"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert data["data"]["belt_level"] == "purple"

    def test_update_training_mode(self, authenticated_client, test_user):
        """Can update training mode."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"training_mode": "competition_prep"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["training_mode"] == "competition_prep"

    def test_update_coaching_style(self, authenticated_client, test_user):
        """Can update coaching style."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"coaching_style": "analytical"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["coaching_style"] == "analytical"

    def test_update_multiple_fields(self, authenticated_client, test_user):
        """Can update several fields at once."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={
                "belt_level": "brown",
                "primary_position": "top",
                "available_days_per_week": 6,
                "coaching_style": "tough_love",
            },
        )
        assert resp.status_code == 200
        prefs = resp.json()["data"]
        assert prefs["belt_level"] == "brown"
        assert prefs["primary_position"] == "top"
        assert prefs["available_days_per_week"] == 6
        assert prefs["coaching_style"] == "tough_love"

    def test_update_invalid_belt_level_returns_error(
        self, authenticated_client, test_user
    ):
        """Invalid belt level returns error in response."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"belt_level": "rainbow"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_update_invalid_training_mode_returns_error(
        self, authenticated_client, test_user
    ):
        """Invalid training mode returns error in response."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"training_mode": "invalid_mode"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_update_days_per_week_clamped(self, authenticated_client, test_user):
        """Days per week is clamped between 1 and 7."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={"available_days_per_week": 10},
        )
        assert resp.status_code == 200
        prefs = resp.json()["data"]
        assert prefs["available_days_per_week"] == 7

    def test_update_with_focus_areas(self, authenticated_client, test_user):
        """Can set focus areas list."""
        resp = authenticated_client.put(
            "/api/v1/coach-preferences/",
            json={
                "focus_areas": [
                    "guard passing",
                    "submissions",
                ]
            },
        )
        assert resp.status_code == 200
        prefs = resp.json()["data"]
        assert "focus_areas" in prefs
