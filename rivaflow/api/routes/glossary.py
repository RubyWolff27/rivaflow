"""Movements glossary endpoints."""
import logging
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional, List

from rivaflow.core.services.glossary_service import GlossaryService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError
from rivaflow.core.validation import validate_video_url

logger = logging.getLogger(__name__)

router = APIRouter()
service = GlossaryService()


class MovementCreate(BaseModel):
    """Movement creation model."""
    name: str
    category: str
    subcategory: Optional[str] = None
    points: int = 0
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    gi_applicable: bool = True
    nogi_applicable: bool = True


class CustomVideoCreate(BaseModel):
    """Custom video link creation model."""
    url: str
    title: Optional[str] = None
    video_type: str = "general"  # gi, nogi, or general


@router.get("/")
async def list_movements(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name, description, aliases"),
    gi_only: bool = Query(False, description="Only gi-applicable movements"),
    nogi_only: bool = Query(False, description="Only no-gi-applicable movements"),
    current_user: dict = Depends(get_current_user),
):
    """Get all movements with optional filtering."""
    movements = service.list_movements(
        user_id=current_user["id"],
        category=category,
        search=search,
        gi_only=gi_only,
        nogi_only=nogi_only,
    )
    return movements


@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get list of all movement categories."""
    categories = service.get_categories(user_id=current_user["id"])
    return {"categories": categories}


@router.get("/{movement_id}")
async def get_movement(movement_id: int, include_videos: bool = Query(True, description="Include custom video links"), current_user: dict = Depends(get_current_user)):
    """Get a specific movement by ID with optional video links."""
    movement = service.get_movement(user_id=current_user["id"], movement_id=movement_id, include_custom_videos=include_videos)
    if not movement:
        raise NotFoundError("Movement not found")
    return movement


@router.post("/")
async def create_custom_movement(movement: MovementCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom user-added movement."""
    try:
        created = service.create_custom_movement(
            user_id=current_user["id"],
            name=movement.name,
            category=movement.category,
            subcategory=movement.subcategory,
            points=movement.points,
            description=movement.description,
            aliases=movement.aliases,
            gi_applicable=movement.gi_applicable,
            nogi_applicable=movement.nogi_applicable,
        )
        return created
    # Global error handler will catch unexpected exceptions

    pass


@router.delete("/{movement_id}")
async def delete_custom_movement(movement_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a custom movement. Can only delete custom movements."""
    deleted = service.delete_custom_movement(user_id=current_user["id"], movement_id=movement_id)
    if not deleted:
        raise NotFoundError("Movement not found or cannot delete seeded movements")
    return {"message": "Movement deleted successfully"}


@router.post("/{movement_id}/videos")
async def add_custom_video(movement_id: int, video: CustomVideoCreate, current_user: dict = Depends(get_current_user)):
    """Add a custom video link to a movement."""
    # Validate URL for security
    try:
        validate_video_url(video.url)
    except ValueError as e:
        raise ValidationError(str(e))

    created = service.add_custom_video(
        user_id=current_user["id"],
        movement_id=movement_id,
        url=video.url,
        title=video.title,
        video_type=video.video_type,
    )
    return created
    # Global error handler will catch unexpected exceptions


@router.delete("/{movement_id}/videos/{video_id}")
async def delete_custom_video(movement_id: int, video_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a custom video link."""
    deleted = service.delete_custom_video(user_id=current_user["id"], video_id=video_id)
    if not deleted:
        raise NotFoundError("Video not found")
    return {"message": "Video deleted successfully"}
