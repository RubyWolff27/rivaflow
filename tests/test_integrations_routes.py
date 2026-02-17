"""Integration tests for WHOOP integration routes."""

from unittest.mock import MagicMock

import pytest

from rivaflow.core.exceptions import ExternalServiceError, NotFoundError


@pytest.fixture(autouse=True)
def enable_whoop(monkeypatch):
    """Enable the WHOOP feature flag for all tests in this module."""
    monkeypatch.setenv("ENABLE_WHOOP_INTEGRATION", "true")
    from rivaflow.core.settings import settings

    monkeypatch.setattr(settings, "ENABLE_WHOOP_INTEGRATION", True)


@pytest.fixture()
def mock_whoop_service(monkeypatch):
    """Patch WhoopService so endpoints use a mock instance."""
    svc = MagicMock()
    monkeypatch.setattr(
        "rivaflow.api.routes.integrations.WhoopService",
        lambda: svc,
    )
    return svc


class TestWhoopStatus:
    """Tests for GET /api/v1/integrations/whoop/status."""

    def test_status_connected(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        """Test getting WHOOP status when connected."""
        mock_whoop_service.get_connection_status.return_value = {
            "connected": True,
            "whoop_user_id": "12345",
        }
        response = authenticated_client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True

    def test_status_disconnected(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        """Test getting WHOOP status when disconnected."""
        mock_whoop_service.get_connection_status.return_value = {
            "connected": False,
        }
        response = authenticated_client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False

    def test_status_requires_auth(self, client, temp_db):
        """Test WHOOP status endpoint requires authentication."""
        response = client.get("/api/v1/integrations/whoop/status")
        assert response.status_code == 401


class TestWhoopDisconnect:
    """Tests for DELETE /api/v1/integrations/whoop."""

    def test_disconnect(self, authenticated_client, test_user, mock_whoop_service):
        """Test disconnecting WHOOP integration."""
        response = authenticated_client.delete("/api/v1/integrations/whoop")
        assert response.status_code == 200
        data = response.json()
        assert data["disconnected"] is True
        mock_whoop_service.disconnect.assert_called_once_with(test_user["id"])

    def test_disconnect_requires_auth(self, client, temp_db):
        """Test WHOOP disconnect requires authentication."""
        response = client.delete("/api/v1/integrations/whoop")
        assert response.status_code == 401


class TestWhoopSync:
    """Tests for POST /api/v1/integrations/whoop/sync."""

    def test_sync_workouts(self, authenticated_client, test_user, mock_whoop_service):
        """Test triggering workout sync."""
        mock_whoop_service.sync_workouts.return_value = {
            "synced": 3,
            "new": 2,
        }
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 200

    def test_sync_with_days(self, authenticated_client, test_user, mock_whoop_service):
        """Test sync with custom days parameter."""
        mock_whoop_service.sync_workouts.return_value = {"synced": 0}
        response = authenticated_client.post("/api/v1/integrations/whoop/sync?days=30")
        assert response.status_code == 200

    def test_sync_not_connected(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        """Test sync returns 400 when WHOOP not connected."""
        mock_whoop_service.sync_workouts.side_effect = NotFoundError(
            "WHOOP not connected"
        )
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 400

    def test_sync_external_error(
        self, authenticated_client, test_user, mock_whoop_service
    ):
        """Test sync returns 502 on external service failure."""
        mock_whoop_service.sync_workouts.side_effect = ExternalServiceError(
            "WHOOP API down"
        )
        response = authenticated_client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 502

    def test_sync_requires_auth(self, client, temp_db):
        """Test WHOOP sync requires authentication."""
        response = client.post("/api/v1/integrations/whoop/sync")
        assert response.status_code == 401


class TestWhoopFeatureFlag:
    """Tests for WHOOP feature flag guard."""

    def test_endpoints_404_when_disabled(
        self, authenticated_client, test_user, monkeypatch
    ):
        """Test all WHOOP endpoints return 404 when feature is disabled."""
        from rivaflow.core.settings import settings

        monkeypatch.setattr(settings, "ENABLE_WHOOP_INTEGRATION", False)

        endpoints = [
            ("GET", "/api/v1/integrations/whoop/status"),
            ("GET", "/api/v1/integrations/whoop/authorize"),
            ("DELETE", "/api/v1/integrations/whoop"),
        ]
        for method, url in endpoints:
            response = getattr(authenticated_client, method.lower())(url)
            assert (
                response.status_code == 404
            ), f"{method} {url} should return 404 when WHOOP disabled"


class TestWhoopAutoCreate:
    """Tests for POST /api/v1/integrations/whoop/auto-create-sessions."""

    def test_set_auto_create(self, authenticated_client, test_user, mock_whoop_service):
        """Test toggling auto-create sessions."""
        mock_whoop_service.set_auto_create_sessions.return_value = {"enabled": True}
        response = authenticated_client.post(
            "/api/v1/integrations/whoop/auto-create-sessions",
            json={"enabled": True},
        )
        assert response.status_code == 200

    def test_set_auto_create_requires_auth(self, client, temp_db):
        """Test auto-create toggle requires auth."""
        response = client.post(
            "/api/v1/integrations/whoop/auto-create-sessions",
            json={"enabled": True},
        )
        assert response.status_code == 401
