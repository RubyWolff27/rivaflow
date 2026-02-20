"""Integration tests for social connection routes (/api/v1/social/).

Covers friend requests, friends list, unfriend, friend suggestions,
and friendship status checks.
"""

from datetime import timedelta

from rivaflow.core.auth import create_access_token

# ── Helpers ──────────────────────────────────────────────────────


def _headers_for(user: dict) -> dict:
    """Build Authorization headers for a given user dict."""
    token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


def _send_request(client, from_headers, to_user_id):
    """Send a friend request and return the response JSON."""
    resp = client.post(
        f"/api/v1/social/friend-requests/{to_user_id}",
        headers=from_headers,
        json={},
    )
    assert resp.status_code == 200
    return resp.json()


# ── Authentication ───────────────────────────────────────────────


class TestConnectionAuth:
    """All connection endpoints require authentication."""

    def test_send_friend_request_requires_auth(self, client, test_user2):
        """Unauthenticated POST /friend-requests/{id} returns 401."""
        response = client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            json={},
        )
        assert response.status_code == 401

    def test_get_received_requests_requires_auth(self, client, temp_db):
        """Unauthenticated GET /friend-requests/received returns 401."""
        response = client.get("/api/v1/social/friend-requests/received")
        assert response.status_code == 401

    def test_get_sent_requests_requires_auth(self, client, temp_db):
        """Unauthenticated GET /friend-requests/sent returns 401."""
        response = client.get("/api/v1/social/friend-requests/sent")
        assert response.status_code == 401

    def test_get_friends_requires_auth(self, client, temp_db):
        """Unauthenticated GET /friends returns 401."""
        response = client.get("/api/v1/social/friends")
        assert response.status_code == 401

    def test_friendship_status_requires_auth(self, client, test_user2):
        """Unauthenticated GET /friends/{id}/status returns 401."""
        response = client.get(f"/api/v1/social/friends/{test_user2['id']}/status")
        assert response.status_code == 401

    def test_friend_suggestions_requires_auth(self, client, temp_db):
        """Unauthenticated GET /friend-suggestions returns 401."""
        response = client.get("/api/v1/social/friend-suggestions")
        assert response.status_code == 401


# ── Friend Requests ──────────────────────────────────────────────


