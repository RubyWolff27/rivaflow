"""Technique management endpoints."""
from fastapi import APIRouter, Depends
from typing import Optional

from rivaflow.core.services.technique_service import TechniqueService
from rivaflow.core.models import TechniqueCreate
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

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
async def list_techniques(current_user: dict = Depends(get_current_user)):
    """List all techniques."""
    return service.list_all_techniques(user_id=current_user["id"])


@router.get("/stale")
async def get_stale_techniques(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Get stale techniques (not trained in N days)."""
    return service.get_stale_techniques(user_id=current_user["id"], days=days)


@router.get("/search")
async def search_techniques(q: str, current_user: dict = Depends(get_current_user)):
    """Search techniques by name."""
    return service.search_techniques(user_id=current_user["id"], query=q)


@router.get("/{technique_id}")
async def get_technique(technique_id: int, current_user: dict = Depends(get_current_user)):
    """Get a technique by ID."""
    technique = service.get_technique(user_id=current_user["id"], technique_id=technique_id)
    if not technique:
        raise NotFoundError("Technique not found")
    return technique
