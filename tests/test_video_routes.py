"""Integration tests for video endpoints."""


class TestListVideos:
    """List videos endpoint tests."""

    def test_list_requires_auth(self, client, temp_db):
        """Test GET /api/v1/videos/ requires auth."""
        response = client.get("/api/v1/videos/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Test list videos returns 200 with auth."""
        response = authenticated_client.get("/api/v1/videos/")
        assert response.status_code == 200

    def test_list_returns_paginated_structure(self, authenticated_client, test_user):
        """Test list videos returns paginated response."""
        response = authenticated_client.get("/api/v1/videos/")
        data = response.json()
        assert "videos" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["videos"], list)

    def test_list_with_pagination(self, authenticated_client, test_user):
        """Test list videos with custom limit and offset."""
        response = authenticated_client.get("/api/v1/videos/?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestGetVideo:
    """Get single video endpoint tests."""

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Test GET /api/v1/videos/999999 returns 404."""
        response = authenticated_client.get("/api/v1/videos/999999")
        assert response.status_code == 404

    def test_get_requires_auth(self, client, temp_db):
        """Test get video requires auth."""
        response = client.get("/api/v1/videos/1")
        assert response.status_code == 401


class TestDeleteVideo:
    """Delete video endpoint tests."""

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Test DELETE /api/v1/videos/999999 returns 404."""
        response = authenticated_client.delete("/api/v1/videos/999999")
        assert response.status_code == 404

    def test_delete_requires_auth(self, client, temp_db):
        """Test delete video requires auth."""
        response = client.delete("/api/v1/videos/1")
        assert response.status_code == 401


class TestCreateVideo:
    """Create video endpoint tests."""

    def test_create_requires_auth(self, client, temp_db):
        """Test POST /api/v1/videos/ requires auth."""
        response = client.post(
            "/api/v1/videos/",
            json={
                "url": "https://youtube.com/watch?v=test",
                "movement_id": 1,
            },
        )
        assert response.status_code == 401

    def test_create_without_movement_id_fails(self, authenticated_client, test_user):
        """Test creating a video without movement_id fails."""
        response = authenticated_client.post(
            "/api/v1/videos/",
            json={"url": "https://youtube.com/watch?v=test"},
        )
        assert response.status_code == 404
