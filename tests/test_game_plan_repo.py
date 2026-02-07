"""Tests for GamePlanRepository, GamePlanNodeRepository, GamePlanEdgeRepository."""

from rivaflow.db.repositories.game_plan_edge_repo import (
    GamePlanEdgeRepository,
)
from rivaflow.db.repositories.game_plan_node_repo import (
    GamePlanNodeRepository,
)
from rivaflow.db.repositories.game_plan_repo import (
    GamePlanRepository,
)


class TestGamePlanRepository:
    """Tests for GamePlanRepository CRUD operations."""

    def test_create_plan(self, temp_db, test_user):
        """Test creating a game plan returns an int ID."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
            style="balanced",
            title="My Plan",
        )
        assert isinstance(plan_id, int)
        assert plan_id > 0

    def test_get_by_id(self, temp_db, test_user):
        """Test retrieving a plan by ID."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="blue",
            archetype="top_passer",
        )
        plan = GamePlanRepository.get_by_id(plan_id, test_user["id"])
        assert plan is not None
        assert plan["belt_level"] == "blue"
        assert plan["archetype"] == "top_passer"

    def test_get_by_id_wrong_user(self, temp_db, test_user):
        """Test that a plan cannot be retrieved by another user."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        result = GamePlanRepository.get_by_id(plan_id, user_id=99999)
        assert result is None

    def test_get_active(self, temp_db, test_user):
        """Test retrieving the active plan."""
        GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        active = GamePlanRepository.get_active(test_user["id"])
        assert active is not None
        assert active["belt_level"] == "white"

    def test_get_active_none(self, temp_db, test_user):
        """Test get_active returns None when no plan exists."""
        active = GamePlanRepository.get_active(test_user["id"])
        assert active is None

    def test_list_by_user(self, temp_db, test_user):
        """Test listing all plans for a user."""
        GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="blue",
            archetype="top_passer",
        )
        plans = GamePlanRepository.list_by_user(test_user["id"])
        assert len(plans) == 2

    def test_update_plan(self, temp_db, test_user):
        """Test updating plan metadata."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        updated = GamePlanRepository.update(
            plan_id, test_user["id"], title="Updated Title"
        )
        assert updated is not None
        # Re-fetch to confirm the update persisted
        refetched = GamePlanRepository.get_by_id(plan_id, test_user["id"])
        assert refetched["title"] == "Updated Title"

    def test_update_plan_no_fields(self, temp_db, test_user):
        """Test update with no valid fields returns existing plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        result = GamePlanRepository.update(plan_id, test_user["id"], bogus_field="nope")
        assert result is not None

    def test_update_plan_not_found(self, temp_db, test_user):
        """Test update returns None for nonexistent plan."""
        result = GamePlanRepository.update(99999, test_user["id"], title="X")
        assert result is None

    def test_delete_plan(self, temp_db, test_user):
        """Test deleting a plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        deleted = GamePlanRepository.delete(plan_id, test_user["id"])
        assert deleted is True
        assert GamePlanRepository.get_by_id(plan_id, test_user["id"]) is None

    def test_delete_plan_not_found(self, temp_db, test_user):
        """Test deleting a nonexistent plan returns False."""
        deleted = GamePlanRepository.delete(99999, test_user["id"])
        assert deleted is False


