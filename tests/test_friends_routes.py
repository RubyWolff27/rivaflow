"""Integration tests for friends (contacts) endpoints."""


class TestListContacts:
    """Tests for GET /api/v1/friends/."""

    def test_list_requires_auth(self, client, temp_db):
        """Unauthenticated request to list contacts returns 401."""
        response = client.get("/api/v1/friends/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Authenticated list returns 200 with paginated structure."""
        response = authenticated_client.get("/api/v1/friends/")
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
        assert "total" in data
        assert isinstance(data["friends"], list)

    def test_list_empty_initially(self, authenticated_client, test_user):
        """New user has no contacts."""
        response = authenticated_client.get("/api/v1/friends/")
        data = response.json()
        assert data["total"] == 0
        assert data["friends"] == []


class TestCreateContact:
    """Tests for POST /api/v1/friends/."""

    def test_create_requires_auth(self, client, temp_db):
        """Unauthenticated create returns 401."""
        response = client.post(
            "/api/v1/friends/",
            json={"name": "Alice"},
        )
        assert response.status_code == 401

    def test_create_contact(self, authenticated_client, test_user):
        """Create a training partner contact."""
        response = authenticated_client.post(
            "/api/v1/friends/",
            json={
                "name": "Bob",
                "friend_type": "training-partner",
                "belt_rank": "blue",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Bob"
        assert data["friend_type"] == "training-partner"

    def test_create_instructor(self, authenticated_client, test_user):
        """Create an instructor contact."""
        response = authenticated_client.post(
            "/api/v1/friends/",
            json={
                "name": "Professor Carlos",
                "friend_type": "instructor",
                "belt_rank": "black",
                "instructor_certification": "3rd degree",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Professor Carlos"
        assert data["friend_type"] == "instructor"


class TestGetContact:
    """Tests for GET /api/v1/friends/{friend_id}."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated get returns 401."""
        response = client.get("/api/v1/friends/1")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Get non-existent contact returns 404."""
        response = authenticated_client.get("/api/v1/friends/999999")
        assert response.status_code == 404

    def test_get_created_contact(self, authenticated_client, test_user):
        """Get a contact that was just created."""
        create_resp = authenticated_client.post(
            "/api/v1/friends/",
            json={"name": "Charlie", "friend_type": "training-partner"},
        )
        assert create_resp.status_code == 201
        friend_id = create_resp.json()["id"]

        response = authenticated_client.get(f"/api/v1/friends/{friend_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Charlie"


class TestUpdateContact:
    """Tests for PUT /api/v1/friends/{friend_id}."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated update returns 401."""
        response = client.put(
            "/api/v1/friends/1",
            json={"name": "Updated"},
        )
        assert response.status_code == 401

    def test_update_contact(self, authenticated_client, test_user):
        """Update a contact returns 200."""
        create_resp = authenticated_client.post(
            "/api/v1/friends/",
            json={"name": "Dave", "belt_rank": "white"},
        )
        friend_id = create_resp.json()["id"]

        response = authenticated_client.put(
            f"/api/v1/friends/{friend_id}",
            json={"belt_rank": "blue"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "id" in data

    def test_update_nonexistent_returns_404(self, authenticated_client, test_user):
        """Update non-existent contact returns 404."""
        response = authenticated_client.put(
            "/api/v1/friends/999999",
            json={"name": "Ghost"},
        )
        assert response.status_code == 404


class TestDeleteContact:
    """Tests for DELETE /api/v1/friends/{friend_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        response = client.delete("/api/v1/friends/1")
        assert response.status_code == 401

    def test_delete_contact(self, authenticated_client, test_user):
        """Delete a contact returns 204."""
        create_resp = authenticated_client.post(
            "/api/v1/friends/",
            json={"name": "Eve"},
        )
        friend_id = create_resp.json()["id"]

        response = authenticated_client.delete(f"/api/v1/friends/{friend_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = authenticated_client.get(f"/api/v1/friends/{friend_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Delete non-existent contact returns 404."""
        response = authenticated_client.delete("/api/v1/friends/999999")
        assert response.status_code == 404


class TestContactFilters:
    """Tests for filtering contacts by type and search."""

    def test_list_instructors(self, authenticated_client, test_user):
        """GET /api/v1/friends/instructors returns 200."""
        response = authenticated_client.get("/api/v1/friends/instructors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_partners(self, authenticated_client, test_user):
        """GET /api/v1/friends/partners returns 200."""
        response = authenticated_client.get("/api/v1/friends/partners")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_contacts(self, authenticated_client, test_user):
        """Search contacts by name."""
        authenticated_client.post(
            "/api/v1/friends/",
            json={"name": "Searchable Sam"},
        )
        response = authenticated_client.get("/api/v1/friends/?search=Searchable")
        assert response.status_code == 200
        data = response.json()
        assert "friends" in data
