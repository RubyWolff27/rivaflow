"""Integration tests for analytics endpoints."""

from datetime import date, timedelta


class TestPerformanceOverview:
    """Performance overview endpoint tests."""

    def test_overview_requires_auth(self, client, temp_db):
        """Test GET /api/v1/analytics/performance-overview requires auth."""
        response = client.get("/api/v1/analytics/performance-overview")
        assert response.status_code == 401

    def test_overview_returns_200(self, authenticated_client, test_user):
        """Test overview returns 200 with auth."""
        response = authenticated_client.get("/api/v1/analytics/performance-overview")
        assert response.status_code == 200

    def test_overview_with_date_range(self, authenticated_client, test_user):
        """Test overview with start_date and end_date params."""
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()
        response = authenticated_client.get(
            f"/api/v1/analytics/performance-overview?start_date={start}&end_date={end}"
        )
        assert response.status_code == 200

    def test_overview_invalid_date_range(self, authenticated_client, test_user):
        """Test overview rejects start_date after end_date."""
        response = authenticated_client.get(
            "/api/v1/analytics/performance-overview"
            "?start_date=2025-06-01&end_date=2025-01-01"
        )
        assert response.status_code == 400

    def test_overview_date_range_too_large(self, authenticated_client, test_user):
        """Test overview rejects date range exceeding 2 years."""
        response = authenticated_client.get(
            "/api/v1/analytics/performance-overview"
            "?start_date=2020-01-01&end_date=2025-01-01"
        )
        assert response.status_code == 400

    def test_overview_with_session_data(self, authenticated_client, session_factory):
        """Test overview returns data when sessions exist."""
        session_factory()
        response = authenticated_client.get("/api/v1/analytics/performance-overview")
        assert response.status_code == 200


class TestPartnerAnalytics:
    """Partner analytics endpoint tests."""

    def test_partners_requires_auth(self, client, temp_db):
        """Test partner analytics requires auth."""
        response = client.get("/api/v1/analytics/partners/stats")
        assert response.status_code == 401

    def test_partners_returns_200(self, authenticated_client, test_user):
        """Test partner analytics returns 200."""
        response = authenticated_client.get("/api/v1/analytics/partners/stats")
        assert response.status_code == 200


class TestReadinessTrends:
    """Readiness trends endpoint tests."""

    def test_readiness_trends_requires_auth(self, client, temp_db):
        """Test readiness trends requires auth."""
        response = client.get("/api/v1/analytics/readiness/trends")
        assert response.status_code == 401

    def test_readiness_trends_returns_200(self, authenticated_client, test_user):
        """Test readiness trends returns 200."""
        response = authenticated_client.get("/api/v1/analytics/readiness/trends")
        assert response.status_code == 200


class TestTechniqueAnalytics:
    """Technique analytics endpoint tests."""

    def test_technique_breakdown_requires_auth(self, client, temp_db):
        """Test technique analytics requires auth."""
        response = client.get("/api/v1/analytics/techniques/breakdown")
        assert response.status_code == 401

    def test_technique_breakdown_returns_200(self, authenticated_client, test_user):
        """Test technique analytics returns 200."""
        response = authenticated_client.get("/api/v1/analytics/techniques/breakdown")
        assert response.status_code == 200


class TestConsistencyAnalytics:
    """Consistency metrics endpoint tests."""

    def test_consistency_requires_auth(self, client, temp_db):
        """Test consistency metrics requires auth."""
        response = client.get("/api/v1/analytics/consistency/metrics")
        assert response.status_code == 401

    def test_consistency_returns_200(self, authenticated_client, test_user):
        """Test consistency metrics returns 200."""
        response = authenticated_client.get("/api/v1/analytics/consistency/metrics")
        assert response.status_code == 200


class TestMilestones:
    """Milestones endpoint tests."""

    def test_milestones_requires_auth(self, client, temp_db):
        """Test milestones requires auth."""
        response = client.get("/api/v1/analytics/milestones")
        assert response.status_code == 401

    def test_milestones_returns_200(self, authenticated_client, test_user):
        """Test milestones returns 200."""
        response = authenticated_client.get("/api/v1/analytics/milestones")
        assert response.status_code == 200