class TestSendFriendRequest:
    """Tests for POST /api/v1/social/friend-requests/{user_id}."""

    def test_send_friend_request(self, client, test_user, test_user2, auth_headers):
        """Send a friend request returns pending connection."""
        response = client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["requester_id"] == test_user["id"]
        assert data["recipient_id"] == test_user2["id"]

    def test_send_request_with_message(
        self, client, test_user, test_user2, auth_headers
    ):
        """Friend request can include connection_source and message."""
        response = client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            headers=auth_headers,
            json={
                "connection_source": "gym",
                "request_message": "We train at the same gym!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["connection_source"] == "gym"
        assert data["request_message"] == "We train at the same gym!"

    def test_cannot_send_request_to_self(self, client, test_user, auth_headers):
        """Sending a friend request to yourself fails (400)."""
        response = client.post(
            f"/api/v1/social/friend-requests/{test_user['id']}",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400

    def test_cannot_send_duplicate_request(
        self, client, test_user, test_user2, auth_headers
    ):
        """Sending a second friend request while one is pending fails."""
        client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            headers=auth_headers,
            json={},
        )
        response = client.post(
            f"/api/v1/social/friend-requests/{test_user2['id']}",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400


class TestGetRequests:
    """Tests for GET friend-requests/received and friend-requests/sent."""

    def test_get_sent_requests(self, client, test_user, test_user2, auth_headers):
        """Sent requests list includes the request just sent."""
        _send_request(client, auth_headers, test_user2["id"])

        response = client.get(
            "/api/v1/social/friend-requests/sent",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert "requests" in data

    def test_get_received_requests(self, client, test_user, test_user2, auth_headers):
        """Received requests list shows request from the other user."""
        _send_request(client, auth_headers, test_user2["id"])

        headers2 = _headers_for(test_user2)
        response = client.get(
            "/api/v1/social/friend-requests/received",
            headers=headers2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        ids = [r["requester_id"] for r in data["requests"]]
        assert test_user["id"] in ids


# ── Accept / Decline / Cancel ────────────────────────────────────


class TestAcceptFriendRequest:
    """Tests for POST /api/v1/social/friend-requests/{id}/accept."""

    def test_accept_friend_request(self, client, test_user, test_user2, auth_headers):
        """Recipient can accept a pending friend request."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        connection_id = connection["id"]

        headers2 = _headers_for(test_user2)
        response = client.post(
            f"/api/v1/social/friend-requests/{connection_id}/accept",
            headers=headers2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

    def test_requester_cannot_accept_own_request(
        self, client, test_user, test_user2, auth_headers
    ):
        """The requester cannot accept their own outgoing request."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        connection_id = connection["id"]

        # test_user (requester) tries to accept
        response = client.post(
            f"/api/v1/social/friend-requests/{connection_id}/accept",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestDeclineFriendRequest:
    """Tests for POST /api/v1/social/friend-requests/{id}/decline."""

    def test_decline_friend_request(self, client, test_user, test_user2, auth_headers):
        """Recipient can decline a pending friend request."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        connection_id = connection["id"]

        headers2 = _headers_for(test_user2)
        response = client.post(
            f"/api/v1/social/friend-requests/{connection_id}/decline",
            headers=headers2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "declined"


class TestCancelFriendRequest:
    """Tests for DELETE /api/v1/social/friend-requests/{id}."""

    def test_cancel_sent_request(self, client, test_user, test_user2, auth_headers):
        """Requester can cancel their own pending request (204)."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        connection_id = connection["id"]

        response = client.delete(
            f"/api/v1/social/friend-requests/{connection_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_recipient_cannot_cancel_request(
        self, client, test_user, test_user2, auth_headers
    ):
        """Recipient cannot cancel the requester's request (404)."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        connection_id = connection["id"]

        headers2 = _headers_for(test_user2)
        response = client.delete(
            f"/api/v1/social/friend-requests/{connection_id}",
            headers=headers2,
        )
        assert response.status_code == 404

    def test_cancel_nonexistent_request(self, client, test_user, auth_headers):
        """Cancel a non-existent request returns 404."""
        response = client.delete(
            "/api/v1/social/friend-requests/999999",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ── Friends List & Unfriend ──────────────────────────────────────


class TestFriendsList:
    """Tests for GET /api/v1/social/friends."""

    def test_friends_list_empty_initially(self, client, test_user, auth_headers):
        """New user has no friends."""
        response = client.get("/api/v1/social/friends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["friends"] == []
        assert data["count"] == 0

    def test_friends_list_after_accept(
        self, client, test_user, test_user2, auth_headers
    ):
        """After accepting a request, both users see each other."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        headers2 = _headers_for(test_user2)
        client.post(
            f"/api/v1/social/friend-requests/{connection['id']}/accept",
            headers=headers2,
        )

        # test_user sees test_user2 as friend
        resp1 = client.get("/api/v1/social/friends", headers=auth_headers)
        assert resp1.status_code == 200
        assert resp1.json()["count"] >= 1

        # test_user2 sees test_user as friend
        resp2 = client.get("/api/v1/social/friends", headers=headers2)
        assert resp2.status_code == 200
        assert resp2.json()["count"] >= 1


class TestUnfriend:
    """Tests for DELETE /api/v1/social/friends/{user_id}."""

    def test_unfriend_returns_204(self, client, test_user, test_user2, auth_headers):
        """Unfriending an accepted friend returns 204."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        headers2 = _headers_for(test_user2)
        client.post(
            f"/api/v1/social/friend-requests/{connection['id']}/accept",
            headers=headers2,
        )

        response = client.delete(
            f"/api/v1/social/friends/{test_user2['id']}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_unfriend_removes_from_list(
        self, client, test_user, test_user2, auth_headers
    ):
        """After unfriending, friends list is empty again."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        headers2 = _headers_for(test_user2)
        client.post(
            f"/api/v1/social/friend-requests/{connection['id']}/accept",
            headers=headers2,
        )
        client.delete(
            f"/api/v1/social/friends/{test_user2['id']}",
            headers=auth_headers,
        )

        response = client.get("/api/v1/social/friends", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["count"] == 0

    def test_unfriend_nonexistent_returns_404(self, client, test_user, auth_headers):
        """Unfriending someone you are not friends with returns 404."""
        response = client.delete(
            "/api/v1/social/friends/999999",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ── Friendship Status ────────────────────────────────────────────


class TestFriendshipStatus:
    """Tests for GET /api/v1/social/friends/{user_id}/status."""

    def test_status_none(self, client, test_user, test_user2, auth_headers):
        """No relationship returns status 'none'."""
        response = client.get(
            f"/api/v1/social/friends/{test_user2['id']}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "none"
        assert data["are_friends"] is False

    def test_status_pending_sent(self, client, test_user, test_user2, auth_headers):
        """After sending request, status is 'pending_sent'."""
        _send_request(client, auth_headers, test_user2["id"])

        response = client.get(
            f"/api/v1/social/friends/{test_user2['id']}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_sent"
        assert data["are_friends"] is False

    def test_status_pending_received(self, client, test_user, test_user2, auth_headers):
        """Recipient sees status 'pending_received'."""
        _send_request(client, auth_headers, test_user2["id"])

        headers2 = _headers_for(test_user2)
        response = client.get(
            f"/api/v1/social/friends/{test_user['id']}/status",
            headers=headers2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_received"
        assert data["are_friends"] is False

    def test_status_friends(self, client, test_user, test_user2, auth_headers):
        """After accepting, status is 'friends'."""
        connection = _send_request(client, auth_headers, test_user2["id"])
        headers2 = _headers_for(test_user2)
        client.post(
            f"/api/v1/social/friend-requests/{connection['id']}/accept",
            headers=headers2,
        )

        response = client.get(
            f"/api/v1/social/friends/{test_user2['id']}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "friends"
        assert data["are_friends"] is True


# ── Friend Suggestions ───────────────────────────────────────────


class TestFriendSuggestions:
    """Tests for friend-suggestions endpoints."""

    def test_get_suggestions_shape(self, client, test_user, auth_headers):
        """GET /friend-suggestions returns valid shape."""
        response = client.get(
            "/api/v1/social/friend-suggestions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert "count" in data
        assert isinstance(data["suggestions"], list)

    def test_browse_users_shape(self, client, test_user, auth_headers):
        """GET /friend-suggestions/browse returns valid shape."""
        response = client.get(
            "/api/v1/social/friend-suggestions/browse",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "count" in data
        assert isinstance(data["users"], list)

    def test_dismiss_suggestion(self, client, test_user, test_user2, auth_headers):
        """POST /friend-suggestions/{id}/dismiss returns success."""
        response = client.post(
            f"/api/v1/social/friend-suggestions/{test_user2['id']}/dismiss",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "dismissed" in data

    def test_regenerate_suggestions(self, client, test_user, auth_headers):
        """POST /friend-suggestions/regenerate returns count."""
        response = client.post(
            "/api/v1/social/friend-suggestions/regenerate",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions_created" in data
