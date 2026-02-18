"""Grading/belt progression endpoints."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.grading_service import GradingService
from rivaflow.core.services.storage_service import get_storage

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class GradingCreate(BaseModel):
    """Grading creation model."""

    grade: str
    date_graded: str
    professor: str | None = None
    instructor_id: int | None = None
    notes: str | None = None
    photo_url: str | None = None


class GradingUpdate(BaseModel):
    """Grading update model."""

    grade: str | None = None
    date_graded: str | None = None
    professor: str | None = None
    instructor_id: int | None = None
    notes: str | None = None
    photo_url: str | None = None


@router.get("/")
@limiter.limit("120/minute")
@route_error_handler("list_gradings", detail="Failed to list gradings")
def list_gradings(request: Request, current_user: dict = Depends(get_current_user)):
    """Get all gradings, ordered by date (newest first)."""
    service = GradingService()
    gradings = service.list_gradings(user_id=current_user["id"])
    return gradings


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
@route_error_handler("create_grading", detail="Failed to create grading")
def create_grading(
    request: Request,
    grading: GradingCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new grading and update the profile's current_grade."""
    service = GradingService()
    created = service.create_grading(
        user_id=current_user["id"],
        grade=grading.grade,
        date_graded=grading.date_graded,
        professor=grading.professor,
        instructor_id=grading.instructor_id,
        notes=grading.notes,
        photo_url=grading.photo_url,
    )
    return created


@router.get("/latest")
@limiter.limit("120/minute")
@route_error_handler("get_latest_grading", detail="Failed to get latest grading")
def get_latest_grading(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get the most recent grading."""
    service = GradingService()
    grading = service.get_latest_grading(user_id=current_user["id"])
    if not grading:
        return None
    return grading


@router.put("/{grading_id}")
@limiter.limit("30/minute")
@route_error_handler("update_grading", detail="Failed to update grading")
def update_grading(
    request: Request,
    grading_id: int,
    grading: GradingUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a grading by ID."""
    service = GradingService()
    try:
        updated = service.update_grading(
            user_id=current_user["id"],
            grading_id=grading_id,
            grade=grading.grade,
            date_graded=grading.date_graded,
            professor=grading.professor,
            instructor_id=grading.instructor_id,
            notes=grading.notes,
            photo_url=grading.photo_url,
        )
        if not updated:
            raise NotFoundError("Grading not found")
        return updated
    except HTTPException:
        raise


@router.delete("/{grading_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_grading", detail="Failed to delete grading")
def delete_grading(
    request: Request, grading_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a grading by ID."""
    service = GradingService()
    deleted = service.delete_grading(
        user_id=current_user["id"],
        grading_id=grading_id,
    )
    if not deleted:
        raise NotFoundError("Grading not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/photo", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
@route_error_handler("upload_grading_photo", detail="Failed to upload grading photo")
async def upload_grading_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a grading photo (belt certificate, etc.).

    Accepts image files (jpg, png, webp, gif) up to 5MB.
    Returns the URL of the uploaded photo.
    """
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

    # Generate unique filename: grading_{user_id}_{timestamp}_{uuid}.{ext}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"grading_{current_user['id']}_{timestamp}_{unique_id}{file_ext}"

    # Upload via storage service (local or S3/R2)
    storage = get_storage()
    photo_url = storage.upload("gradings", filename, content)

    return {
        "photo_url": photo_url,
        "filename": filename,
        "message": "Grading photo uploaded successfully",
    }
