"""Video library endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional

from rivaflow.core.services.video_service import VideoService
from rivaflow.core.models import VideoCreate

router = APIRouter()
service = VideoService()


@router.post("/")
async def add_video(video: VideoCreate):
    """Add a new video."""
    try:
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
            url=video.url,
            title=video.title,
            timestamps=timestamps,
            technique_name=technique_name,
        )
        created_video = service.get_video(video_id)
        return created_video
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_videos():
    """List all videos."""
    return service.list_all_videos()


@router.get("/technique/{technique_name}")
async def get_videos_by_technique(technique_name: str):
    """Get videos for a specific technique."""
    return service.list_videos_by_technique(technique_name)


@router.get("/search")
async def search_videos(q: str):
    """Search videos by title or URL."""
    return service.search_videos(q)


@router.delete("/{video_id}")
async def delete_video(video_id: int):
    """Delete a video."""
    try:
        service.delete_video(video_id)
        return {"status": "deleted", "video_id": video_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}")
async def get_video(video_id: int):
    """Get a video by ID."""
    video = service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
