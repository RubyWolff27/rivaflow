"""Tests for admin Grapple AI Coach monitoring and feedback routes."""

# ── Access control ─────────────────────────────────────────────


class TestGrappleAccessControl:
    """Non-admin users are rejected on admin-only endpoints."""

    def test_unauthenticated_gets_401_on_stats(self, client, temp_db):
        resp = client.get("/api/v1/admin/grapple/stats/global")
        assert resp.status_code in (401, 403)

    def test_unauthenticated_gets_401_on_health(self, client, temp_db):
        resp = client.get("/api/v1/admin/grapple/health")
        assert resp.status_code in (401, 403)

    def test_non_admin_gets_403_on_global_stats(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/stats/global",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_projections(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/stats/projections",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_providers(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/stats/providers",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_users(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/stats/users",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_feedback_list(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/feedback",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_health(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/admin/grapple/health",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ── Feedback POST (any authenticated user) ─────────────────────


class TestGrappleFeedbackPost:
    """POST /admin/grapple/feedback is for any authenticated user."""

    def test_unauthenticated_gets_401(self, client, temp_db):
        resp = client.post(
            "/api/v1/admin/grapple/feedback",
            json={
                "message_id": "msg-123",
                "rating": "positive",
            },
        )
        assert resp.status_code in (401, 403)

    def test_non_admin_can_post_feedback(
        self, client, test_user, auth_headers, monkeypatch
    ):
        """Non-admin users CAN submit feedback (uses get_current_user)."""
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.submit_feedback",
            lambda **kwargs: {
                "feedback_id": 42,
                "message": "Thank you for your feedback!",
            },
        )
        resp = client.post(
            "/api/v1/admin/grapple/feedback",
            headers=auth_headers,
            json={
                "message_id": "msg-abc",
                "rating": "positive",
                "category": "helpful",
                "comment": "Great answer!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["feedback_id"] == 42
        assert "message" in data

    def test_admin_can_post_feedback(
        self, client, admin_user, admin_headers, monkeypatch
    ):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.submit_feedback",
            lambda **kwargs: {
                "feedback_id": 99,
                "message": "Thank you for your feedback!",
            },
        )
        resp = client.post(
            "/api/v1/admin/grapple/feedback",
            headers=admin_headers,
            json={
                "message_id": "msg-xyz",
                "rating": "negative",
            },
        )
        assert resp.status_code == 200


# ── Admin stats endpoints (monkeypatched) ──────────────────────


class TestGrappleStatsHappyPath:
    """Admin can access Grapple stats with monkeypatched service."""

    def test_global_stats(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.get_global_stats",
            lambda days=30: {
                "total_users": 10,
                "active_users_7d": 5,
                "total_sessions": 50,
                "total_messages": 200,
                "total_tokens": 100000,
                "total_cost_usd": 1.23,
                "by_provider": {"openai": {"count": 50}},
                "by_tier": {"free": {"users": 8}},
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/stats/global?days=7",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 10
        assert data["active_users_7d"] == 5
        assert data["total_sessions"] == 50
        assert data["total_messages"] == 200
        assert data["total_tokens"] == 100000
        assert "by_provider" in data
        assert "by_tier" in data

    def test_cost_projections(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.get_projections",
            lambda: {
                "current_month": {
                    "cost_so_far": 0.5,
                    "projected_total": 1.5,
                    "days_elapsed": 10,
                    "days_remaining": 20,
                },
                "daily_average": {
                    "last_7_days": 0.05,
                    "daily_costs": [],
                },
                "calculated_at": "2026-02-20T00:00:00",
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/stats/projections",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "current_month" in data
        assert "daily_average" in data
        assert "calculated_at" in data

    def test_provider_stats(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.get_provider_stats",
            lambda days=7: {
                "period_days": days,
                "start_date": "2026-02-13T00:00:00",
                "providers": [
                    {
                        "provider": "openai",
                        "model": "gpt-4",
                        "request_count": 100,
                        "total_tokens": 50000,
                        "input_tokens": 30000,
                        "output_tokens": 20000,
                        "total_cost_usd": 0.75,
                        "avg_tokens_per_request": 500.0,
                    }
                ],
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/stats/providers",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 7
        assert "providers" in data
        assert len(data["providers"]) == 1

    def test_user_stats(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.get_top_users",
            lambda limit=50: {
                "users": [
                    {
                        "user_id": 1,
                        "email": "top@example.com",
                        "subscription_tier": "premium",
                        "total_sessions": 20,
                        "total_messages": 80,
                        "total_tokens": 40000,
                        "total_cost_usd": 0.30,
                        "last_activity": "2026-02-20",
                    }
                ],
                "total_returned": 1,
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/stats/users",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert data["total_returned"] == 1

    def test_feedback_list(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.get_feedback",
            lambda limit=100, rating=None: {
                "feedback": [],
                "total_returned": 0,
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/feedback",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "feedback" in data
        assert data["total_returned"] == 0

    def test_health_check(self, client, admin_user, admin_headers, monkeypatch):
        monkeypatch.setattr(
            "rivaflow.core.services.grapple_admin_service"
            ".GrappleAdminService.check_health",
            lambda: {
                "overall_status": "healthy",
                "llm_client": {
                    "status": "healthy",
                    "providers": {},
                },
                "database": {"status": "healthy"},
                "checked_at": "2026-02-20T00:00:00",
            },
        )
        resp = client.get(
            "/api/v1/admin/grapple/health",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_status"] == "healthy"
        assert data["llm_client"]["status"] == "healthy"
        assert data["database"]["status"] == "healthy"
