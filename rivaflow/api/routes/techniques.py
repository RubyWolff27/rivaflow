"""Technique management endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional

from rivaflow.core.services.technique_service import TechniqueService
from rivaflow.core.models import TechniqueCreate

router = APIRouter()
service = TechniqueService()


@router.post("/")
async def add_technique(technique: TechniqueCreate):
    """Add a new technique."""
    try:
        technique_id = service.add_technique(
            name=technique.name,
            category=technique.category,
        )
        created_technique = service.get_technique(technique_id)
        return created_technique
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_techniques():
    """List all techniques."""
    return service.list_all_techniques()


@router.get("/stale")
async def get_stale_techniques(days: int = 7):
    """Get stale techniques (not trained in N days)."""
    return service.get_stale_techniques(days)


@router.get("/search")
async def search_techniques(q: str):
    """Search techniques by name."""
    return service.search_techniques(q)


@router.get("/{technique_id}")
async def get_technique(technique_id: int):
    """Get a technique by ID."""
    technique = service.get_technique(technique_id)
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique
