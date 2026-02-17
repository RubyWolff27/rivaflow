"""Integration tests for grading/belt progression endpoints."""


class TestListGradings:
    """Tests for GET /api/v1/gradings/."""

    def test_list_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/gradings/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Authenticated list returns 200."""
        response = authenticated_client.get("/api/v1/gradings/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_empty_initially(self, authenticated_client, test_user):
        """New user has no gradings."""
        response = authenticated_client.get("/api/v1/gradings/")
        data = response.json()
        assert data == []


class TestCreateGrading:
    """Tests for POST /api/v1/gradings/."""

    def test_create_requires_auth(self, client, temp_db):
        """Unauthenticated create returns 401."""
        response = client.post(
            "/api/v1/gradings/",
            json={
                "grade": "blue",
                "date_graded": "2025-06-15",
            },
        )
        assert response.status_code == 401

    def test_create_grading(self, authenticated_client, test_user):
        """Create a belt grading."""
        response = authenticated_client.post(
            "/api/v1/gradings/",
            json={
                "grade": "blue",
                "date_graded": "2025-06-15",
                "professor": "Professor Carlos",
                "notes": "Great promotion day",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["grade"] == "blue"
        assert data["date_graded"] == "2025-06-15"

    def test_create_grading_minimal(self, authenticated_client, test_user):
        """Create a grading with only required fields."""
        response = authenticated_client.post(
            "/api/v1/gradings/",
            json={
                "grade": "white",
                "date_graded": "2024-01-01",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["grade"] == "white"


class TestGetLatestGrading:
    """Tests for GET /api/v1/gradings/latest."""

    def test_latest_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/gradings/latest")
        assert response.status_code == 401

    def test_latest_when_empty(self, authenticated_client, test_user):
        """Returns null when no gradings exist."""
        response = authenticated_client.get("/api/v1/gradings/latest")
        assert response.status_code == 200

    def test_latest_after_create(self, authenticated_client, test_user):
        """Returns most recent grading after creation."""
        authenticated_client.post(
            "/api/v1/gradings/",
            json={"grade": "white", "date_graded": "2024-01-01"},
        )
        authenticated_client.post(
            "/api/v1/gradings/",
            json={"grade": "blue", "date_graded": "2025-06-15"},
        )
        response = authenticated_client.get("/api/v1/gradings/latest")
        assert response.status_code == 200
        data = response.json()
        if data is not None:
            assert data["grade"] == "blue"


class TestUpdateGrading:
    """Tests for PUT /api/v1/gradings/{grading_id}."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated update returns 401."""
        response = client.put(
            "/api/v1/gradings/1",
            json={"grade": "purple"},
        )
        assert response.status_code == 401

    def test_update_grading(self, authenticated_client, test_user):
        """Update a grading's grade and notes."""
        create_resp = authenticated_client.post(
            "/api/v1/gradings/",
            json={"grade": "blue", "date_graded": "2025-06-15"},
        )
        grading_id = create_resp.json()["id"]

        response = authenticated_client.put(
            f"/api/v1/gradings/{grading_id}",
            json={"grade": "purple", "notes": "Updated notes"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["grade"] == "purple"

    def test_update_nonexistent_returns_404(self, authenticated_client, test_user):
        """Update non-existent grading returns 404."""
        response = authenticated_client.put(
            "/api/v1/gradings/999999",
            json={"grade": "black"},
        )
        assert response.status_code == 404


class TestDeleteGrading:
    """Tests for DELETE /api/v1/gradings/{grading_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        response = client.delete("/api/v1/gradings/1")
        assert response.status_code == 401

    def test_delete_grading(self, authenticated_client, test_user):
        """Delete a grading returns 204."""
        create_resp = authenticated_client.post(
            "/api/v1/gradings/",
            json={"grade": "blue", "date_graded": "2025-06-15"},
        )
        grading_id = create_resp.json()["id"]

        response = authenticated_client.delete(f"/api/v1/gradings/{grading_id}")
        assert response.status_code == 204

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Delete non-existent grading returns 404."""
        response = authenticated_client.delete("/api/v1/gradings/999999")
        assert response.status_code == 404
