"""Tests for grapple usage routes (/api/v1/grapple/ tier & usage endpoints)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from rivaflow.core.auth import create_access_token, hash_password
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.user_repo import UserRepository


def _make_premium_user(temp_db):
    """Create a premium-tier user for grapple access."""
    user_repo = UserRepository()
    user = user_repo.create(
        email="premium_usage@example.com",
        hashed_password=hash_password("TestPass123!secure"),
        first_name="Premium",
        last_name="Usage",
        subscription_tier="premium",
        is_beta_user=True,
    )
    return user


def _make_premium_headers(user):
    """Create auth headers for a premium user."""
    token = create_access_token(data={"sub": str(user["id"])})
    return {"Authorization": f"Bearer {token}"}


def _upgrade_user_to_premium(user_id):
    """Upgrade an existing user to premium tier via DB."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE users SET subscription_tier = ?,"
                " is_beta_user = ? WHERE id = ?"
            ),
            ("premium", True, user_id),
        )
        conn.commit()


def _build_mock_token_monitor():
    """Build a mock GrappleTokenMonitor with sensible defaults."""
    monitor = MagicMock()
    monitor.get_user_usage.return_value = {
        "total_tokens": 5000,
        "total_cost_usd": 0.05,
        "message_count": 25,
    }
    monitor.get_cost_projection.return_value = {
        "projected_monthly_cost_usd": 1.50,
        "daily_average_cost_usd": 0.05,
    }
    monitor.check_cost_limit.return_value = {
        "allowed": True,
        "remaining_usd": 48.50,
        "limit_usd": 50.0,
    }
    return monitor


def _build_mock_rate_limiter():
    """Build a mock GrappleRateLimiter with sensible defaults."""
    limiter = MagicMock()
    reset_time = datetime.now(UTC) + timedelta(minutes=30)
    limiter.get_user_usage_stats.return_value = {
        "messages_last_7_days": 42,
        "daily_breakdown": [],
    }
    limiter.check_rate_limit.return_value = {
        "allowed": True,
        "remaining": 35,
        "limit": 60,
        "reset_at": reset_time,
    }
    return limiter


# ====================================================================
# Authentication Tests
# ====================================================================


class TestGrappleUsageAuth:
    """Auth tests for grapple usage endpoints."""

    def test_info_unauthenticated(self, client, temp_db):
        """GET /info without auth returns 401."""
        resp = client.get("/api/v1/grapple/info")
        assert resp.status_code == 401

    def test_teaser_unauthenticated(self, client, temp_db):
        """GET /teaser without auth returns 401."""
        resp = client.get("/api/v1/grapple/teaser")
        assert resp.status_code == 401

    def test_usage_unauthenticated(self, client, temp_db):
        """GET /usage without auth returns 401."""
        resp = client.get("/api/v1/grapple/usage")
        assert resp.status_code == 401


# ====================================================================
# /info Endpoint
# ====================================================================


