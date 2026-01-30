"""Photo routes."""
from fastapi import APIRouter, Depends
from rivaflow.core.dependencies import get_current_user

router = APIRouter()


@router.get("/photos/activity/session/{session_id}")
async def get_session_photos(session_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get photos for a training session.

    TODO: Implement photo storage and retrieval.
    For now, returns empty array to prevent frontend crashes.
    """
    return []
