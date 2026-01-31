"""Photo routes."""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from rivaflow.core.dependencies import get_current_user

router = APIRouter()


@router.post("/photos/upload")
async def upload_photo(
    file: UploadFile = File(...),
    activity_type: str = Form(...),
    activity_id: int = Form(...),
    activity_date: str = Form(...),
    caption: str = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload photo for an activity.

    TODO: Implement photo storage (S3, Cloudinary, or local filesystem).
    For beta, this returns a clear "Coming Soon" message.
    """
    raise HTTPException(
        status_code=501,
        detail="Photo upload is coming soon! This feature is in development."
    )


@router.get("/photos/activity/{activity_type}/{activity_id}")
async def get_activity_photos(
    activity_type: str,
    activity_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Get photos for an activity (session, readiness, or rest).

    TODO: Implement photo storage and retrieval.
    For now, returns empty array to prevent frontend crashes.
    """
    return []


@router.get("/photos/{photo_id}")
async def get_photo(photo_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get photo by ID.

    TODO: Implement photo retrieval.
    """
    raise HTTPException(
        status_code=404,
        detail="Photo not found"
    )


@router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a photo.

    TODO: Implement photo deletion.
    """
    raise HTTPException(
        status_code=501,
        detail="Photo deletion is coming soon!"
    )


@router.put("/photos/{photo_id}/caption")
async def update_caption(
    photo_id: int,
    caption: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update photo caption.

    TODO: Implement caption update.
    """
    raise HTTPException(
        status_code=501,
        detail="Photo caption editing is coming soon!"
    )
