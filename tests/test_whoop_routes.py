"""Integration tests for WHOOP integration routes (16 endpoints)."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from rivaflow.core.dependencies import get_whoop_service


@pytest.fixture(autouse=True)
def enable_whoop(monkeypatch):
    """Enable the WHOOP feature flag for all tests in this module."""
    monkeypatch.setenv("ENABLE_WHOOP_INTEGRATION", "true")
    from rivaflow.core.settings import settings

    monkeypatch.setattr(settings, "ENABLE_WHOOP_INTEGRATION", True)


@pytest.fixture()
def mock_whoop_service(client):
    """Override get_whoop_service DI so endpoints use a mock instance."""
    svc = MagicMock()
    client.app.dependency_overrides[get_whoop_service] = lambda: svc
    yield svc
    client.app.dependency_overrides.pop(get_whoop_service, None)


# ============================================================================
# OAuth flow
# ============================================================================


class TestWhoopAuthorize:
    """GET /api/v1/integrations/whoop/authorize"""

    def test_returns_authorization_url(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.initiate_oauth.return_value = (
            "https://api.prod.whoop.com/oauth/authorize?client_id=test"
        )
        response = authenticated_client.get("/api/v1/integrations/whoop/authorize")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert data["authorization_url"].startswith("https://")

    def test_requires_auth(self, client, temp_db):
        response = client.get("/api/v1/integrations/whoop/authorize")
        assert response.status_code == 401


class TestWhoopCallback:
    """GET /api/v1/integrations/whoop/callback"""

    def test_callback_success(self, client, temp_db, mock_whoop_service):
        """Successful OAuth callback redirects to profile."""
        mock_whoop_service.handle_callback.return_value = None
        response = client.get(
            "/api/v1/integrations/whoop/callback",
            params={"code": "test_code", "state": "test_state"},
            follow_redirects=False,
        )
        assert response.status_code in (302, 307)
        assert "whoop=connected" in response.headers.get("location", "")

    def test_callback_error(self, client, temp_db, mock_whoop_service):
        """Callback with error parameter redirects with error."""
        response = client.get(
            "/api/v1/integrations/whoop/callback",
            params={"error": "access_denied"},
            follow_redirects=False,
        )
        assert response.status_code in (302, 307)
        assert "whoop=error" in response.headers.get("location", "")

    def test_callback_missing_params(self, client, temp_db, mock_whoop_service):
        """Callback without code or state redirects with error."""
        response = client.get(
            "/api/v1/integrations/whoop/callback",
            follow_redirects=False,
        )
        assert response.status_code in (302, 307)
        assert "whoop=error" in response.headers.get("location", "")


# ============================================================================
# Status & scope
# ============================================================================


class TestWhoopStatus:
    """GET /api/v1/integrations/whoop/status"""

    def test_connected_status(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.get_connection_status.return_value = {
            "connected": True,
            "last_synced_at": "2025-01-01T00:00:00",
        }
        response = authenticated_client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 200
        assert response.json()["connected"] is True

    def test_disconnected_status(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.get_connection_status.return_value = {
            "connected": False,
        }
        response = authenticated_client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 200
        assert response.json()["connected"] is False


class TestWhoopScopeCheck:
    """GET /api/v1/integrations/whoop/scope-check"""

    def test_scope_check(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.check_scope_compatibility.return_value = {
            "needs_reauth": False,
            "current_scopes": ["read:workout", "read:recovery"],
        }
        response = authenticated_client.get("/api/v1/integrations/whoop/scope-check")
        assert response.status_code == 200
        assert response.json()["needs_reauth"] is False


# ============================================================================
# Sync operations
# ============================================================================


class TestWhoopSync:
    """POST /api/v1/integrations/whoop/sync"""

    def test_sync_workouts(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.sync_workouts.return_value = {
            "total_fetched": 5,
            "created": 3,
            "updated": 2,
            "auto_sessions_created": 1,
        }
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["total_fetched"] == 5

    def test_sync_not_connected(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        from rivaflow.core.exceptions import NotFoundError

        mock_whoop_service.sync_workouts.side_effect = NotFoundError(
            "WHOOP not connected"
        )
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 400


class TestWhoopSyncRecovery:
    """POST /api/v1/integrations/whoop/sync-recovery"""

    def test_sync_recovery(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.sync_recovery.return_value = {
            "total_fetched": 7,
            "created": 5,
            "updated": 2,
        }
        response = authenticated_client.post("/api/v1/integrations/whoop/sync-recovery")
        assert response.status_code == 200
        data = response.json()
        assert data["total_fetched"] == 7

    def test_sync_recovery_not_connected(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        from rivaflow.core.exceptions import NotFoundError

        mock_whoop_service.sync_recovery.side_effect = NotFoundError(
            "WHOOP not connected"
        )
        response = authenticated_client.post("/api/v1/integrations/whoop/sync-recovery")
        assert response.status_code == 400


# ============================================================================
# Data retrieval
# ============================================================================


class TestWhoopWorkouts:
    """GET /api/v1/integrations/whoop/workouts"""

    def test_get_workouts(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.workout_cache_repo = MagicMock()
        mock_whoop_service.workout_cache_repo.get_by_user_and_time_range.return_value = [
            {"id": 1, "sport_name": "Brazilian Jiu-Jitsu", "strain": 12.5}
        ]
        response = authenticated_client.get("/api/v1/integrations/whoop/workouts")
        assert response.status_code == 200
        data = response.json()
        assert "workouts" in data
        assert "count" in data

    def test_get_workouts_by_session(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.find_matching_workouts.return_value = []
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/workouts",
            params={"session_id": 1},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0


class TestWhoopLatestRecovery:
    """GET /api/v1/integrations/whoop/recovery/latest"""

    def test_latest_recovery(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.get_latest_recovery.return_value = {
            "recovery_score": 78,
            "hrv_ms": 55.2,
            "resting_hr": 52,
        }
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/recovery/latest"
        )
        assert response.status_code == 200
        assert response.json()["recovery_score"] == 78

    def test_no_recovery_data(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.get_latest_recovery.return_value = None
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/recovery/latest"
        )
        assert response.status_code == 200
        assert "message" in response.json()


class TestWhoopReadinessAutoFill:
    """GET /api/v1/integrations/whoop/readiness/auto-fill"""

    def test_auto_fill(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.apply_recovery_to_readiness.return_value = {
            "sleep": 4,
            "energy": 3,
            "hrv_ms": 55.2,
        }
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/readiness/auto-fill",
            params={"date": date.today().isoformat()},
        )
        assert response.status_code == 200
        assert response.json()["auto_fill"]["sleep"] == 4

    def test_auto_fill_no_data(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.apply_recovery_to_readiness.return_value = None
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/readiness/auto-fill",
            params={"date": date.today().isoformat()},
        )
        assert response.status_code == 200
        assert response.json()["auto_fill"] is None


# ============================================================================
# Session matching
# ============================================================================


class TestWhoopMatch:
    """POST /api/v1/integrations/whoop/match"""

    def test_match_workout(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.apply_workout_to_session.return_value = {
            "id": 1,
            "whoop_strain": 12.5,
        }
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/match",
            json={"session_id": 1, "workout_cache_id": 10},
        )
        assert response.status_code == 200

    def test_match_workout_not_found(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        from rivaflow.core.exceptions import NotFoundError

        mock_whoop_service.apply_workout_to_session.side_effect = NotFoundError(
            "Session not found"
        )
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/match",
            json={"session_id": 999, "workout_cache_id": 10},
        )
        assert response.status_code == 404


class TestWhoopSessionContext:
    """GET /api/v1/integrations/whoop/session/{session_id}/context"""

    def test_session_context(self, authenticated_client, test_user, session_factory):
        """Test getting WHOOP context for a session (no WHOOP data)."""
        session_id = session_factory()
        response = authenticated_client.get(
            f"/api/v1/integrations/whoop/session/{session_id}/context"
        )
        assert response.status_code == 200
        data = response.json()
        assert "recovery" in data
        assert "workout" in data

    def test_session_context_not_found(self, authenticated_client, test_user):
        """Test context for nonexistent session returns 404."""
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/session/99999/context"
        )
        assert response.status_code == 404


# ============================================================================
# Zones
# ============================================================================


class TestWhoopZonesBatch:
    """GET /api/v1/integrations/whoop/zones/batch"""

    def test_zones_batch(self, authenticated_client, test_user, session_factory):
        """Test batch zone data retrieval."""
        sid = session_factory()
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/zones/batch",
            params={"session_ids": str(sid)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data

    def test_zones_batch_empty(self, authenticated_client, test_user):
        """Test batch zones with no valid session IDs."""
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/zones/batch",
            params={"session_ids": ""},
        )
        assert response.status_code == 200


class TestWhoopZonesWeekly:
    """GET /api/v1/integrations/whoop/zones/weekly"""

    def test_zones_weekly(self, authenticated_client, test_user):
        """Test weekly zone summary."""
        response = authenticated_client.get(
            "/api/v1/integrations/whoop/zones/weekly",
            params={"week_offset": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "session_count" in data
        assert "week_start" in data
        assert "week_end" in data


# ============================================================================
# Toggles
# ============================================================================


class TestWhoopAutoCreate:
    """POST /api/v1/integrations/whoop/auto-create-sessions"""

    def test_enable_auto_create(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.set_auto_create_sessions.return_value = {
            "auto_create_sessions": True,
        }
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/auto-create-sessions",
            json={"enabled": True},
        )
        assert response.status_code == 200

    def test_disable_auto_create(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.set_auto_create_sessions.return_value = {
            "auto_create_sessions": False,
        }
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/auto-create-sessions",
            json={"enabled": False},
        )
        assert response.status_code == 200


class TestWhoopAutoFillReadiness:
    """POST /api/v1/integrations/whoop/auto-fill-readiness"""

    def test_enable_auto_fill(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.set_auto_fill_readiness.return_value = {
            "auto_fill_readiness": True,
        }
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/auto-fill-readiness",
            json={"enabled": True},
        )
        assert response.status_code == 200

    def test_disable_auto_fill(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        mock_whoop_service.set_auto_fill_readiness.return_value = {
            "auto_fill_readiness": False,
        }
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/auto-fill-readiness",
            json={"enabled": False},
        )
        assert response.status_code == 200


# ============================================================================
# Disconnect
# ============================================================================


class TestWhoopDisconnect:
    """DELETE /api/v1/integrations/whoop"""

    def test_disconnect(self, authenticated_client, test_user, mock_whoop_service):
        mock_whoop_service.disconnect.return_value = None
        response = authenticated_client.delete("/api/v1/integrations/whoop")
        assert response.status_code == 200
        assert response.json()["disconnected"] is True


# ============================================================================
# Feature flag disabled
# ============================================================================


class TestWhoopFeatureFlagDisabled:
    """All endpoints return 404 when ENABLE_WHOOP_INTEGRATION=False."""

    @pytest.fixture(autouse=True)
    def disable_whoop(self, monkeypatch):
        monkeypatch.setenv("ENABLE_WHOOP_INTEGRATION", "false")
        from rivaflow.core.settings import settings

        monkeypatch.setattr(settings, "ENABLE_WHOOP_INTEGRATION", False)

    def test_authorize_returns_404(self, authenticated_client, test_user):
        response = authenticated_client.get("/api/v1/integrations/whoop/authorize")
        assert response.status_code == 404

    def test_status_returns_404(self, authenticated_client, test_user):
        response = authenticated_client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 404

    def test_sync_returns_404(self, authenticated_client, test_user):
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 404

    def test_disconnect_returns_404(self, authenticated_client, test_user):
        response = authenticated_client.delete("/api/v1/integrations/whoop")
        assert response.status_code == 404
