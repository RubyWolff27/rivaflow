"""Video library endpoints — backed by movement_videos table."""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.glossary_service import GlossaryService

router = APIRouter()


class VideoCreateRequest(BaseModel):
    """Input model for creating a video (writes to movement_videos)."""

    url: str
    title: str | None = None
    movement_id: int | None = None
    video_type: str = Field(default="general")


@router.post("/")
@limiter.limit("120/minute")
@route_error_handler("add_video", detail="Failed to add video")
def add_video(
    request: Request,
    video: VideoCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a new video linked to a glossary movement."""
    service = GlossaryService()
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
@limiter.limit("120/minute")
@route_error_handler("list_videos", detail="Failed to list videos")
def list_videos(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """List all videos with pagination."""
    service = GlossaryService()
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
@limiter.limit("120/minute")
@route_error_handler("delete_video", detail="Failed to delete video")
def delete_video(
    request: Request, video_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a video (admin only)."""
    from fastapi import HTTPException, status

    service = GlossaryService()
    try:
        deleted = service.delete_video(user_id=current_user["id"], video_id=video_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete videos",
        )
    if not deleted:
        raise NotFoundError("Video not found")
    return {"status": "deleted", "video_id": video_id}


@router.get("/{video_id}")
@limiter.limit("120/minute")
@route_error_handler("get_video", detail="Failed to get video")
def get_video(
    request: Request, video_id: int, current_user: dict = Depends(get_current_user)
):
    """Get a video by ID."""
    service = GlossaryService()
    video = service.get_video(user_id=current_user["id"], video_id=video_id)
    if not video:
        raise NotFoundError("Video not found")
    return video
