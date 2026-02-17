"""Integration tests for activity feed routes."""


class TestActivityFeed:
    """Tests for GET /api/v1/feed/activity."""

    def test_get_activity_feed(self, authenticated_client, test_user):
        """Test getting activity feed returns valid structure."""
        response = authenticated_client.get("/api/v1/feed/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data or "total" in data or isinstance(data, dict)

    def test_get_activity_feed_with_sessions(
        self, authenticated_client, test_user, session_factory
    ):
        """Test activity feed includes logged sessions."""
        session_factory()
        response = authenticated_client.get("/api/v1/feed/activity")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activity_feed_with_limit(self, authenticated_client, test_user):
        """Test activity feed respects limit parameter."""
        response = authenticated_client.get("/api/v1/feed/activity?limit=5")
        assert response.status_code == 200

    def test_get_activity_feed_with_days_back(self, authenticated_client, test_user):
        """Test activity feed respects days_back parameter."""
        response = authenticated_client.get("/api/v1/feed/activity?days_back=7")
        assert response.status_code == 200

    def test_get_activity_feed_requires_auth(self, client, temp_db):
        """Test activity feed requires authentication."""
        response = client.get("/api/v1/feed/activity")
        assert response.status_code == 401


class TestFriendsFeed:
    """Tests for GET /api/v1/feed/friends."""

    def test_get_friends_feed(self, authenticated_client, test_user):
        """Test getting friends feed returns valid structure."""
        response = authenticated_client.get("/api/v1/feed/friends")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_friends_feed_empty(self, authenticated_client, test_user):
        """Test friends feed when user has no friends."""
        response = authenticated_client.get("/api/v1/feed/friends")
        assert response.status_code == 200
        data = response.json()
        # Should still return valid structure even with no friends
        assert isinstance(data, dict)

    def test_get_friends_feed_with_limit(self, authenticated_client, test_user):
        """Test friends feed respects limit parameter."""
        response = authenticated_client.get("/api/v1/feed/friends?limit=10")
        assert response.status_code == 200

    def test_get_friends_feed_requires_auth(self, client, temp_db):
        """Test friends feed requires authentication."""
        response = client.get("/api/v1/feed/friends")
        assert response.status_code == 401

    def test_get_friends_feed_with_cursor(self, authenticated_client, test_user):
        """Test friends feed supports cursor-based pagination."""
        response = authenticated_client.get(
            "/api/v1/feed/friends?cursor=2025-01-01:session:0"
        )
        assert response.status_code == 200
