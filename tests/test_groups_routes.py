"""Integration tests for groups endpoints."""


class TestCreateGroup:
    """Tests for POST /api/v1/groups/."""

    def test_create_requires_auth(self, client, temp_db):
        """Unauthenticated create returns 401."""
        response = client.post(
            "/api/v1/groups/",
            json={"name": "Test Crew"},
        )
        assert response.status_code == 401

    def test_create_group(self, authenticated_client, test_user):
        """Create a group and get back group data."""
        response = authenticated_client.post(
            "/api/v1/groups/",
            json={
                "name": "Morning Crew",
                "description": "6am training squad",
                "group_type": "training_crew",
                "privacy": "invite_only",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Morning Crew"
        assert "id" in data

    def test_create_open_group(self, authenticated_client, test_user):
        """Create an open group."""
        response = authenticated_client.post(
            "/api/v1/groups/",
            json={
                "name": "Open Mat Gang",
                "privacy": "open",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["privacy"] == "open"


class TestListGroups:
    """Tests for GET /api/v1/groups/."""

    def test_list_requires_auth(self, client, temp_db):
        """Unauthenticated list returns 401."""
        response = client.get("/api/v1/groups/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Authenticated list returns 200 with structure."""
        response = authenticated_client.get("/api/v1/groups/")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert "count" in data

    def test_list_includes_created_group(self, authenticated_client, test_user):
        """Created group appears in user's group list."""
        authenticated_client.post(
            "/api/v1/groups/",
            json={"name": "My Group"},
        )
        response = authenticated_client.get("/api/v1/groups/")
        data = response.json()
        assert data["count"] >= 1
        names = [g["name"] for g in data["groups"]]
        assert "My Group" in names


class TestGetGroup:
    """Tests for GET /api/v1/groups/{group_id}."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated get returns 401."""
        response = client.get("/api/v1/groups/1")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Get non-existent group returns 404."""
        response = authenticated_client.get("/api/v1/groups/999999")
        assert response.status_code == 404

    def test_get_group_detail(self, authenticated_client, test_user):
        """Get group detail includes members and user_role."""
        create_resp = authenticated_client.post(
            "/api/v1/groups/",
            json={"name": "Detail Group"},
        )
        group_id = create_resp.json()["id"]

        response = authenticated_client.get(f"/api/v1/groups/{group_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detail Group"
        assert "members" in data
        assert "member_count" in data
        assert "user_role" in data
        assert data["user_role"] == "admin"


class TestUpdateGroup:
    """Tests for PUT /api/v1/groups/{group_id}."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated update returns 401."""
        response = client.put(
            "/api/v1/groups/1",
            json={"name": "Updated"},
        )
        assert response.status_code == 401

    def test_update_group(self, authenticated_client, test_user):
        """Admin can update group name."""
        create_resp = authenticated_client.post(
            "/api/v1/groups/",
            json={"name": "Old Name"},
        )
        group_id = create_resp.json()["id"]

        response = authenticated_client.put(
            f"/api/v1/groups/{group_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"


class TestDeleteGroup:
    """Tests for DELETE /api/v1/groups/{group_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        response = client.delete("/api/v1/groups/1")
        assert response.status_code == 401

    def test_delete_group(self, authenticated_client, test_user):
        """Admin can delete group."""
        create_resp = authenticated_client.post(
            "/api/v1/groups/",
            json={"name": "Doomed Group"},
        )
        group_id = create_resp.json()["id"]

        response = authenticated_client.delete(f"/api/v1/groups/{group_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = authenticated_client.get(f"/api/v1/groups/{group_id}")
        assert get_resp.status_code == 404


class TestGroupMembership:
    """Tests for join/leave and member management."""

    def test_join_requires_auth(self, client, temp_db):
        """Unauthenticated join returns 401."""
        response = client.post("/api/v1/groups/1/join")
        assert response.status_code == 401

    def test_leave_requires_auth(self, client, temp_db):
        """Unauthenticated leave returns 401."""
        response = client.post("/api/v1/groups/1/leave")
        assert response.status_code == 401

    def test_join_nonexistent_returns_404(self, authenticated_client, test_user):
        """Join non-existent group returns 404."""
        response = authenticated_client.post("/api/v1/groups/999999/join")
        assert response.status_code == 404

    def test_join_invite_only_returns_403(
        self, authenticated_client, test_user, test_user2, client
    ):
        """Joining an invite-only group returns 403."""
        from datetime import timedelta

        from rivaflow.core.auth import create_access_token

        # User 1 creates invite-only group
        create_resp = authenticated_client.post(
            "/api/v1/groups/",
            json={
                "name": "Private Group",
                "privacy": "invite_only",
            },
        )
        group_id = create_resp.json()["id"]

        # User 2 tries to join
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        response = client.post(
            f"/api/v1/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 403
