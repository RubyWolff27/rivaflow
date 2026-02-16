"""Integration tests for glossary (movements) endpoints."""


class TestListMovements:
    """List movements endpoint tests."""

    def test_list_requires_auth(self, client, temp_db):
        """Test GET /api/v1/glossary/ requires auth."""
        response = client.get("/api/v1/glossary/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Test list movements returns 200 with auth."""
        response = authenticated_client.get("/api/v1/glossary/")
        assert response.status_code == 200

    def test_list_returns_paginated_structure(self, authenticated_client, test_user):
        """Test list movements returns paginated response."""
        response = authenticated_client.get("/api/v1/glossary/")
        data = response.json()
        assert "movements" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["movements"], list)

    def test_list_with_search(self, authenticated_client, test_user):
        """Test list movements with search filter."""
        response = authenticated_client.get("/api/v1/glossary/?search=armbar")
        assert response.status_code == 200
        data = response.json()
        assert "movements" in data

    def test_list_search_too_short(self, authenticated_client, test_user):
        """Test search with too-short query is rejected."""
        response = authenticated_client.get("/api/v1/glossary/?search=a")
        assert response.status_code == 422

    def test_list_with_category_filter(self, authenticated_client, test_user):
        """Test list movements with category filter."""
        response = authenticated_client.get("/api/v1/glossary/?category=submission")
        assert response.status_code == 200
        data = response.json()
        assert "movements" in data

    def test_list_with_pagination(self, authenticated_client, test_user):
        """Test list movements with limit and offset."""
        response = authenticated_client.get("/api/v1/glossary/?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0


class TestGetMovement:
    """Get single movement endpoint tests."""

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Test GET /api/v1/glossary/999999 returns 404."""
        response = authenticated_client.get("/api/v1/glossary/999999")
        assert response.status_code == 404

    def test_get_requires_auth(self, client, temp_db):
        """Test get movement requires auth."""
        response = client.get("/api/v1/glossary/1")
        assert response.status_code == 401


class TestGetCategories:
    """Categories endpoint tests."""

    def test_categories_requires_auth(self, client, temp_db):
        """Test categories requires auth."""
        response = client.get("/api/v1/glossary/categories")
        assert response.status_code == 401

    def test_categories_returns_200(self, authenticated_client, test_user):
        """Test categories returns 200."""
        response = authenticated_client.get("/api/v1/glossary/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)


class TestCreateCustomMovement:
    """Create custom movement endpoint tests."""

    def test_create_requires_auth(self, client, temp_db):
        """Test POST /api/v1/glossary/ requires auth."""
        response = client.post(
            "/api/v1/glossary/",
            json={"name": "Test Move", "category": "submission"},
        )
        assert response.status_code == 401

    def test_create_returns_movement(self, authenticated_client, test_user):
        """Test creating a custom movement returns created data."""
        response = authenticated_client.post(
            "/api/v1/glossary/",
            json={"name": "Custom Test Move", "category": "sweep"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Custom Test Move"
        assert data["category"] == "sweep"
