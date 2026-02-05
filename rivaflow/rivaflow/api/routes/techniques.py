"""Technique management endpoints."""

from fastapi import APIRouter, Depends, Query

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.models import TechniqueCreate
from rivaflow.core.services.technique_service import TechniqueService

router = APIRouter()
service = TechniqueService()


@router.post("/")
async def add_technique(technique: TechniqueCreate, current_user: dict = Depends(get_current_user)):
    """Add a new technique."""
    technique_id = service.add_technique(
        user_id=current_user["id"],
        name=technique.name,
        category=technique.category,
    )
    created_technique = service.get_technique(user_id=current_user["id"], technique_id=technique_id)
    return created_technique


@router.get("/")
async def list_techniques(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """List all techniques with pagination."""
    all_techniques = service.list_all_techniques(user_id=current_user["id"])
    total = len(all_techniques)
    techniques = all_techniques[offset : offset + limit]

    return {"techniques": techniques, "total": total, "limit": limit, "offset": offset}


@router.get("/stale")
async def get_stale_techniques(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Get stale techniques (not trained in N days)."""
    return service.get_stale_techniques(user_id=current_user["id"], days=days)


@router.get("/search")
async def search_techniques(
    q: str = Query(..., min_length=2), current_user: dict = Depends(get_current_user)
):
    """Search techniques by name."""
    return service.search_techniques(user_id=current_user["id"], query=q)


@router.get("/{technique_id}")
async def get_technique(technique_id: int, current_user: dict = Depends(get_current_user)):
    """Get a technique by ID."""
    technique = service.get_technique(user_id=current_user["id"], technique_id=technique_id)
    if not technique:
        raise NotFoundError("Technique not found")
    return technique
