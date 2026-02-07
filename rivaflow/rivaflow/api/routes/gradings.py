"""Grading/belt progression endpoints."""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.grading_service import GradingService

router = APIRouter()
service = GradingService()

# Configure upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "uploads" / "gradings"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
async def list_gradings(current_user: dict = Depends(get_current_user)):
    """Get all gradings, ordered by date (newest first)."""
    gradings = service.list_gradings(user_id=current_user["id"])
    return gradings


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_grading(
    grading: GradingCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new grading and update the profile's current_grade."""
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
async def get_latest_grading(current_user: dict = Depends(get_current_user)):
    """Get the most recent grading."""
    grading = service.get_latest_grading(user_id=current_user["id"])
    if not grading:
        return None
    return grading


@router.put("/{grading_id}")
async def update_grading(
    grading_id: int,
    grading: GradingUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a grading by ID."""
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
async def delete_grading(
    grading_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a grading by ID."""
    deleted = service.delete_grading(
        user_id=current_user["id"],
        grading_id=grading_id,
    )
    if not deleted:
        raise NotFoundError("Grading not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/photo", status_code=status.HTTP_201_CREATED)
async def upload_grading_photo(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
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
    file_path = UPLOAD_DIR / filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Return photo URL
    photo_url = f"/uploads/gradings/{filename}"

    return {
        "photo_url": photo_url,
        "filename": filename,
        "message": "Grading photo uploaded successfully",
    }
