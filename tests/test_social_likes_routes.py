"""Integration tests for social like/unlike routes (/api/v1/social/)."""

from datetime import timedelta

from rivaflow.core.auth import create_access_token


class TestLikeAuth:
    """Authentication tests for like endpoints."""

    def test_like_requires_auth(self, client, temp_db):
        """Unauthenticated POST /like returns 401."""
        response = client.post(
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": 1},
        )
        assert response.status_code == 401

    def test_unlike_requires_auth(self, client, temp_db):
        """Unauthenticated DELETE /like returns 401."""
        response = client.request(
            "DELETE",
            "/api/v1/social/like",
            json={"activity_type": "session", "activity_id": 1},
        )
        assert response.status_code == 401

    def test_get_likes_requires_auth(self, client, temp_db):
        """Unauthenticated GET /likes/{type}/{id} returns 401."""
        response = client.get("/api/v1/social/likes/session/1")
        assert response.status_code == 401


class TestLikeActivity:
    """Tests for POST /api/v1/social/like."""

    def test_like_public_session(
        self, client, test_user, auth_headers, session_factory
    ):
        """Like a public session succeeds."""
        session_id = session_factory(visibility_level="public")
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["activity_type"] == "session"
        assert data["activity_id"] == session_id

    def test_like_invalid_activity_type(self, client, test_user, auth_headers):
        """Like with invalid activity_type gets 422."""
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "workout",
                "activity_id": 1,
            },
        )
        assert response.status_code == 422

    def test_like_nonexistent_session(self, client, test_user, auth_headers):
        """Like a non-existent activity returns 400."""
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": 999999,
            },
        )
        assert response.status_code == 400

    def test_like_private_session_fails(
        self, client, test_user, auth_headers, session_factory
    ):
        """Cannot like a private session (400)."""
        session_id = session_factory(visibility_level="private")
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert response.status_code == 400

    def test_like_already_liked_fails(
        self, client, test_user, auth_headers, session_factory
    ):
        """Liking the same activity twice fails (400)."""
        session_id = session_factory(visibility_level="public")
        client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert response.status_code == 400

    def test_two_users_can_like_same_session(
        self,
        client,
        test_user,
        test_user2,
        auth_headers,
        session_factory,
    ):
        """Two different users can like the same session."""
        session_id = session_factory(visibility_level="public")

        # test_user likes
        resp1 = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert resp1.status_code == 200

        # test_user2 likes
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        headers2 = {"Authorization": f"Bearer {token2}"}
        resp2 = client.post(
            "/api/v1/social/like",
            headers=headers2,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert resp2.status_code == 200

    def test_like_missing_fields_returns_422(self, client, test_user, auth_headers):
        """POST /like with missing required fields returns 422."""
        response = client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={"activity_type": "session"},
        )
        assert response.status_code == 422


class TestGetLikes:
    """Tests for GET /api/v1/social/likes/{activity_type}/{activity_id}."""

    def test_get_likes_count(self, client, test_user, auth_headers, session_factory):
        """After liking, count is at least 1."""
        session_id = session_factory(visibility_level="public")
        client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )

        response = client.get(
            f"/api/v1/social/likes/session/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "likes" in data
        assert "count" in data
        assert data["count"] >= 1
        assert isinstance(data["likes"], list)

    def test_get_likes_empty(self, client, test_user, auth_headers, session_factory):
        """Session with no likes returns count 0."""
        session_id = session_factory(visibility_level="public")
        response = client.get(
            f"/api/v1/social/likes/session/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["likes"] == []
        assert data["count"] == 0

    def test_get_likes_invalid_activity_type(self, client, test_user, auth_headers):
        """GET likes with invalid activity_type returns 422."""
        response = client.get(
            "/api/v1/social/likes/bogus/1",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_get_likes_reflects_multiple_users(
        self,
        client,
        test_user,
        test_user2,
        auth_headers,
        session_factory,
    ):
        """Likes from multiple users appear in the list."""
        session_id = session_factory(visibility_level="public")

        # test_user likes
        client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )

        # test_user2 likes
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        headers2 = {"Authorization": f"Bearer {token2}"}
        client.post(
            "/api/v1/social/like",
            headers=headers2,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )

        response = client.get(
            f"/api/v1/social/likes/session/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2


class TestUnlikeActivity:
    """Tests for DELETE /api/v1/social/like."""

    def test_unlike_returns_204(self, client, test_user, auth_headers, session_factory):
        """Unlike a previously liked session returns 204."""
        session_id = session_factory(visibility_level="public")
        client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )

        response = client.request(
            "DELETE",
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        assert response.status_code == 204

    def test_unlike_removes_from_count(
        self, client, test_user, auth_headers, session_factory
    ):
        """After unliking, count drops back to 0."""
        session_id = session_factory(visibility_level="public")
        client.post(
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        client.request(
            "DELETE",
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )

        response = client.get(
            f"/api/v1/social/likes/session/{session_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_unlike_not_liked_returns_false(
        self, client, test_user, auth_headers, session_factory
    ):
        """Unlike something never liked returns {unliked: false}."""
        session_id = session_factory(visibility_level="public")
        response = client.request(
            "DELETE",
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "session",
                "activity_id": session_id,
            },
        )
        # Route returns {unliked: false} when not previously liked
        assert response.status_code == 200
        data = response.json()
        assert data["unliked"] is False

    def test_unlike_invalid_activity_type(self, client, test_user, auth_headers):
        """DELETE /like with invalid activity_type returns 422."""
        response = client.request(
            "DELETE",
            "/api/v1/social/like",
            headers=auth_headers,
            json={
                "activity_type": "workout",
                "activity_id": 1,
            },
        )
        assert response.status_code == 422
