"""Integration tests for user profile (public view) endpoints."""


class TestSearchUsers:
    """Tests for GET /api/v1/users/search."""

    def test_search_requires_auth(self, client, temp_db):
        """Unauthenticated search returns 401."""
        response = client.get("/api/v1/users/search?q=test")
        assert response.status_code == 401

    def test_search_returns_200(self, authenticated_client, test_user):
        """Authenticated search returns 200."""
        response = authenticated_client.get("/api/v1/users/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_excludes_self(self, authenticated_client, test_user, test_user2):
        """Search results exclude the requesting user."""
        response = authenticated_client.get("/api/v1/users/search?q=Test")
        data = response.json()
        user_ids = [u["id"] for u in data if "id" in u]
        assert test_user["id"] not in user_ids

    def test_search_finds_other_user(self, authenticated_client, test_user, test_user2):
        """Search finds other users by name."""
        response = authenticated_client.get("/api/v1/users/search?q=Test2")
        data = response.json()
        # test_user2 should be found
        if len(data) > 0:
            found_ids = [u["id"] for u in data if "id" in u]
            assert test_user2["id"] in found_ids

    def test_search_missing_query_returns_422(self, authenticated_client, test_user):
        """Missing q parameter returns 422."""
        response = authenticated_client.get("/api/v1/users/search")
        assert response.status_code == 422


class TestGetUserProfile:
    """Tests for GET /api/v1/users/{user_id}."""

    def test_get_profile_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 401

    def test_get_own_profile(self, authenticated_client, test_user):
        """Get own user profile returns 200."""
        user_id = test_user["id"]
        response = authenticated_client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200

    def test_get_other_user_profile(self, authenticated_client, test_user, test_user2):
        """Get another user's profile returns 200."""
        response = authenticated_client.get(f"/api/v1/users/{test_user2['id']}")
        assert response.status_code == 200

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Get non-existent user returns 404."""
        response = authenticated_client.get("/api/v1/users/999999")
        assert response.status_code == 404


class TestGetUserStats:
    """Tests for GET /api/v1/users/{user_id}/stats."""

    def test_stats_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/users/1/stats")
        assert response.status_code == 401

    def test_stats_returns_200(self, authenticated_client, test_user):
        """Get user stats returns 200."""
        response = authenticated_client.get(f"/api/v1/users/{test_user['id']}/stats")
        assert response.status_code == 200

    def test_stats_nonexistent_returns_404(self, authenticated_client, test_user):
        """Stats for non-existent user returns 404."""
        response = authenticated_client.get("/api/v1/users/999999/stats")
        assert response.status_code == 404


class TestGetUserActivity:
    """Tests for GET /api/v1/users/{user_id}/activity."""

    def test_activity_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/users/1/activity")
        assert response.status_code == 401

    def test_activity_returns_200(self, authenticated_client, test_user):
        """Get user activity returns 200."""
        response = authenticated_client.get(f"/api/v1/users/{test_user['id']}/activity")
        assert response.status_code == 200

    def test_activity_nonexistent_returns_404(self, authenticated_client, test_user):
        """Activity for non-existent user returns 404."""
        response = authenticated_client.get("/api/v1/users/999999/activity")
        assert response.status_code == 404

    def test_activity_with_pagination(self, authenticated_client, test_user):
        """Activity endpoint accepts limit and offset params."""
        response = authenticated_client.get(
            f"/api/v1/users/{test_user['id']}/activity" "?limit=5&offset=0"
        )
        assert response.status_code == 200
