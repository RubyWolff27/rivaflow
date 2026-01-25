"""Movements glossary endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from rivaflow.core.services.glossary_service import GlossaryService

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
):
    """Get all movements with optional filtering."""
    movements = service.list_movements(
        category=category,
        search=search,
        gi_only=gi_only,
        nogi_only=nogi_only,
    )
    return movements


@router.get("/categories")
async def get_categories():
    """Get list of all movement categories."""
    categories = service.get_categories()
    return {"categories": categories}


@router.get("/{movement_id}")
async def get_movement(movement_id: int, include_videos: bool = Query(True, description="Include custom video links")):
    """Get a specific movement by ID with optional video links."""
    movement = service.get_movement(movement_id, include_custom_videos=include_videos)
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return movement


@router.post("/")
async def create_custom_movement(movement: MovementCreate):
    """Create a custom user-added movement."""
    try:
        created = service.create_custom_movement(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{movement_id}")
async def delete_custom_movement(movement_id: int):
    """Delete a custom movement. Can only delete custom movements."""
    deleted = service.delete_custom_movement(movement_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Movement not found or cannot delete seeded movements"
        )
    return {"message": "Movement deleted successfully"}


@router.post("/{movement_id}/videos")
async def add_custom_video(movement_id: int, video: CustomVideoCreate):
    """Add a custom video link to a movement."""
    try:
        created = service.add_custom_video(
            movement_id=movement_id,
            url=video.url,
            title=video.title,
            video_type=video.video_type,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{movement_id}/videos/{video_id}")
async def delete_custom_video(movement_id: int, video_id: int):
    """Delete a custom video link."""
    deleted = service.delete_custom_video(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video deleted successfully"}
