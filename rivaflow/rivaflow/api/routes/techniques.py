"""Technique management endpoints — backed by movements glossary."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.glossary_service import GlossaryService

router = APIRouter()
service = GlossaryService()


class TechniqueCreateRequest(BaseModel):
    """Input model for creating a technique (writes to glossary)."""

    name: str = Field(min_length=1, max_length=100)
    category: str = Field(default="submission")


@router.post("/")
async def add_technique(
    technique: TechniqueCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new technique (creates a glossary entry)."""
    return service.create_custom_movement(
        user_id=current_user["id"],
        name=technique.name,
        category=technique.category,
    )


@router.get("/")
async def list_techniques(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """List trained techniques with pagination."""
    all_techniques = service.list_trained_movements(
        user_id=current_user["id"], trained_only=True
    )
    total = len(all_techniques)
    techniques = all_techniques[offset : offset + limit]

    return {
        "techniques": techniques,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stale")
async def get_stale_techniques(
    days: int = 7, current_user: dict = Depends(get_current_user)
):
    """Get stale techniques (trained but not within N days)."""
    return service.get_stale_movements(user_id=current_user["id"], days=days)


@router.get("/search")
async def search_techniques(
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
):
    """Search techniques by name."""
    return service.list_trained_movements(user_id=current_user["id"], search=q)


@router.get("/{technique_id}")
async def get_technique(
    technique_id: int, current_user: dict = Depends(get_current_user)
):
    """Get a technique by ID (reads from glossary)."""
    movement = service.get_movement(
        user_id=current_user["id"], movement_id=technique_id
    )
    if not movement:
        raise NotFoundError("Technique not found")
    return movement
