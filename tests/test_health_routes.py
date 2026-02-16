"""Integration tests for health check endpoints."""


class TestHealthCheck:
    """Main health check endpoint tests."""

    def test_health_returns_200(self, client):
        """Test GET /health returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, client):
        """Test health response includes status healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_includes_database(self, client):
        """Test health response includes database check."""
        response = client.get("/health")
        data = response.json()
        assert "database" in data
        assert data["database"] == "connected"

    def test_health_includes_commit(self, client):
        """Test health response includes commit field."""
        response = client.get("/health")
        data = response.json()
        assert "commit" in data

    def test_health_includes_service_name(self, client):
        """Test health response includes service name."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "rivaflow-api"

    def test_health_includes_version(self, client):
        """Test health response includes version field."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data


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
