"""Video library endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from rivaflow.core.services.video_service import VideoService
from rivaflow.core.models import VideoCreate
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
service = VideoService()


@router.post("/")
async def add_video(video: VideoCreate, current_user: dict = Depends(get_current_user)):
    """Add a new video."""
    # Convert technique_id to technique_name if provided
    technique_name = None
    if video.technique_id:
        from rivaflow.db.repositories import TechniqueRepository
        tech_repo = TechniqueRepository()
        tech = tech_repo.get_by_id(video.technique_id)
        if tech:
            technique_name = tech["name"]

    # Convert timestamps to dict format
    timestamps = None
    if video.timestamps:
        timestamps = [{"time": ts.time, "label": ts.label} for ts in video.timestamps]

    video_id = service.add_video(
        user_id=current_user["id"],
        url=video.url,
        title=video.title,
        timestamps=timestamps,
        technique_name=technique_name,
    )
    created_video = service.get_video(user_id=current_user["id"], video_id=video_id)
    return created_video


@router.get("/")
async def list_videos(
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List all videos with pagination."""
    all_videos = service.list_all_videos(user_id=current_user["id"])
    total = len(all_videos)
    videos = all_videos[offset:offset + limit]

    return {
        "videos": videos,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/technique/{technique_name}")
async def get_videos_by_technique(technique_name: str, current_user: dict = Depends(get_current_user)):
    """Get videos for a specific technique."""
    return service.list_videos_by_technique(user_id=current_user["id"], technique_name=technique_name)


@router.get("/search")
async def search_videos(q: str = Query(..., min_length=2), current_user: dict = Depends(get_current_user)):
    """Search videos by title or URL."""
    return service.search_videos(user_id=current_user["id"], query=q)


@router.delete("/{video_id}")
async def delete_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a video."""
    service.delete_video(user_id=current_user["id"], video_id=video_id)
    return {"status": "deleted", "video_id": video_id}


@router.get("/{video_id}")
async def get_video(video_id: int, current_user: dict = Depends(get_current_user)):
    """Get a video by ID."""
    video = service.get_video(user_id=current_user["id"], video_id=video_id)
    if not video:
        raise NotFoundError("Video not found")
    return video
