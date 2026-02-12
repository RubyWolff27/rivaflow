"""Integration tests for notification routes."""


class TestNotificationCounts:
    """Notification count tests."""

    def test_get_counts(self, authenticated_client, test_user):
        """Test getting notification counts."""
        response = authenticated_client.get("/api/v1/notifications/counts")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data

    def test_counts_requires_auth(self, client, temp_db):
        """Test that notification counts require auth."""
        response = client.get("/api/v1/notifications/counts")
        assert response.status_code == 401


class TestListNotifications:
    """Notification listing tests."""

    def test_list_notifications(self, authenticated_client, test_user):
        """Test listing notifications."""
        response = authenticated_client.get("/api/v1/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "count" in data

    def test_list_with_limit(self, authenticated_client, test_user):
        """Test listing notifications with limit parameter."""
        response = authenticated_client.get(
            "/api/v1/notifications/", params={"limit": 5}
        )
        assert response.status_code == 200

    def test_list_unread_only(self, authenticated_client, test_user):
        """Test listing only unread notifications."""
        response = authenticated_client.get(
            "/api/v1/notifications/", params={"unread_only": True}
        )
        assert response.status_code == 200


class TestMarkRead:
    """Mark-as-read tests."""

    def test_mark_all_read(self, authenticated_client, test_user):
        """Test marking all notifications as read."""
        response = authenticated_client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_mark_feed_read(self, authenticated_client, test_user):
        """Test marking feed notifications as read."""
        response = authenticated_client.post("/api/v1/notifications/feed/read")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_mark_follows_read(self, authenticated_client, test_user):
        """Test marking follow notifications as read."""
        response = authenticated_client.post("/api/v1/notifications/follows/read")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_mark_single_read(self, authenticated_client, test_user):
        """Test marking a single notification as read (nonexistent ID)."""
        response = authenticated_client.post("/api/v1/notifications/1/read")
        assert response.status_code == 200


class TestDeleteNotification:
    """Notification deletion tests."""

    def test_delete_nonexistent(self, authenticated_client, test_user):
        """Test deleting a nonexistent notification."""
        response = authenticated_client.delete("/api/v1/notifications/99999")
        assert response.status_code in (200, 204, 404)