class TestGrappleInfo:
    """Tests for GET /api/v1/grapple/info."""

    def test_info_free_user(self, client, test_user, auth_headers):
        """Free user gets tier info with grapple disabled."""
        resp = client.get(
            "/api/v1/grapple/info",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["is_beta"] is False
        assert "features" in data
        assert "limits" in data
        assert data["features"]["grapple"] is False
        assert data["limits"]["grapple_messages_per_hour"] == 0

    def test_info_premium_user(self, client, temp_db):
        """Premium user gets tier info with grapple enabled."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/info",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "premium"
        assert data["is_beta"] is True
        assert data["features"]["grapple"] is True
        assert data["limits"]["grapple_messages_per_hour"] == 60
        assert data["limits"]["monthly_cost_limit_usd"] == 50.0

    def test_info_upgraded_user(self, client, test_user, auth_headers):
        """User upgraded to premium sees updated tier info."""
        _upgrade_user_to_premium(test_user["id"])

        resp = client.get(
            "/api/v1/grapple/info",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "premium"
        assert data["features"]["grapple"] is True

    def test_info_response_shape(self, client, test_user, auth_headers):
        """Response matches TierInfoResponse schema."""
        resp = client.get(
            "/api/v1/grapple/info",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        # All required fields present
        assert "tier" in data
        assert "is_beta" in data
        assert "features" in data
        assert "limits" in data
        # Features dict has expected keys
        assert "grapple" in data["features"]
        assert "advanced_analytics" in data["features"]
        assert "api_access" in data["features"]


# ====================================================================
# /teaser Endpoint
# ====================================================================


class TestGrappleTeaser:
    """Tests for GET /api/v1/grapple/teaser."""

    def test_teaser_free_user_no_access(self, client, test_user, auth_headers):
        """Free user sees has_access=false with upgrade info."""
        resp = client.get(
            "/api/v1/grapple/teaser",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["has_access"] is False
        assert data["current_tier"] == "free"
        assert data["upgrade_url"] is not None
        assert "grapple_features" in data
        assert "beta_features" in data
        assert "premium_features" in data
        assert "Upgrade" in data["message"]

    def test_teaser_premium_user_has_access(self, client, temp_db):
        """Premium user sees has_access=true."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/teaser",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["has_access"] is True
        assert data["current_tier"] == "premium"
        assert data["upgrade_url"] is None
        assert "You have access" in data["message"]

    def test_teaser_has_feature_lists(self, client, test_user, auth_headers):
        """Teaser response includes feature description lists."""
        resp = client.get(
            "/api/v1/grapple/teaser",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["grapple_features"], list)
        assert len(data["grapple_features"]) > 0
        assert isinstance(data["beta_features"], list)
        assert len(data["beta_features"]) > 0
        assert isinstance(data["premium_features"], list)
        assert len(data["premium_features"]) > 0

    def test_teaser_upgraded_user_sees_access(self, client, test_user, auth_headers):
        """Upgraded user sees has_access=true."""
        _upgrade_user_to_premium(test_user["id"])

        resp = client.get(
            "/api/v1/grapple/teaser",
            headers=auth_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["has_access"] is True


# ====================================================================
# /usage Endpoint
# ====================================================================


class TestGrappleUsage:
    """Tests for GET /api/v1/grapple/usage."""

    def test_usage_free_user_denied(self, client, test_user, auth_headers):
        """Free user gets 403 on /usage (requires beta/premium)."""
        resp = client.get(
            "/api/v1/grapple/usage",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_usage_premium_user_success(self, client, temp_db):
        """Premium user gets usage stats with mocked services."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "premium"
        assert data["user_id"] == user["id"]
        assert "usage_30_days" in data
        assert "cost_projection" in data
        assert "cost_limit" in data
        assert "rate_limit" in data
        assert "limits" in data

    def test_usage_response_shape(self, client, temp_db):
        """Verify the full response structure."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()

        # Top-level keys
        assert "user_id" in data
        assert "tier" in data
        assert "usage_30_days" in data
        assert "cost_projection" in data
        assert "cost_limit" in data
        assert "rate_limit" in data
        assert "limits" in data

        # Rate limit sub-structure
        rate_limit = data["rate_limit"]
        assert "current_status" in rate_limit
        assert "weekly_stats" in rate_limit

        status = rate_limit["current_status"]
        assert "allowed" in status
        assert "remaining" in status
        assert "limit" in status
        assert "reset_at" in status

        # Limits sub-structure
        limits = data["limits"]
        assert "messages_per_hour" in limits
        assert "monthly_cost_limit_usd" in limits

    def test_usage_token_values(self, client, temp_db):
        """Verify mock token usage values are returned."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()

        # Token monitor values
        assert data["usage_30_days"]["total_tokens"] == 5000
        assert data["usage_30_days"]["message_count"] == 25
        assert data["cost_projection"]["projected_monthly_cost_usd"] == 1.50
        assert data["cost_limit"]["allowed"] is True
        assert data["cost_limit"]["remaining_usd"] == 48.50

    def test_usage_rate_limit_values(self, client, temp_db):
        """Verify mock rate limiter values are returned."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()

        status = data["rate_limit"]["current_status"]
        assert status["allowed"] is True
        assert status["remaining"] == 35
        assert status["limit"] == 60

        weekly = data["rate_limit"]["weekly_stats"]
        assert weekly["messages_last_7_days"] == 42

    def test_usage_limits_match_premium_tier(self, client, temp_db):
        """Limits section reflects premium tier values."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["limits"]["messages_per_hour"] == 60
        assert data["limits"]["monthly_cost_limit_usd"] == 50.0

    def test_usage_upgraded_user(self, client, test_user, auth_headers):
        """User upgraded to premium can access /usage."""
        _upgrade_user_to_premium(test_user["id"])

        mock_monitor = _build_mock_token_monitor()
        mock_limiter = _build_mock_rate_limiter()

        with (
            patch(
                "rivaflow.core.services.grapple" ".token_monitor.GrappleTokenMonitor",
                return_value=mock_monitor,
            ),
            patch(
                "rivaflow.core.services.grapple" ".rate_limiter.GrappleRateLimiter",
                return_value=mock_limiter,
            ),
        ):
            resp = client.get(
                "/api/v1/grapple/usage",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "premium"
