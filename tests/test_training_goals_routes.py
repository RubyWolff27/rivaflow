"""Integration tests for monthly training goals endpoints."""

from datetime import date


class TestCreateTrainingGoal:
    """Tests for POST /api/v1/training-goals/."""

    def test_create_requires_auth(self, client, temp_db):
        """Unauthenticated create returns 401."""
        response = client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "sessions",
                "target_value": 12,
                "month": "2026-02",
            },
        )
        assert response.status_code == 401

    def test_create_frequency_goal(self, authenticated_client, test_user):
        """Create a frequency-based training goal."""
        month = date.today().strftime("%Y-%m")
        response = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "sessions",
                "target_value": 12,
                "month": month,
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["goal_type"] == "frequency"
        assert data["metric"] == "sessions"
        assert data["target_value"] == 12

    def test_create_invalid_metric(self, authenticated_client, test_user):
        """Invalid metric returns 400."""
        response = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "nope",
                "target_value": 5,
                "month": "2026-02",
            },
        )
        assert response.status_code == 400

    def test_create_invalid_goal_type(self, authenticated_client, test_user):
        """Invalid goal_type returns 400."""
        response = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "invalid",
                "metric": "sessions",
                "target_value": 5,
                "month": "2026-02",
            },
        )
        assert response.status_code == 400

    def test_create_zero_target_returns_400(self, authenticated_client, test_user):
        """Zero target_value is rejected."""
        response = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "sessions",
                "target_value": 0,
                "month": "2026-02",
            },
        )
        assert response.status_code == 400


class TestListTrainingGoals:
    """Tests for GET /api/v1/training-goals/."""

    def test_list_requires_auth(self, client, temp_db):
        """Unauthenticated list returns 401."""
        response = client.get("/api/v1/training-goals/")
        assert response.status_code == 401

    def test_list_returns_200(self, authenticated_client, test_user):
        """Authenticated list returns 200."""
        month = date.today().strftime("%Y-%m")
        response = authenticated_client.get(f"/api/v1/training-goals/?month={month}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_includes_created_goal(self, authenticated_client, test_user):
        """Created goal appears in list."""
        month = date.today().strftime("%Y-%m")
        authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "hours",
                "target_value": 10,
                "month": month,
            },
        )
        response = authenticated_client.get(f"/api/v1/training-goals/?month={month}")
        data = response.json()
        assert len(data) >= 1


class TestGetTrainingGoal:
    """Tests for GET /api/v1/training-goals/{goal_id}."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated get returns 401."""
        response = client.get("/api/v1/training-goals/1")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Get non-existent goal returns 404."""
        response = authenticated_client.get("/api/v1/training-goals/999999")
        assert response.status_code == 404

    def test_get_created_goal(self, authenticated_client, test_user):
        """Get a goal that was just created."""
        month = date.today().strftime("%Y-%m")
        create_resp = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "rolls",
                "target_value": 50,
                "month": month,
            },
        )
        goal_id = create_resp.json()["id"]

        response = authenticated_client.get(f"/api/v1/training-goals/{goal_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "rolls"
        assert data["target_value"] == 50


class TestUpdateTrainingGoal:
    """Tests for PUT /api/v1/training-goals/{goal_id}."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated update returns 401."""
        response = client.put(
            "/api/v1/training-goals/1",
            json={"target_value": 20},
        )
        assert response.status_code == 401

    def test_update_target_value(self, authenticated_client, test_user):
        """Update a goal's target value."""
        month = date.today().strftime("%Y-%m")
        create_resp = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "sessions",
                "target_value": 10,
                "month": month,
            },
        )
        goal_id = create_resp.json()["id"]

        response = authenticated_client.put(
            f"/api/v1/training-goals/{goal_id}",
            json={"target_value": 15},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_value"] == 15

    def test_update_nonexistent_returns_404(self, authenticated_client, test_user):
        """Update non-existent goal returns 404."""
        response = authenticated_client.put(
            "/api/v1/training-goals/999999",
            json={"target_value": 20},
        )
        assert response.status_code == 404


class TestDeleteTrainingGoal:
    """Tests for DELETE /api/v1/training-goals/{goal_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        response = client.delete("/api/v1/training-goals/1")
        assert response.status_code == 401

    def test_delete_goal(self, authenticated_client, test_user):
        """Delete a training goal."""
        month = date.today().strftime("%Y-%m")
        create_resp = authenticated_client.post(
            "/api/v1/training-goals/",
            json={
                "goal_type": "frequency",
                "metric": "sessions",
                "target_value": 8,
                "month": month,
            },
        )
        goal_id = create_resp.json()["id"]

        response = authenticated_client.delete(f"/api/v1/training-goals/{goal_id}")
        assert response.status_code == 200

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Delete non-existent goal returns 404."""
        response = authenticated_client.delete("/api/v1/training-goals/999999")
        assert response.status_code == 404
