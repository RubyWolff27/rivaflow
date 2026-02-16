"""Integration tests for technique endpoints."""


class TestListTechniques:
    """List techniques endpoint tests."""

    def test_list_requires_auth(self, client, temp_db):
        """Test GET /api/v1/techniques/ requires auth."""
        response = client.get("/api/v1/techniques/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Test list techniques returns 200 with auth."""
        response = authenticated_client.get("/api/v1/techniques/")
        assert response.status_code == 200

    def test_list_returns_paginated_structure(self, authenticated_client, test_user):
        """Test list techniques returns paginated response."""
        response = authenticated_client.get("/api/v1/techniques/")
        data = response.json()
        assert "techniques" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["techniques"], list)

    def test_list_with_pagination(self, authenticated_client, test_user):
        """Test list techniques with custom limit and offset."""
        response = authenticated_client.get("/api/v1/techniques/?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestCreateTechnique:
    """Create technique endpoint tests."""

    def test_create_requires_auth(self, client, temp_db):
        """Test POST /api/v1/techniques/ requires auth."""
        response = client.post(
            "/api/v1/techniques/",
            json={"name": "Armbar", "category": "submission"},
        )
        assert response.status_code == 401

    def test_create_returns_technique(self, authenticated_client, test_user):
        """Test creating a technique returns created data."""
        response = authenticated_client.post(
            "/api/v1/techniques/",
            json={"name": "Test Armbar", "category": "submission"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Armbar"
        assert data["category"] == "submission"

    def test_create_with_default_category(self, authenticated_client, test_user):
        """Test creating a technique with default category."""
        response = authenticated_client.post(
            "/api/v1/techniques/",
            json={"name": "Test Triangle"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "submission"

    def test_create_empty_name_fails(self, authenticated_client, test_user):
        """Test creating a technique with empty name fails validation."""
        response = authenticated_client.post(
            "/api/v1/techniques/",
            json={"name": "", "category": "submission"},
        )
        assert response.status_code == 422


class TestGetTechnique:
    """Get single technique endpoint tests."""

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Test GET /api/v1/techniques/999999 returns 404."""
        response = authenticated_client.get("/api/v1/techniques/999999")
        assert response.status_code == 404

    def test_get_requires_auth(self, client, temp_db):
        """Test get technique requires auth."""
        response = client.get("/api/v1/techniques/1")
        assert response.status_code == 401


class TestSearchTechniques:
    """Search techniques endpoint tests."""

    def test_search_requires_auth(self, client, temp_db):
        """Test search techniques requires auth."""
        response = client.get("/api/v1/techniques/search?q=armbar")
        assert response.status_code == 401

    def test_search_returns_200(self, authenticated_client, test_user):
        """Test search returns 200."""
        response = authenticated_client.get("/api/v1/techniques/search?q=armbar")
        assert response.status_code == 200

    def test_search_query_too_short(self, authenticated_client, test_user):
        """Test search rejects query shorter than 2 chars."""
        response = authenticated_client.get("/api/v1/techniques/search?q=a")
        assert response.status_code == 422


class TestStaleTechniques:
    """Stale techniques endpoint tests."""

    def test_stale_requires_auth(self, client, temp_db):
        """Test stale techniques requires auth."""
        response = client.get("/api/v1/techniques/stale")
        assert response.status_code == 401

    def test_stale_returns_200(self, authenticated_client, test_user):
        """Test stale techniques returns 200."""
        response = authenticated_client.get("/api/v1/techniques/stale")
        assert response.status_code == 200
