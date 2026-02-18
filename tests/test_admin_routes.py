"""Tests for admin API routes (Wave 4 coverage).

Covers:
- Non-admin users receive 403 on admin endpoints
- Admin users can access admin endpoints
- User listing via /admin/users
- User deactivation via PUT /admin/users/{id}
- Dashboard stats endpoint
"""

from datetime import timedelta

from rivaflow.core.auth import create_access_token
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.user_repo import UserRepository


def _make_admin(user_id: int) -> None:
    """Promote a user to admin in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE users SET is_admin = ? WHERE id = ?"),
            (True, user_id),
        )


def _admin_token(user_id: int) -> str:
    """Create a JWT token for the given user."""
    return create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(hours=1),
    )


def _admin_headers(user_id: int) -> dict:
    return {"Authorization": f"Bearer {_admin_token(user_id)}"}


# ── Access control ─────────────────────────────────────────────


class TestAdminAccessControl:
    """Non-admin users are rejected with 403."""

    def test_non_admin_gets_403_on_users(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/users", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_gyms(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/gyms", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_dashboard(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client, temp_db):
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code in (401, 403)


# ── Admin user list ────────────────────────────────────────────


class TestAdminUserList:
    """GET /admin/users returns paginated user list."""

    def test_list_users(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        assert data["total"] >= 1

    def test_list_users_with_search(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get(
            "/api/v1/admin/users?search=test",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_list_users_pagination(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get(
            "/api/v1/admin/users?limit=1&offset=0",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) <= 1


# ── User deactivation ─────────────────────────────────────────


class TestAdminUserDeactivation:
    """PUT /admin/users/{id} can deactivate a user."""

    def test_deactivate_user(self, client, test_user, test_user2):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        target_id = test_user2["id"]

        resp = client.put(
            f"/api/v1/admin/users/{target_id}",
            headers=headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200

        # Verify the user is now inactive
        updated = UserRepository.get_by_id(target_id)
        assert updated is not None
        assert not updated["is_active"]

    def test_reactivate_user(self, client, test_user, test_user2):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        target_id = test_user2["id"]

        # Deactivate first
        client.put(
            f"/api/v1/admin/users/{target_id}",
            headers=headers,
            json={"is_active": False},
        )
        # Then reactivate
        resp = client.put(
            f"/api/v1/admin/users/{target_id}",
            headers=headers,
            json={"is_active": True},
        )
        assert resp.status_code == 200
        updated = UserRepository.get_by_id(target_id)
        assert updated["is_active"]

    def test_update_nonexistent_user_returns_404(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.put(
            "/api/v1/admin/users/99999",
            headers=headers,
            json={"is_active": False},
        )
        assert resp.status_code == 404


# ── User detail ────────────────────────────────────────────────


class TestAdminUserDetail:
    """GET /admin/users/{id} returns detailed info."""

    def test_get_user_detail(self, client, test_user, test_user2):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get(
            f"/api/v1/admin/users/{test_user2['id']}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test2@example.com"
        assert "stats" in data
        assert "sessions" in data["stats"]

    def test_get_nonexistent_user_returns_404(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get(
            "/api/v1/admin/users/99999",
            headers=headers,
        )
        assert resp.status_code == 404


# ── Dashboard stats ────────────────────────────────────────────


class TestAdminDashboard:
    """GET /admin/dashboard/stats returns platform stats."""

    def test_dashboard_stats(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "total_sessions" in data
        assert "total_gyms" in data
        assert data["total_users"] >= 1


# ── Subscription tier update ───────────────────────────────────


class TestAdminSubscriptionUpdate:
    """Admin can change subscription tier."""

    def test_update_subscription_tier(self, client, test_user, test_user2):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        target_id = test_user2["id"]

        resp = client.put(
            f"/api/v1/admin/users/{target_id}",
            headers=headers,
            json={"subscription_tier": "premium"},
        )
        assert resp.status_code == 200

        updated = UserRepository.get_by_id(target_id)
        assert updated["subscription_tier"] == "premium"


# ── Delete user ────────────────────────────────────────────────


class TestAdminDeleteUser:
    """DELETE /admin/users/{id} removes a user."""

    def test_delete_user(self, client, test_user, test_user2):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        target_id = test_user2["id"]

        resp = client.delete(
            f"/api/v1/admin/users/{target_id}",
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify deletion
        deleted = UserRepository.get_by_id(target_id)
        assert deleted is None

    def test_cannot_delete_self(self, client, test_user):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.delete(
            f"/api/v1/admin/users/{test_user['id']}",
            headers=headers,
        )
        # Should be rejected (ValidationError -> 400)
        assert resp.status_code == 400
