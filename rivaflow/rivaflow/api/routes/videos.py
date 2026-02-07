"""Video library endpoints — backed by movement_videos table."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.glossary_service import GlossaryService

router = APIRouter()
service = GlossaryService()


class VideoCreateRequest(BaseModel):
    """Input model for creating a video (writes to movement_videos)."""

    url: str
    title: str | None = None
    movement_id: int | None = None
    video_type: str = Field(default="general")


@router.post("/")
async def add_video(
    video: VideoCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new video linked to a glossary movement."""
    if not video.movement_id:
        raise NotFoundError("movement_id is required to link a video to a movement")
    return service.add_video(
        user_id=current_user["id"],
        movement_id=video.movement_id,
        url=video.url,
        title=video.title,
        video_type=video.video_type,
    )


@router.get("/")
async def list_videos(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """List all videos with pagination."""
    all_videos = service.list_all_videos(
        user_id=current_user["id"], limit=limit, offset=offset
    )
    return {
        "videos": all_videos,
        "total": len(all_videos),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{video_id}")
async def delete_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a video."""
    deleted = service.delete_video(user_id=current_user["id"], video_id=video_id)
    if not deleted:
        raise NotFoundError("Video not found")
    return {"status": "deleted", "video_id": video_id}


@router.get("/{video_id}")
async def get_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """Get a video by ID."""
    video = service.get_video(user_id=current_user["id"], video_id=video_id)
    if not video:
        raise NotFoundError("Video not found")
    return video
