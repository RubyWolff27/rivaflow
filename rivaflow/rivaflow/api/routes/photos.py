"""Photo routes."""

import os
import uuid
from datetime import datetime
from pathlib import Path

import filetype
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.db.repositories import ActivityPhotoRepository

router = APIRouter()
photo_repo = ActivityPhotoRepository()
limiter = Limiter(key_func=get_remote_address)

# Configure upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "uploads" / "activities"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PHOTOS_PER_ACTIVITY = 3


def validate_image_content(content: bytes, filename: str) -> str | None:
    """
    Validate that file content is actually an image using magic bytes.

    Args:
        content: File content bytes
        filename: Original filename

    Returns:
        Error message if invalid, None if valid
    """
    # Use filetype to detect actual image type from content
    kind = filetype.guess(content)

    if kind is None:
        return "File is not a valid image. File content does not match image format."

    # Get detected type (extension without dot)
    detected_type = kind.extension

    # Map allowed types (filetype uses 'jpg' not 'jpeg')
    allowed_types = {"jpg", "jpeg", "png", "webp", "gif"}

    if detected_type not in allowed_types:
        return f"Unsupported image type: {detected_type}. Allowed: {', '.join(allowed_types)}"

    # Verify extension matches content
    file_ext = Path(filename).suffix.lower().lstrip(".")

    # Normalize both to jpeg for comparison
    normalized_detected = "jpeg" if detected_type == "jpg" else detected_type
    normalized_file_ext = "jpeg" if file_ext == "jpg" else file_ext

    if normalized_detected != normalized_file_ext:
        return f"File extension mismatch. File claims to be .{file_ext} but content is {detected_type}"

    return None


@router.post("/photos/upload")
@limiter.limit("10/minute")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    activity_type: str = Form(...),
    activity_id: int = Form(...),
    activity_date: str = Form(...),
    caption: str = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload photo for an activity.

    Accepts image files (jpg, png, webp, gif) up to 5MB.
    Maximum 3 photos per activity.
    """
    # Validate activity type
    if activity_type not in ["session", "readiness", "rest"]:
        raise HTTPException(status_code=400, detail="Invalid activity type")

    # Check photo count limit
    photo_count = photo_repo.count_by_activity(
        current_user["id"], activity_type, activity_id
    )
    if photo_count >= MAX_PHOTOS_PER_ACTIVITY:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PHOTOS_PER_ACTIVITY} photos per activity",
        )

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Validate actual file content (magic bytes check)
    content_error = validate_image_content(content, file.filename or "unknown")
    if content_error:
        raise HTTPException(status_code=400, detail=content_error)

    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    # Generate unique filename: {activity_type}_{user_id}_{timestamp}_{uuid}.{ext}
    # Use full UUID4 to avoid collisions (instead of truncated)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    filename = f"{activity_type}_{current_user['id']}_{timestamp}_{unique_id}{file_ext}"

    # Security: Ensure filename doesn't escape upload directory
    file_path = UPLOAD_DIR / filename
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record
    photo_url = f"/uploads/activities/{filename}"
    photo_id = photo_repo.create(
        user_id=current_user["id"],
        activity_type=activity_type,
        activity_id=activity_id,
        activity_date=activity_date,
        file_path=photo_url,
        file_name=filename,
        file_size=len(content),
        mime_type=file.content_type,
        caption=caption,
        display_order=photo_count + 1,
    )

    return {
        "id": photo_id,
        "file_path": photo_url,
        "filename": filename,
        "caption": caption,
        "message": "Photo uploaded successfully",
    }


@router.get("/photos/activity/{activity_type}/{activity_id}")
async def get_activity_photos(
    activity_type: str,
    activity_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Get photos for an activity (session, readiness, or rest).
    """
    photos = photo_repo.get_by_activity(current_user["id"], activity_type, activity_id)
    return photos


@router.get("/photos/{photo_id}")
async def get_photo(photo_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get photo by ID.
    """
    photo = photo_repo.get_by_id(current_user["id"], photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a photo.
    """
    # Get photo info to delete file
    photo = photo_repo.get_by_id(current_user["id"], photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete from database
    deleted = photo_repo.delete(current_user["id"], photo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete file from filesystem
    try:
        file_path = UPLOAD_DIR / photo["file_name"]
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        # Log error but don't fail the request - database record is already deleted
        print(f"Error deleting file {photo['file_name']}: {e}")

    return {"message": "Photo deleted successfully"}


@router.put("/photos/{photo_id}/caption")
async def update_caption(
    photo_id: int,
    caption: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update photo caption.
    """
    updated = photo_repo.update_caption(current_user["id"], photo_id, caption)
    if not updated:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo = photo_repo.get_by_id(current_user["id"], photo_id)
    return photo
