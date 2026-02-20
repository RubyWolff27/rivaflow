"""Tests for admin user management, comments, techniques, audit logs, and feedback routes."""

from rivaflow.core.auth import hash_password
from rivaflow.db.repositories.user_repo import UserRepository


def _create_extra_user(email="extra@example.com"):
    """Create an additional user directly in the database."""
    user_repo = UserRepository()
    return user_repo.create(
        email=email,
        hashed_password=hash_password("ExtraPass123!secure"),
        first_name="Extra",
        last_name="User",
    )


# ── Access control ─────────────────────────────────────────────


class TestUsersAccessControl:
    """Non-admin users are rejected."""

    def test_unauthenticated_gets_401(self, client, temp_db):
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code in (401, 403)

    def test_non_admin_gets_403_on_users(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/users", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_comments(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/comments", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_techniques(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/techniques", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_audit_logs(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/audit-logs", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_feedback(self, client, test_user, auth_headers):
        resp = client.get("/api/v1/admin/feedback", headers=auth_headers)
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_feedback_stats(
        self, client, test_user, auth_headers
    ):
        resp = client.get(
            "/api/v1/admin/feedback/stats",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ── User listing ───────────────────────────────────────────────


class TestUsersListing:
    """Admin can list and search users."""

    def test_list_users(self, client, admin_user, admin_headers):
        resp = client.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        assert data["total"] >= 1

    def test_list_users_with_search(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/users?search=admin",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_list_users_pagination(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/users?limit=1&offset=0",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) <= 1

    def test_list_users_filter_is_admin(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/users?is_admin=true",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


# ── User details ───────────────────────────────────────────────


class TestUsersDetails:
    """Admin can get detailed user info."""

    def test_get_user_details(self, client, admin_user, admin_headers):
        extra = _create_extra_user()
        resp = client.get(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "extra@example.com"
        assert "stats" in data

    def test_get_nonexistent_user_returns_404(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/users/99999",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ── User update ────────────────────────────────────────────────


class TestUsersUpdate:
    """Admin can update user fields."""

    def test_update_subscription_tier(self, client, admin_user, admin_headers):
        extra = _create_extra_user("tier@example.com")
        resp = client.put(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
            json={"subscription_tier": "premium"},
        )
        assert resp.status_code == 200
        updated = UserRepository.get_by_id(extra["id"])
        assert updated["subscription_tier"] == "premium"

    def test_update_is_active(self, client, admin_user, admin_headers):
        extra = _create_extra_user("active@example.com")
        resp = client.put(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200
        updated = UserRepository.get_by_id(extra["id"])
        assert not updated["is_active"]

    def test_update_is_beta_user(self, client, admin_user, admin_headers):
        extra = _create_extra_user("beta@example.com")
        resp = client.put(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
            json={"is_beta_user": True},
        )
        assert resp.status_code == 200

    def test_update_nonexistent_user_returns_404(
        self, client, admin_user, admin_headers
    ):
        resp = client.put(
            "/api/v1/admin/users/99999",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 404

    def test_invalid_subscription_tier_returns_422(
        self, client, admin_user, admin_headers
    ):
        extra = _create_extra_user("invalid@example.com")
        resp = client.put(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
            json={"subscription_tier": "ultra_mega"},
        )
        assert resp.status_code == 422


# ── Delete user ────────────────────────────────────────────────


class TestUsersDelete:
    """Admin can delete users but not self."""

    def test_delete_user(self, client, admin_user, admin_headers):
        extra = _create_extra_user("delete@example.com")
        resp = client.delete(
            f"/api/v1/admin/users/{extra['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

        # Verify user is gone
        deleted = UserRepository.get_by_id(extra["id"])
        assert deleted is None

    def test_cannot_delete_self(self, client, admin_user, admin_headers):
        resp = client.delete(
            f"/api/v1/admin/users/{admin_user['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_delete_nonexistent_user_returns_404(
        self, client, admin_user, admin_headers
    ):
        resp = client.delete(
            "/api/v1/admin/users/99999",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ── Comments moderation ────────────────────────────────────────


class TestCommentsModeration:
    """Admin can list and delete comments."""

    def test_list_comments(self, client, admin_user, admin_headers):
        resp = client.get("/api/v1/admin/comments", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "comments" in data
        assert "total" in data

    def test_list_comments_pagination(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/comments?limit=5&offset=0",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["comments"]) <= 5

    def test_delete_nonexistent_comment_returns_404(
        self, client, admin_user, admin_headers
    ):
        resp = client.delete(
            "/api/v1/admin/comments/99999",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ── Techniques management ──────────────────────────────────────


class TestTechniquesManagement:
    """Admin can list and delete techniques."""

    def test_list_techniques(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/techniques",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "techniques" in data
        assert "count" in data

    def test_list_techniques_with_search(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/techniques?search=armbar",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "techniques" in data

    def test_delete_nonexistent_technique_returns_404(
        self, client, admin_user, admin_headers
    ):
        resp = client.delete(
            "/api/v1/admin/techniques/99999",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ── Audit logs ─────────────────────────────────────────────────


class TestAuditLogs:
    """Admin can view audit logs."""

    def test_get_audit_logs(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/audit-logs",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_audit_logs_pagination(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/audit-logs?limit=5&offset=0",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) <= 5

    def test_audit_logs_filter_by_action(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/audit-logs?action=user.update",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data


# ── Feedback management ────────────────────────────────────────


class TestFeedbackManagement:
    """Admin can list, filter, and update feedback."""

    def _create_feedback(self, user_id):
        """Insert a feedback record directly in the DB."""
        from rivaflow.db.repositories.feedback_repo import (
            FeedbackRepository,
        )

        return FeedbackRepository.create(
            user_id=user_id,
            category="bug",
            message="Something is broken",
            subject="Bug report",
        )

    def test_list_feedback(self, client, admin_user, admin_headers):
        resp = client.get("/api/v1/admin/feedback", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "feedback" in data
        assert "count" in data
        assert "stats" in data

    def test_list_feedback_with_status_filter(self, client, admin_user, admin_headers):
        self._create_feedback(admin_user["id"])
        resp = client.get(
            "/api/v1/admin/feedback?status=new",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "feedback" in data

    def test_list_feedback_with_category_filter(
        self, client, admin_user, admin_headers
    ):
        self._create_feedback(admin_user["id"])
        resp = client.get(
            "/api/v1/admin/feedback?category=bug",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "feedback" in data

    def test_get_feedback_stats(self, client, admin_user, admin_headers):
        resp = client.get(
            "/api/v1/admin/feedback/stats",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_category" in data

    def test_update_feedback_status(self, client, admin_user, admin_headers):
        feedback_id = self._create_feedback(admin_user["id"])
        resp = client.put(
            f"/api/v1/admin/feedback/{feedback_id}/status",
            headers=admin_headers,
            json={
                "status": "reviewing",
                "admin_notes": "Looking into it",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "reviewing"

    def test_update_feedback_to_resolved(self, client, admin_user, admin_headers):
        feedback_id = self._create_feedback(admin_user["id"])
        resp = client.put(
            f"/api/v1/admin/feedback/{feedback_id}/status",
            headers=admin_headers,
            json={
                "status": "resolved",
                "admin_notes": "Fixed in v2.1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"

    def test_update_nonexistent_feedback_returns_404(
        self, client, admin_user, admin_headers
    ):
        resp = client.put(
            "/api/v1/admin/feedback/99999/status",
            headers=admin_headers,
            json={"status": "closed"},
        )
        assert resp.status_code == 404

    def test_invalid_feedback_status_returns_422(
        self, client, admin_user, admin_headers
    ):
        feedback_id = self._create_feedback(admin_user["id"])
        resp = client.put(
            f"/api/v1/admin/feedback/{feedback_id}/status",
            headers=admin_headers,
            json={"status": "invalid_status"},
        )
        assert resp.status_code == 422