class TestGamePlanNodeRepository:
    """Tests for GamePlanNodeRepository CRUD operations."""

    def _create_plan(self, user_id):
        return GamePlanRepository.create(
            user_id=user_id,
            belt_level="white",
            archetype="guard_player",
        )

    def test_create_node(self, temp_db, test_user):
        """Test creating a node."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Armbar")
        assert isinstance(node_id, int)
        assert node_id > 0

    def test_get_by_id(self, temp_db, test_user):
        """Test retrieving a node by ID."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(
            plan_id=plan_id,
            name="Triangle",
            node_type="submission",
        )
        node = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert node is not None
        assert node["name"] == "Triangle"
        assert node["node_type"] == "submission"

    def test_get_by_id_not_found(self, temp_db, test_user):
        """Test get_by_id returns None for nonexistent node."""
        plan_id = self._create_plan(test_user["id"])
        result = GamePlanNodeRepository.get_by_id(99999, plan_id)
        assert result is None

    def test_list_by_plan(self, temp_db, test_user):
        """Test listing nodes for a plan."""
        plan_id = self._create_plan(test_user["id"])
        GamePlanNodeRepository.create(plan_id=plan_id, name="Node A")
        GamePlanNodeRepository.create(plan_id=plan_id, name="Node B")
        nodes = GamePlanNodeRepository.list_by_plan(plan_id)
        assert len(nodes) == 2

    def test_bulk_create(self, temp_db, test_user):
        """Test bulk creating nodes."""
        plan_id = self._create_plan(test_user["id"])
        nodes = [
            {"plan_id": plan_id, "name": "Node 1"},
            {"plan_id": plan_id, "name": "Node 2"},
            {"plan_id": plan_id, "name": "Node 3"},
        ]
        ids = GamePlanNodeRepository.bulk_create(nodes)
        assert len(ids) == 3
        assert all(isinstance(i, int) for i in ids)

    def test_update_node(self, temp_db, test_user):
        """Test updating a node."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Old Name")
        updated = GamePlanNodeRepository.update(
            node_id, plan_id, name="New Name", confidence=4
        )
        assert updated is not None
        # Re-fetch to confirm update persisted
        refetched = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert refetched["name"] == "New Name"
        assert refetched["confidence"] == 4

    def test_update_node_no_fields(self, temp_db, test_user):
        """Test update with no valid fields returns existing node."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Node")
        result = GamePlanNodeRepository.update(node_id, plan_id, fake_field="nope")
        assert result is not None
        assert result["name"] == "Node"

    def test_update_node_not_found(self, temp_db, test_user):
        """Test update returns None for nonexistent node."""
        plan_id = self._create_plan(test_user["id"])
        result = GamePlanNodeRepository.update(99999, plan_id, name="X")
        assert result is None

    def test_delete_node(self, temp_db, test_user):
        """Test deleting a node."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Delete Me")
        deleted = GamePlanNodeRepository.delete(node_id, plan_id)
        assert deleted is True
        assert GamePlanNodeRepository.get_by_id(node_id, plan_id) is None

    def test_delete_node_not_found(self, temp_db, test_user):
        """Test deleting a nonexistent node returns False."""
        plan_id = self._create_plan(test_user["id"])
        deleted = GamePlanNodeRepository.delete(99999, plan_id)
        assert deleted is False

    def test_increment_usage(self, temp_db, test_user):
        """Test incrementing usage stats on a node."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Usage Node")
        GamePlanNodeRepository.increment_usage(node_id, plan_id)
        node = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert node["attempts"] == 1
        assert node["successes"] == 0

    def test_increment_usage_with_success(self, temp_db, test_user):
        """Test incrementing usage with success flag."""
        plan_id = self._create_plan(test_user["id"])
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Success Node")
        GamePlanNodeRepository.increment_usage(node_id, plan_id, success=True)
        node = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert node["attempts"] == 1
        assert node["successes"] == 1

    def test_set_focus_nodes(self, temp_db, test_user):
        """Test setting focus nodes (max 5)."""
        plan_id = self._create_plan(test_user["id"])
        ids = []
        for i in range(6):
            nid = GamePlanNodeRepository.create(plan_id=plan_id, name=f"Node {i}")
            ids.append(nid)

        GamePlanNodeRepository.set_focus_nodes(plan_id, ids)
        focus = GamePlanNodeRepository.get_focus_nodes(plan_id)
        # Max 5 focus nodes
        assert len(focus) == 5

    def test_get_focus_nodes_empty(self, temp_db, test_user):
        """Test get_focus_nodes returns empty list when no focus."""
        plan_id = self._create_plan(test_user["id"])
        GamePlanNodeRepository.create(plan_id=plan_id, name="Node")
        focus = GamePlanNodeRepository.get_focus_nodes(plan_id)
        assert focus == []


class TestGamePlanEdgeRepository:
    """Tests for GamePlanEdgeRepository CRUD operations."""

    def _create_plan_with_nodes(self, user_id):
        plan_id = GamePlanRepository.create(
            user_id=user_id,
            belt_level="white",
            archetype="guard_player",
        )
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="Node A")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="Node B")
        return plan_id, n1, n2

    def test_create_edge(self, temp_db, test_user):
        """Test creating an edge."""
        plan_id, n1, n2 = self._create_plan_with_nodes(test_user["id"])
        edge_id = GamePlanEdgeRepository.create(
            plan_id=plan_id,
            from_node_id=n1,
            to_node_id=n2,
        )
        assert isinstance(edge_id, int)
        assert edge_id > 0

    def test_list_by_plan(self, temp_db, test_user):
        """Test listing edges for a plan."""
        plan_id, n1, n2 = self._create_plan_with_nodes(test_user["id"])
        GamePlanEdgeRepository.create(plan_id=plan_id, from_node_id=n1, to_node_id=n2)
        edges = GamePlanEdgeRepository.list_by_plan(plan_id)
        assert len(edges) == 1
        assert edges[0]["from_node_id"] == n1
        assert edges[0]["to_node_id"] == n2

    def test_bulk_create(self, temp_db, test_user):
        """Test bulk creating edges."""
        plan_id, n1, n2 = self._create_plan_with_nodes(test_user["id"])
        n3 = GamePlanNodeRepository.create(plan_id=plan_id, name="Node C")
        edges = [
            {
                "plan_id": plan_id,
                "from_node_id": n1,
                "to_node_id": n2,
            },
            {
                "plan_id": plan_id,
                "from_node_id": n2,
                "to_node_id": n3,
            },
        ]
        ids = GamePlanEdgeRepository.bulk_create(edges)
        assert len(ids) == 2

    def test_delete_edge(self, temp_db, test_user):
        """Test deleting an edge."""
        plan_id, n1, n2 = self._create_plan_with_nodes(test_user["id"])
        edge_id = GamePlanEdgeRepository.create(
            plan_id=plan_id, from_node_id=n1, to_node_id=n2
        )
        deleted = GamePlanEdgeRepository.delete(edge_id, plan_id)
        assert deleted is True
        assert GamePlanEdgeRepository.list_by_plan(plan_id) == []

    def test_delete_edge_not_found(self, temp_db, test_user):
        """Test deleting a nonexistent edge returns False."""
        plan_id, _, _ = self._create_plan_with_nodes(test_user["id"])
        deleted = GamePlanEdgeRepository.delete(99999, plan_id)
        assert deleted is False

    def test_edge_with_label(self, temp_db, test_user):
        """Test creating an edge with label and type."""
        plan_id, n1, n2 = self._create_plan_with_nodes(test_user["id"])
        GamePlanEdgeRepository.create(
            plan_id=plan_id,
            from_node_id=n1,
            to_node_id=n2,
            edge_type="counter",
            label="sweep defense",
        )
        edges = GamePlanEdgeRepository.list_by_plan(plan_id)
        assert len(edges) == 1
        assert edges[0]["edge_type"] == "counter"
        assert edges[0]["label"] == "sweep defense"
