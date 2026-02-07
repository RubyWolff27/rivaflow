"""Tests for game_plan_service and game_plan_template_service."""

from unittest.mock import patch

from rivaflow.core.services.game_plan_service import (
    _build_tree,
    add_edge,
    add_node,
    delete_edge,
    delete_node,
    get_plan_tree,
    set_focus_nodes,
    update_node,
)
from rivaflow.db.repositories.game_plan_edge_repo import (
    GamePlanEdgeRepository,
)
from rivaflow.db.repositories.game_plan_node_repo import (
    GamePlanNodeRepository,
)
from rivaflow.db.repositories.game_plan_repo import (
    GamePlanRepository,
)


class TestBuildTree:
    """Tests for the _build_tree utility function."""

    def test_empty_list(self):
        """Test with empty list returns empty list."""
        assert _build_tree([]) == []

    def test_flat_nodes(self):
        """Test flat nodes become root nodes."""
        nodes = [
            {"id": 1, "parent_id": None, "name": "A"},
            {"id": 2, "parent_id": None, "name": "B"},
        ]
        tree = _build_tree(nodes)
        assert len(tree) == 2
        assert tree[0]["children"] == []
        assert tree[1]["children"] == []

    def test_nested_tree(self):
        """Test parent-child nesting."""
        nodes = [
            {"id": 1, "parent_id": None, "name": "Root"},
            {"id": 2, "parent_id": 1, "name": "Child"},
            {"id": 3, "parent_id": 1, "name": "Child 2"},
        ]
        tree = _build_tree(nodes)
        assert len(tree) == 1
        assert tree[0]["name"] == "Root"
        assert len(tree[0]["children"]) == 2

    def test_orphan_node_becomes_root(self):
        """Test node with missing parent becomes root."""
        nodes = [
            {"id": 1, "parent_id": None, "name": "Root"},
            {"id": 2, "parent_id": 999, "name": "Orphan"},
        ]
        tree = _build_tree(nodes)
        assert len(tree) == 2


