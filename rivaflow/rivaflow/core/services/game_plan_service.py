"""Service layer for game plan operations."""

import logging

from rivaflow.db.repositories.game_plan_edge_repo import (
    GamePlanEdgeRepository,
)
from rivaflow.db.repositories.game_plan_node_repo import (
    GamePlanNodeRepository,
)
from rivaflow.db.repositories.game_plan_repo import (
    GamePlanRepository,
)

logger = logging.getLogger(__name__)


def get_plan_tree(plan_id: int, user_id: int) -> dict | None:
    """Get a game plan with its full node tree.

    Returns plan dict with nested 'nodes' tree and 'edges'.
    """
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return None

    flat_nodes = GamePlanNodeRepository.list_by_plan(plan_id)
    edges = GamePlanEdgeRepository.list_by_plan(plan_id)

    plan["nodes"] = _build_tree(flat_nodes)
    plan["flat_nodes"] = flat_nodes
    plan["edges"] = edges
    plan["focus_nodes"] = [n for n in flat_nodes if n.get("is_focus")]
    return plan


def get_active_plan_tree(user_id: int) -> dict | None:
    """Get user's active game plan with tree."""
    plan = GamePlanRepository.get_active(user_id)
    if not plan:
        return None
    return get_plan_tree(plan["id"], user_id)


def update_plan(plan_id: int, user_id: int, **kwargs) -> dict | None:
    """Update plan metadata."""
    return GamePlanRepository.update(plan_id, user_id, **kwargs)


def delete_plan(plan_id: int, user_id: int) -> bool:
    """Delete a game plan."""
    return GamePlanRepository.delete(plan_id, user_id)


def add_node(
    plan_id: int,
    user_id: int,
    name: str,
    node_type: str = "technique",
    parent_id: int | None = None,
    glossary_id: int | None = None,
) -> dict | None:
    """Add a node to a game plan."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return None

    node_id = GamePlanNodeRepository.create(
        plan_id=plan_id,
        name=name,
        node_type=node_type,
        parent_id=parent_id,
        glossary_id=glossary_id,
    )
    return GamePlanNodeRepository.get_by_id(node_id, plan_id)


def update_node(plan_id: int, user_id: int, node_id: int, **kwargs) -> dict | None:
    """Update a node in a game plan."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return None
    return GamePlanNodeRepository.update(node_id, plan_id, **kwargs)


def delete_node(plan_id: int, user_id: int, node_id: int) -> bool:
    """Delete a node from a game plan."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return False
    return GamePlanNodeRepository.delete(node_id, plan_id)


def add_edge(
    plan_id: int,
    user_id: int,
    from_node_id: int,
    to_node_id: int,
    edge_type: str = "transition",
    label: str | None = None,
) -> int | None:
    """Add an edge between two nodes."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return None
    return GamePlanEdgeRepository.create(
        plan_id, from_node_id, to_node_id, edge_type, label
    )


def delete_edge(plan_id: int, user_id: int, edge_id: int) -> bool:
    """Delete an edge from a game plan."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return False
    return GamePlanEdgeRepository.delete(edge_id, plan_id)


def set_focus_nodes(plan_id: int, user_id: int, node_ids: list[int]) -> list[dict]:
    """Set focus nodes for a plan (max 5)."""
    plan = GamePlanRepository.get_by_id(plan_id, user_id)
    if not plan:
        return []
    GamePlanNodeRepository.set_focus_nodes(plan_id, node_ids[:5])
    return GamePlanNodeRepository.get_focus_nodes(plan_id)


def _build_tree(flat_nodes: list[dict]) -> list[dict]:
    """Convert flat node list to nested tree."""
    node_map = {}
    roots = []

    for node in flat_nodes:
        node["children"] = []
        node_map[node["id"]] = node

    for node in flat_nodes:
        parent_id = node.get("parent_id")
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots
