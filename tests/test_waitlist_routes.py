"""Integration tests for waitlist routes (public and admin)."""

from datetime import timedelta

from rivaflow.core.auth import create_access_token
from rivaflow.db.database import convert_query, get_connection


def _make_admin(user_id):
    """Promote a user to admin."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE users SET is_admin = ? WHERE id = ?"),
            (True, user_id),
        )


class TestJoinWaitlist:
    """Tests for POST /api/v1/waitlist/join."""

    def test_join_waitlist(self, client, temp_db):
        """Test joining the waitlist with valid data."""
        response = client.post(
            "/api/v1/waitlist/join",
            json={"email": "newuser@example.com"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "position" in data
        assert "message" in data

    def test_join_waitlist_with_all_fields(self, client, temp_db):
        """Test joining the waitlist with all optional fields."""
        response = client.post(
            "/api/v1/waitlist/join",
            json={
                "email": "full@example.com",
                "first_name": "John",
                "gym_name": "Test Gym",
                "belt_rank": "white",
                "referral_source": "friend",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["position"] >= 1

    def test_join_waitlist_duplicate(self, client, temp_db):
        """Test joining the waitlist with an existing email."""
        client.post(
            "/api/v1/waitlist/join",
            json={"email": "dup@example.com"},
        )
        response = client.post(
            "/api/v1/waitlist/join",
            json={"email": "dup@example.com"},
        )
        # Duplicate returns 201 but with "already on the list" message
        assert response.status_code == 201
        data = response.json()
        assert "already" in data["message"].lower()

    def test_join_waitlist_invalid_email(self, client, temp_db):
        """Test joining with invalid email is rejected."""
        response = client.post(
            "/api/v1/waitlist/join",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


class TestWaitlistCount:
    """Tests for GET /api/v1/waitlist/count."""

    def test_get_count_empty(self, client, temp_db):
        """Test getting waitlist count when empty."""
        response = client.get("/api/v1/waitlist/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_get_count_after_join(self, client, temp_db):
        """Test count increases after joining."""
        client.post(
            "/api/v1/waitlist/join",
            json={"email": "counted@example.com"},
        )
        response = client.get("/api/v1/waitlist/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestAdminWaitlistList:
    """Tests for GET /api/v1/admin/waitlist/."""

    def test_list_requires_auth(self, client, temp_db):
        """Test admin waitlist list requires authentication."""
        response = client.get("/api/v1/admin/waitlist/")
        assert response.status_code in (401, 403)

    def test_list_requires_admin(self, authenticated_client, test_user):
        """Test non-admin user gets 403 for admin endpoint."""
        response = authenticated_client.get("/api/v1/admin/waitlist/")
        assert response.status_code == 403

    def test_list_as_admin(self, client, test_user, temp_db):
        """Test admin can list waitlist entries."""
        _make_admin(test_user["id"])
        token = create_access_token(
            data={"sub": str(test_user["id"])},
            expires_delta=timedelta(hours=1),
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/admin/waitlist/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data


class TestAdminWaitlistStats:
    """Tests for GET /api/v1/admin/waitlist/stats."""

    def test_stats_requires_admin(self, authenticated_client, test_user):
        """Test non-admin user gets 403 for stats."""
        response = authenticated_client.get("/api/v1/admin/waitlist/stats")
        assert response.status_code == 403

    def test_stats_as_admin(self, client, test_user, temp_db):
        """Test admin can view waitlist stats."""
        _make_admin(test_user["id"])
        token = create_access_token(
            data={"sub": str(test_user["id"])},
            expires_delta=timedelta(hours=1),
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/admin/waitlist/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "waiting" in data
        assert "invited" in data