class TestGamePlanService:
    """Tests for game plan service functions."""

    def test_get_plan_tree(self, temp_db, test_user):
        """Test getting a full plan tree."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="Root")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="Child", parent_id=n1)
        GamePlanEdgeRepository.create(plan_id=plan_id, from_node_id=n1, to_node_id=n2)

        tree = get_plan_tree(plan_id, test_user["id"])

        assert tree is not None
        assert "nodes" in tree
        assert "flat_nodes" in tree
        assert "edges" in tree
        assert "focus_nodes" in tree
        assert len(tree["nodes"]) == 1
        assert len(tree["nodes"][0]["children"]) == 1
        assert len(tree["flat_nodes"]) == 2
        assert len(tree["edges"]) == 1

    def test_get_plan_tree_not_found(self, temp_db, test_user):
        """Test getting a nonexistent plan returns None."""
        result = get_plan_tree(99999, test_user["id"])
        assert result is None

    def test_add_node(self, temp_db, test_user):
        """Test adding a node to a plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        node = add_node(
            plan_id=plan_id,
            user_id=test_user["id"],
            name="Armbar",
            node_type="submission",
        )
        assert node is not None
        assert node["name"] == "Armbar"

    def test_add_node_plan_not_found(self, temp_db, test_user):
        """Test adding node to nonexistent plan returns None."""
        result = add_node(
            plan_id=99999,
            user_id=test_user["id"],
            name="X",
        )
        assert result is None

    def test_update_node(self, temp_db, test_user):
        """Test updating a node in a plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Old")
        result = update_node(plan_id, test_user["id"], node_id, name="New")
        assert result is not None
        # Re-fetch to confirm update persisted
        refetched = GamePlanNodeRepository.get_by_id(node_id, plan_id)
        assert refetched["name"] == "New"

    def test_update_node_plan_not_found(self, temp_db, test_user):
        """Test update_node with nonexistent plan returns None."""
        result = update_node(99999, test_user["id"], 1, name="X")
        assert result is None

    def test_delete_node(self, temp_db, test_user):
        """Test deleting a node from a plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        node_id = GamePlanNodeRepository.create(plan_id=plan_id, name="Del")
        deleted = delete_node(plan_id, test_user["id"], node_id)
        assert deleted is True

    def test_delete_node_plan_not_found(self, temp_db, test_user):
        """Test delete_node with nonexistent plan returns False."""
        result = delete_node(99999, test_user["id"], 1)
        assert result is False

    def test_add_edge(self, temp_db, test_user):
        """Test adding an edge between nodes."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="A")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="B")
        edge_id = add_edge(plan_id, test_user["id"], n1, n2, label="sweep")
        assert edge_id is not None
        assert isinstance(edge_id, int)

    def test_add_edge_plan_not_found(self, temp_db, test_user):
        """Test adding edge to nonexistent plan returns None."""
        result = add_edge(99999, test_user["id"], 1, 2)
        assert result is None

    def test_delete_edge(self, temp_db, test_user):
        """Test deleting an edge."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        n1 = GamePlanNodeRepository.create(plan_id=plan_id, name="A")
        n2 = GamePlanNodeRepository.create(plan_id=plan_id, name="B")
        edge_id = GamePlanEdgeRepository.create(
            plan_id=plan_id, from_node_id=n1, to_node_id=n2
        )
        deleted = delete_edge(plan_id, test_user["id"], edge_id)
        assert deleted is True

    def test_delete_edge_plan_not_found(self, temp_db, test_user):
        """Test delete_edge with nonexistent plan returns False."""
        result = delete_edge(99999, test_user["id"], 1)
        assert result is False

    def test_set_focus_nodes(self, temp_db, test_user):
        """Test setting focus nodes on a plan."""
        plan_id = GamePlanRepository.create(
            user_id=test_user["id"],
            belt_level="white",
            archetype="guard_player",
        )
        ids = []
        for i in range(3):
            nid = GamePlanNodeRepository.create(plan_id=plan_id, name=f"N{i}")
            ids.append(nid)

        focus = set_focus_nodes(plan_id, test_user["id"], ids)
        assert len(focus) == 3

    def test_set_focus_nodes_plan_not_found(self, temp_db, test_user):
        """Test set_focus_nodes with nonexistent plan returns []."""
        result = set_focus_nodes(99999, test_user["id"], [1, 2])
        assert result == []


class TestGamePlanTemplateService:
    """Tests for generate_plan_from_template."""

    def test_generate_plan_from_template(self, temp_db, test_user):
        """Test generating a plan from an existing template."""
        from rivaflow.core.services.game_plan_template_service import (
            generate_plan_from_template,
        )

        # Mock glossary lookups to return None (no glossary)
        with patch(
            "rivaflow.core.services.game_plan_template_service" "._resolve_glossary_id",
            return_value=None,
        ):
            plan = generate_plan_from_template(
                user_id=test_user["id"],
                belt_level="white",
                archetype="guard_player",
                style="balanced",
            )

        assert plan is not None
        assert plan["belt_level"] == "white"
        assert plan["archetype"] == "guard_player"
        assert plan["title"] == "White Belt - Guard Player"

        # Verify nodes were created
        nodes = GamePlanNodeRepository.list_by_plan(plan["id"])
        assert len(nodes) > 0

    def test_generate_plan_fallback_template(self, temp_db, test_user):
        """Test that a missing template falls back to default."""
        from rivaflow.core.services.game_plan_template_service import (
            generate_plan_from_template,
        )

        with patch(
            "rivaflow.core.services.game_plan_template_service" "._resolve_glossary_id",
            return_value=None,
        ):
            # purple_guard_player doesn't exist -> fallback
            plan = generate_plan_from_template(
                user_id=test_user["id"],
                belt_level="purple",
                archetype="guard_player",
            )

        assert plan is not None
        # Falls back to white_guard_player template
        assert plan["belt_level"] == "purple"
