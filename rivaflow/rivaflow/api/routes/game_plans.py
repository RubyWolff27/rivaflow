"""Game Plan API routes — My Game mind map."""

import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/game-plans", tags=["game-plans"])
logger = logging.getLogger(__name__)


# Request/Response Models


class GeneratePlanRequest(BaseModel):
    belt_level: str = Field(..., pattern="^(white|blue|purple|brown|black)$")
    archetype: str = Field(
        ...,
        pattern="^(guard_player|top_passer)$",
    )
    style: str = "balanced"


class AddNodeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    node_type: str = "technique"
    parent_id: int | None = None
    glossary_id: int | None = None


class UpdateNodeRequest(BaseModel):
    name: str | None = None
    node_type: str | None = None
    confidence: int | None = Field(None, ge=1, le=5)
    priority: str | None = None
    is_focus: bool | None = None
    notes: str | None = None
    parent_id: int | None = None


class UpdatePlanRequest(BaseModel):
    title: str | None = None
    belt_level: str | None = None
    archetype: str | None = None
    style: str | None = None
    is_active: bool | None = None


class AddEdgeRequest(BaseModel):
    from_node_id: int
    to_node_id: int
    edge_type: str = "transition"
    label: str | None = None


class SetFocusRequest(BaseModel):
    node_ids: list[int] = Field(..., max_length=5)


# Endpoints


@router.post("/generate")
@limiter.limit("20/minute")
@route_error_handler("generate_plan", detail="Failed to generate game plan")
def generate_plan(
    request: Request,
    body: GeneratePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a game plan from a template."""
    from rivaflow.core.services.game_plan_template_service import (
        generate_plan_from_template,
    )

    user_id = current_user["id"]
    try:
        plan = generate_plan_from_template(
            user_id=user_id,
            belt_level=body.belt_level,
            archetype=body.archetype,
            style=body.style,
        )
    except FileNotFoundError:
        raise ValidationError("No template available for that combination")

    return plan


@router.get("/")
@limiter.limit("60/minute")
@route_error_handler("get_current_plan", detail="Failed to get game plan")
def get_current_plan(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get user's active game plan with full tree."""
    from rivaflow.core.services.game_plan_service import (
        get_active_plan_tree,
    )

    user_id = current_user["id"]
    plan = get_active_plan_tree(user_id)
    if not plan:
        return {"plan": None}
    return plan


@router.get("/{plan_id}")
@limiter.limit("60/minute")
@route_error_handler("get_plan", detail="Failed to get game plan")
def get_plan(
    request: Request,
    plan_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific game plan by ID."""
    from rivaflow.core.services.game_plan_service import (
        get_plan_tree,
    )

    user_id = current_user["id"]
    plan = get_plan_tree(plan_id, user_id)
    if not plan:
        raise NotFoundError("Game plan not found")
    return plan


@router.patch("/{plan_id}")
@limiter.limit("30/minute")
@route_error_handler("update_plan", detail="Failed to update game plan")
def update_plan(
    request: Request,
    plan_id: int,
    body: UpdatePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update plan metadata."""
    from rivaflow.core.services.game_plan_service import (
        update_plan as svc_update_plan,
    )

    user_id = current_user["id"]
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise ValidationError("No fields to update")

    result = svc_update_plan(plan_id, user_id, **updates)
    if not result:
        raise NotFoundError("Game plan not found")
    return result


@router.delete("/{plan_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_plan", detail="Failed to delete game plan")
def delete_plan(
    request: Request,
    plan_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a game plan."""
    from rivaflow.core.services.game_plan_service import (
        delete_plan as svc_delete_plan,
    )

    user_id = current_user["id"]
    deleted = svc_delete_plan(plan_id, user_id)
    if not deleted:
        raise NotFoundError("Game plan not found")
    return {"message": "Game plan deleted"}


@router.post("/{plan_id}/nodes")
@limiter.limit("20/minute")
@route_error_handler("add_node", detail="Failed to add node")
def add_node(
    request: Request,
    plan_id: int,
    body: AddNodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a node to a game plan."""
    from rivaflow.core.services.game_plan_service import add_node as svc_add_node

    user_id = current_user["id"]
    node = svc_add_node(
        plan_id=plan_id,
        user_id=user_id,
        name=body.name,
        node_type=body.node_type,
        parent_id=body.parent_id,
        glossary_id=body.glossary_id,
    )
    if not node:
        raise NotFoundError("Game plan not found")
    return node


@router.patch("/{plan_id}/nodes/{node_id}")
@limiter.limit("30/minute")
@route_error_handler("update_node", detail="Failed to update node")
def update_node(
    request: Request,
    plan_id: int,
    node_id: int,
    body: UpdateNodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a node."""
    from rivaflow.core.services.game_plan_service import update_node as svc_update_node

    user_id = current_user["id"]
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise ValidationError("No fields to update")

    node = svc_update_node(plan_id, user_id, node_id, **updates)
    if not node:
        raise NotFoundError("Node not found")
    return node


@router.delete("/{plan_id}/nodes/{node_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_node", detail="Failed to delete node")
def delete_node(
    request: Request,
    plan_id: int,
    node_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a node."""
    from rivaflow.core.services.game_plan_service import delete_node as svc_delete_node

    user_id = current_user["id"]
    deleted = svc_delete_node(plan_id, user_id, node_id)
    if not deleted:
        raise NotFoundError("Node not found")
    return {"message": "Node deleted"}


@router.post("/{plan_id}/edges")
@limiter.limit("20/minute")
@route_error_handler("add_edge", detail="Failed to add edge")
def add_edge(
    request: Request,
    plan_id: int,
    body: AddEdgeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add an edge between nodes."""
    from rivaflow.core.services.game_plan_service import add_edge as svc_add_edge

    user_id = current_user["id"]
    edge_id = svc_add_edge(
        plan_id=plan_id,
        user_id=user_id,
        from_node_id=body.from_node_id,
        to_node_id=body.to_node_id,
        edge_type=body.edge_type,
        label=body.label,
    )
    if edge_id is None:
        raise NotFoundError("Game plan not found")
    return {"id": edge_id}


@router.delete("/{plan_id}/edges/{edge_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_edge", detail="Failed to delete edge")
def delete_edge(
    request: Request,
    plan_id: int,
    edge_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete an edge."""
    from rivaflow.core.services.game_plan_service import delete_edge as svc_delete_edge

    user_id = current_user["id"]
    deleted = svc_delete_edge(plan_id, user_id, edge_id)
    if not deleted:
        raise NotFoundError("Edge not found")
    return {"message": "Edge deleted"}


@router.post("/{plan_id}/focus")
@limiter.limit("20/minute")
@route_error_handler("set_focus", detail="Failed to set focus nodes")
def set_focus(
    request: Request,
    plan_id: int,
    body: SetFocusRequest,
    current_user: dict = Depends(get_current_user),
):
    """Set focus nodes (max 5)."""
    from rivaflow.core.services.game_plan_service import (
        set_focus_nodes,
    )

    user_id = current_user["id"]
    focus = set_focus_nodes(plan_id, user_id, body.node_ids)
    return {"focus_nodes": focus}
