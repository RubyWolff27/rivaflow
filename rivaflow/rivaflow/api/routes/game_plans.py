"""Game Plan API routes — My Game mind map."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from rivaflow.core.dependencies import get_current_user

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
async def generate_plan(
    request: GeneratePlanRequest,
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
            belt_level=request.belt_level,
            archetype=request.archetype,
            style=request.style,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No template available for that combination",
        )

    return plan


@router.get("/")
async def get_current_plan(
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
async def get_plan(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game plan not found",
        )
    return plan


@router.patch("/{plan_id}")
async def update_plan(
    plan_id: int,
    request: UpdatePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update plan metadata."""
    from rivaflow.db.repositories.game_plan_repo import (
        GamePlanRepository,
    )

    user_id = current_user["id"]
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = GamePlanRepository.update(plan_id, user_id, **updates)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game plan not found",
        )
    return result


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a game plan."""
    from rivaflow.db.repositories.game_plan_repo import (
        GamePlanRepository,
    )

    user_id = current_user["id"]
    deleted = GamePlanRepository.delete(plan_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game plan not found",
        )
    return {"success": True}


@router.post("/{plan_id}/nodes")
async def add_node(
    plan_id: int,
    request: AddNodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a node to a game plan."""
    from rivaflow.core.services.game_plan_service import add_node as svc_add_node

    user_id = current_user["id"]
    node = svc_add_node(
        plan_id=plan_id,
        user_id=user_id,
        name=request.name,
        node_type=request.node_type,
        parent_id=request.parent_id,
        glossary_id=request.glossary_id,
    )
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game plan not found",
        )
    return node


@router.patch("/{plan_id}/nodes/{node_id}")
async def update_node(
    plan_id: int,
    node_id: int,
    request: UpdateNodeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a node."""
    from rivaflow.core.services.game_plan_service import update_node as svc_update_node

    user_id = current_user["id"]
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    node = svc_update_node(plan_id, user_id, node_id, **updates)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    return node


@router.delete("/{plan_id}/nodes/{node_id}")
async def delete_node(
    plan_id: int,
    node_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a node."""
    from rivaflow.core.services.game_plan_service import delete_node as svc_delete_node

    user_id = current_user["id"]
    deleted = svc_delete_node(plan_id, user_id, node_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    return {"success": True}


@router.post("/{plan_id}/edges")
async def add_edge(
    plan_id: int,
    request: AddEdgeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add an edge between nodes."""
    from rivaflow.core.services.game_plan_service import add_edge as svc_add_edge

    user_id = current_user["id"]
    edge_id = svc_add_edge(
        plan_id=plan_id,
        user_id=user_id,
        from_node_id=request.from_node_id,
        to_node_id=request.to_node_id,
        edge_type=request.edge_type,
        label=request.label,
    )
    if edge_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game plan not found",
        )
    return {"id": edge_id}


@router.delete("/{plan_id}/edges/{edge_id}")
async def delete_edge(
    plan_id: int,
    edge_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete an edge."""
    from rivaflow.core.services.game_plan_service import delete_edge as svc_delete_edge

    user_id = current_user["id"]
    deleted = svc_delete_edge(plan_id, user_id, edge_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found",
        )
    return {"success": True}


@router.post("/{plan_id}/focus")
async def set_focus(
    plan_id: int,
    request: SetFocusRequest,
    current_user: dict = Depends(get_current_user),
):
    """Set focus nodes (max 5)."""
    from rivaflow.core.services.game_plan_service import (
        set_focus_nodes,
    )

    user_id = current_user["id"]
    focus = set_focus_nodes(plan_id, user_id, request.node_ids)
    return {"focus_nodes": focus}
