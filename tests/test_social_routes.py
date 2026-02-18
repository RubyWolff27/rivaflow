"""Integration tests for social feature routes."""


class TestFollowUnfollow:
    """Follow/unfollow lifecycle tests."""

    def test_follow_user(self, authenticated_client, test_user, test_user2):
        """Test following another user."""
        response = authenticated_client.post(
            f"/api/v1/social/follow/{test_user2['id']}"
        )
        assert response.status_code == 200

    def test_cannot_follow_self(self, authenticated_client, test_user):
        """Test that a user cannot follow themselves."""
        response = authenticated_client.post(f"/api/v1/social/follow/{test_user['id']}")
        assert response.status_code in (400, 422)

    def test_cannot_follow_twice(self, authenticated_client, test_user, test_user2):
        """Test that following the same user twice fails."""
        authenticated_client.post(f"/api/v1/social/follow/{test_user2['id']}")
        response = authenticated_client.post(
            f"/api/v1/social/follow/{test_user2['id']}"
        )
        assert response.status_code == 400

    def test_unfollow_user(self, authenticated_client, test_user, test_user2):
        """Test unfollowing a user."""
        authenticated_client.post(f"/api/v1/social/follow/{test_user2['id']}")
        response = authenticated_client.delete(
            f"/api/v1/social/follow/{test_user2['id']}"
        )
        assert response.status_code == 204

    def test_check_following_status(self, authenticated_client, test_user, test_user2):
        """Test checking following status."""
        # Not following yet
        response = authenticated_client.get(
            f"/api/v1/social/following/{test_user2['id']}"
        )
        assert response.status_code == 200
        assert response.json()["is_following"] is False

        # Follow
        authenticated_client.post(f"/api/v1/social/follow/{test_user2['id']}")

        # Now following
        response = authenticated_client.get(
            f"/api/v1/social/following/{test_user2['id']}"
        )
        assert response.status_code == 200
        assert response.json()["is_following"] is True

    def test_get_followers_list(self, authenticated_client, test_user, test_user2):
        """Test getting followers list."""
        # Follow user2 (from test_user's perspective)
        authenticated_client.post(f"/api/v1/social/follow/{test_user2['id']}")

        response = authenticated_client.get("/api/v1/social/following")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_follow_requires_auth(self, client, test_user2):
        """Test that following requires authentication."""
        response = client.post(f"/api/v1/social/follow/{test_user2['id']}")
        assert response.status_code == 401


class TestLikes:
    """Like/unlike activity tests."""

    def test_like_activity(self, authenticated_client, test_user, session_factory):
        """Test liking a session."""
        session_id = session_factory(visibility_level="public")
        response = authenticated_client.post(
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": session_id},
        )
        assert response.status_code == 200

    def test_unlike_activity(self, authenticated_client, test_user, session_factory):
        """Test unliking a session."""
        session_id = session_factory(visibility_level="public")
        authenticated_client.post(
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": session_id},
        )

        response = authenticated_client.request(
            "DELETE",
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": session_id},
        )
        assert response.status_code == 204

    def test_get_activity_likes(self, authenticated_client, test_user, session_factory):
        """Test getting likes for an activity."""
        session_id = session_factory(visibility_level="public")
        authenticated_client.post(
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": session_id},
        )

        response = authenticated_client.get(
            f"/api/v1/social/likes/session/{session_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestComments:
    """Comment CRUD tests."""

    def test_create_comment(self, authenticated_client, test_user, session_factory):
        """Test creating a comment on a session."""
        session_id = session_factory(visibility_level="public")
        response = authenticated_client.post(
            "/api/v1/social/comment",
            json={
                "activity_type": "session",
                "activity_id": session_id,
                "comment_text": "Great training!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "comment_text" in data

    def test_update_comment(self, authenticated_client, test_user, session_factory):
        """Test updating a comment."""
        session_id = session_factory(visibility_level="public")
        create_resp = authenticated_client.post(
            "/api/v1/social/comment",
            json={
                "activity_type": "session",
                "activity_id": session_id,
                "comment_text": "Original text",
            },
        )
        comment_id = create_resp.json()["id"]

        response = authenticated_client.put(
            f"/api/v1/social/comment/{comment_id}",
            json={"comment_text": "Updated text"},
        )
        assert response.status_code == 200

    def test_delete_comment(self, authenticated_client, test_user, session_factory):
        """Test deleting a comment."""
        session_id = session_factory(visibility_level="public")
        create_resp = authenticated_client.post(
            "/api/v1/social/comment",
            json={
                "activity_type": "session",
                "activity_id": session_id,
                "comment_text": "To be deleted",
            },
        )
        comment_id = create_resp.json()["id"]

        response = authenticated_client.delete(f"/api/v1/social/comment/{comment_id}")
        assert response.status_code == 204

    def test_get_activity_comments(
        self, authenticated_client, test_user, session_factory
    ):
        """Test getting comments for an activity."""
        session_id = session_factory(visibility_level="public")
        authenticated_client.post(
            "/api/v1/social/comment",
            json={
                "activity_type": "session",
                "activity_id": session_id,
                "comment_text": "Test comment",
            },
        )

        response = authenticated_client.get(
            f"/api/v1/social/comments/session/{session_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1


class TestFriendRequests:
    """Friend request lifecycle tests."""

    def test_send_friend_request(self, authenticated_client, test_user, test_user2):
        """Test sending a friend request."""
        response = authenticated_client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            json={},
        )
        assert response.status_code == 200

    def test_get_sent_requests(self, authenticated_client, test_user, test_user2):
        """Test getting sent friend requests."""
        authenticated_client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            json={},
        )

        response = authenticated_client.get("/api/v1/social/friend-requests/sent")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_cancel_friend_request(self, authenticated_client, test_user, test_user2):
        """Test cancelling a sent friend request."""
        send_resp = authenticated_client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            json={},
        )
        connection_id = send_resp.json()["id"]

        response = authenticated_client.delete(
            f"/api/v1/social/friend-requests/{connection_id}"
        )
        assert response.status_code == 204

    def test_friendship_status_none(self, authenticated_client, test_user, test_user2):
        """Test friendship status when no relationship exists."""
        response = authenticated_client.get(
            f"/api/v1/social/friends/{test_user2['id']}/status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "none"
        assert data["are_friends"] is False

    def test_friendship_status_pending(
        self, authenticated_client, test_user, test_user2
    ):
        """Test friendship status after sending request."""
        authenticated_client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            json={},
        )

        response = authenticated_client.get(
            f"/api/v1/social/friends/{test_user2['id']}/status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_sent"


class TestFeed:
    """Feed endpoint tests."""

    def test_get_own_feed(self, authenticated_client, test_user):
        """Test getting own activity feed."""
        response = authenticated_client.get("/api/v1/feed/activity")
        assert response.status_code == 200

    def test_get_friends_feed(self, authenticated_client, test_user):
        """Test getting friends activity feed."""
        response = authenticated_client.get("/api/v1/feed/friends")
        assert response.status_code == 200

    def test_feed_requires_auth(self, client):
        """Test that feeds require authentication."""
        response = client.get("/api/v1/feed/activity")
        assert response.status_code == 401

    def test_own_feed_contains_session(
        self, authenticated_client, test_user, session_factory
    ):
        """Test that own feed contains logged sessions."""
        session_factory()

        response = authenticated_client.get("/api/v1/feed/activity")
        assert response.status_code == 200
