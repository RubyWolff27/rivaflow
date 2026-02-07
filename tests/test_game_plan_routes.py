"""API route tests for game_plans.py endpoints."""

from unittest.mock import patch

from rivaflow.db.repositories.game_plan_node_repo import (
    GamePlanNodeRepository,
)
from rivaflow.db.repositories.game_plan_repo import (
    GamePlanRepository,
)


class TestGamePlanRoutes:
    """Tests for /api/v1/game-plans endpoints."""

    def _create_plan(self, user_id):
        """Helper to create a game plan."""
        return GamePlanRepository.create(
            user_id=user_id,
            belt_level="white",
            archetype="guard_player",
            title="Test Plan",
        )

    def test_generate_plan(self, authenticated_client, test_user):
        """Test POST /api/v1/game-plans/generate."""
        with patch(
            "rivaflow.core.services.game_plan_template_service" "._resolve_glossary_id",
            return_value=None,
        ):
            resp = authenticated_client.post(
                "/api/v1/game-plans/generate",
                json={
                    "belt_level": "white",
                    "archetype": "guard_player",
                    "style": "balanced",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["belt_level"] == "white"
        assert "id" in data

    def test_generate_plan_invalid_belt(self, authenticated_client):
        """Test generate with invalid belt_level is rejected."""
        resp = authenticated_client.post(
            "/api/v1/game-plans/generate",
            json={
                "belt_level": "orange",
                "archetype": "guard_player",
            },
        )
        assert resp.status_code == 422

    def test_get_current_plan_none(self, authenticated_client):
        """Test GET / when no active plan exists."""
        resp = authenticated_client.get("/api/v1/game-plans/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] is None

    def test_get_current_plan(self, authenticated_client, test_user):
        """Test GET / returns active plan tree."""
        self._create_plan(test_user["id"])
        resp = authenticated_client.get("/api/v1/game-plans/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["belt_level"] == "white"
        assert "nodes" in data

    def test_get_plan_by_id(self, authenticated_client, test_user):
        """Test GET /{plan_id} returns plan tree."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.get(f"/api/v1/game-plans/{plan_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == plan_id

    def test_get_plan_not_found(self, authenticated_client):
        """Test GET /{plan_id} returns 404 for missing plan."""
        resp = authenticated_client.get("/api/v1/game-plans/99999")
        assert resp.status_code == 404

    def test_update_plan(self, authenticated_client, test_user):
        """Test PATCH /{plan_id} updates plan metadata."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.patch(
            f"/api/v1/game-plans/{plan_id}",
            json={"title": "Updated Plan"},
        )
        assert resp.status_code == 200
        # Verify via GET (SQLite nested-conn returns stale data)
        get_resp = authenticated_client.get(f"/api/v1/game-plans/{plan_id}")
        assert get_resp.json()["title"] == "Updated Plan"

    def test_update_plan_no_fields(self, authenticated_client, test_user):
        """Test PATCH with empty body returns 400."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.patch(
            f"/api/v1/game-plans/{plan_id}",
            json={},
        )
        assert resp.status_code == 400

    def test_update_plan_not_found(self, authenticated_client):
        """Test PATCH on nonexistent plan returns 404."""
        resp = authenticated_client.patch(
            "/api/v1/game-plans/99999",
            json={"title": "X"},
        )
        assert resp.status_code == 404

    def test_delete_plan(self, authenticated_client, test_user):
        """Test DELETE /{plan_id}."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.delete(f"/api/v1/game-plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_plan_not_found(self, authenticated_client):
        """Test DELETE on nonexistent plan returns 404."""
        resp = authenticated_client.delete("/api/v1/game-plans/99999")
        assert resp.status_code == 404

    def test_add_node(self, authenticated_client, test_user):
        """Test POST /{plan_id}/nodes."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.post(
            f"/api/v1/game-plans/{plan_id}/nodes",
            json={"name": "New Node", "node_type": "technique"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Node"

    def test_add_node_plan_not_found(self, authenticated_client):
        """Test adding node to nonexistent plan returns 404."""
        resp = authenticated_client.post(
            "/api/v1/game-plans/99999/nodes",
            json={"name": "Node"},
        )
        assert resp.status_code == 404

    def test_update_node(self, authenticated_client, test_user):
        """Test PATCH /{plan_id}/nodes/{node_id}."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Old")
        resp = authenticated_client.patch(
            f"/api/v1/game-plans/{plan_id}/nodes/{node_id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        # Verify via repo (SQLite nested-conn returns stale data)
        refetched = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert refetched["name"] == "Updated"

    def test_update_node_no_fields(self, authenticated_client, test_user):
        """Test PATCH node with empty body returns 400."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Node")
        resp = authenticated_client.patch(
            f"/api/v1/game-plans/{plan_id}/nodes/{node_id}",
            json={},
        )
        assert resp.status_code == 400

    def test_delete_node(self, authenticated_client, test_user):
        """Test DELETE /{plan_id}/nodes/{node_id}."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Del")
        resp = authenticated_client.delete(
            f"/api/v1/game-plans/{plan_id}/nodes/{node_id}"
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_node_not_found(self, authenticated_client, test_user):
        """Test DELETE node that doesn't exist returns 404."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.delete(f"/api/v1/game-plans/{plan_id}/nodes/99999")
        assert resp.status_code == 404

    def test_add_edge(self, authenticated_client, test_user):
        """Test POST /{plan_id}/edges."""
        plan_id = self._create_plan(test_user["id"])
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="A")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="B")
        resp = authenticated_client.post(
            f"/api/v1/game-plans/{plan_id}/edges",
            json={"from_node_id": n1, "to_node_id": n2},
        )
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_add_edge_plan_not_found(self, authenticated_client):
        """Test adding edge to nonexistent plan returns 404."""
        resp = authenticated_client.post(
            "/api/v1/game-plans/99999/edges",
            json={"from_node_id": 1, "to_node_id": 2},
        )
        assert resp.status_code == 404

    def test_delete_edge(self, authenticated_client, test_user):
        """Test DELETE /{plan_id}/edges/{edge_id}."""
        from rivaflow.db.repositories.game_plan_edge_repo import (
            GamePlanEdgeRepository,
        )

        plan_id = self._create_plan(test_user["id"])
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="A")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="B")
        edge_id = GamePlanEdgeRepository.create(
            plan_id=plan_id, from_node_id=n1, to_node_id=n2
        )
        resp = authenticated_client.delete(
            f"/api/v1/game-plans/{plan_id}/edges/{edge_id}"
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_edge_not_found(self, authenticated_client, test_user):
        """Test DELETE edge that doesn't exist returns 404."""
        plan_id = self._create_plan(test_user["id"])
        resp = authenticated_client.delete(f"/api/v1/game-plans/{plan_id}/edges/99999")
        assert resp.status_code == 404

    def test_set_focus(self, authenticated_client, test_user):
        """Test POST /{plan_id}/focus."""
        plan_id = self._create_plan(test_user["id"])
        ids = []
        for i in range(3):
            nid = GamePlanNodeRepository.create(plan_id=plan_id, name=f"F{i}")
            ids.append(nid)

        resp = authenticated_client.post(
            f"/api/v1/game-plans/{plan_id}/focus",
            json={"node_ids": ids},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "focus_nodes" in data
        assert len(data["focus_nodes"]) == 3

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        resp = client.get("/api/v1/game-plans/")
        assert resp.status_code in (401, 403)
