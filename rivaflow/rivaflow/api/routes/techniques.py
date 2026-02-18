"""Technique management endpoints — backed by movements glossary."""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.glossary_service import GlossaryService

router = APIRouter()


class TechniqueCreateRequest(BaseModel):
    """Input model for creating a technique (writes to glossary)."""

    name: str = Field(min_length=1, max_length=100)
    category: str = Field(default="submission")


@router.post("/")
@limiter.limit("120/minute")
@route_error_handler("add_technique", detail="Failed to add technique")
def add_technique(
    request: Request,
    technique: TechniqueCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new technique (creates a glossary entry)."""
    service = GlossaryService()
    return service.create_custom_movement(
        user_id=current_user["id"],
        name=technique.name,
        category=technique.category,
    )


@router.get("/")
@limiter.limit("120/minute")
@route_error_handler("list_techniques", detail="Failed to list techniques")
def list_techniques(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """List trained techniques with pagination."""
    service = GlossaryService()
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
@limiter.limit("120/minute")
@route_error_handler("get_stale_techniques", detail="Failed to get stale techniques")
def get_stale_techniques(
    request: Request, days: int = 7, current_user: dict = Depends(get_current_user)
):
    """Get stale techniques (trained but not within N days)."""
    service = GlossaryService()
    return service.get_stale_movements(user_id=current_user["id"], days=days)


@router.get("/search")
@limiter.limit("120/minute")
@route_error_handler("search_techniques", detail="Failed to search techniques")
def search_techniques(
    request: Request,
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
):
    """Search techniques by name."""
    service = GlossaryService()
    return service.list_trained_movements(user_id=current_user["id"], search=q)


@router.get("/{technique_id}")
@limiter.limit("120/minute")
@route_error_handler("get_technique", detail="Failed to get technique")
def get_technique(
    request: Request, technique_id: int, current_user: dict = Depends(get_current_user)
):
    """Get a technique by ID (reads from glossary)."""
    service = GlossaryService()
    movement = service.get_movement(
        user_id=current_user["id"], movement_id=technique_id
    )
    if not movement:
        raise NotFoundError("Technique not found")
    return movement
