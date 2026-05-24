"""Integration tests for health check endpoints.

Updated 2026-05-24 — /health reduced to minimal status payload to prevent
reconnaissance disclosure; /health/detailed added as auth-gated endpoint.
"""

import os
from unittest.mock import patch


class TestHealthCheck:
    """Public minimal health check endpoint tests."""

    def test_health_returns_200(self, client):
        """Test GET /health returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, client):
        """Test health response includes status healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_does_not_disclose_commit(self, client):
        """Public /health must NOT expose commit hash (reconnaissance surface)."""
        response = client.get("/health")
        data = response.json()
        assert "commit" not in data, "Public /health must not expose commit SHA"

    def test_health_does_not_disclose_version(self, client):
        """Public /health must NOT expose version (reconnaissance surface)."""
        response = client.get("/health")
        data = response.json()
        assert "version" not in data, "Public /health must not expose app version"

    def test_health_does_not_disclose_email_config(self, client):
        """Public /health must NOT expose email provider (recon surface)."""
        response = client.get("/health")
        data = response.json()
        assert "email" not in data, "Public /health must not expose email config"

    def test_health_does_not_disclose_database_label(self, client):
        """Public /health must NOT expose database connection label."""
        response = client.get("/health")
        data = response.json()
        assert "database" not in data, "Public /health must not expose DB label"

    def test_health_does_not_disclose_service_name(self, client):
        """Public /health must NOT expose service identifier."""
        response = client.get("/health")
        data = response.json()
        assert "service" not in data, "Public /health must not expose service name"


class TestDetailedHealthCheck:
    """Auth-gated detailed health endpoint tests.

    Returns 404 when token is missing/wrong so endpoint existence is concealed.
    """

    def test_detailed_health_404_without_token(self, client):
        """No X-Admin-Token → 404 (not 401/403; conceals existence)."""
        response = client.get("/health/detailed")
        assert response.status_code == 404

    def test_detailed_health_404_with_wrong_token(self, client):
        """Wrong X-Admin-Token → 404."""
        with patch.dict(os.environ, {"HEALTH_DETAILED_TOKEN": "expected-secret"}):
            response = client.get(
                "/health/detailed", headers={"X-Admin-Token": "wrong-secret"}
            )
            assert response.status_code == 404

    def test_detailed_health_404_when_env_var_unset(self, client):
        """Unset HEALTH_DETAILED_TOKEN env var → 404 even with any token (fail closed)."""
        # Ensure the env var is genuinely unset for this test
        if "HEALTH_DETAILED_TOKEN" in os.environ:
            del os.environ["HEALTH_DETAILED_TOKEN"]
        response = client.get(
            "/health/detailed", headers={"X-Admin-Token": "any-value"}
        )
        assert response.status_code == 404

    def test_detailed_health_200_with_correct_token(self, client):
        """Correct X-Admin-Token → 200 + full payload."""
        with patch.dict(os.environ, {"HEALTH_DETAILED_TOKEN": "expected-secret"}):
            response = client.get(
                "/health/detailed", headers={"X-Admin-Token": "expected-secret"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "rivaflow-api"
            assert "version" in data
            assert "commit" in data
            assert "email" in data
            assert "database" in data


class TestReadinessCheck:
    """Readiness probe endpoint tests."""

    def test_readiness_returns_200(self, client):
        """Test GET /health/ready returns 200."""
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_readiness_status_ready(self, client):
        """Test readiness response has status ready."""
        response = client.get("/health/ready")
        data = response.json()
        assert data["status"] == "ready"

    def test_readiness_includes_service(self, client):
        """Test readiness response includes service name."""
        response = client.get("/health/ready")
        data = response.json()
        assert data["service"] == "rivaflow-api"


class TestLivenessCheck:
    """Liveness probe endpoint tests."""

    def test_liveness_returns_200(self, client):
        """Test GET /health/live returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_liveness_status_alive(self, client):
        """Test liveness response has status alive."""
        response = client.get("/health/live")
        data = response.json()
        assert data["status"] == "alive"

    def test_liveness_includes_service(self, client):
        """Test liveness response includes service name."""
        response = client.get("/health/live")
        data = response.json()
        assert data["service"] == "rivaflow-api"
