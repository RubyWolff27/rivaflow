"""Profile management endpoints."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path
import uuid
from datetime import datetime

from rivaflow.core.services.profile_service import ProfileService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError
from rivaflow.db.repositories.user_repo import UserRepository

router = APIRouter()
service = ProfileService()
user_repo = UserRepository()

# Configure upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class ProfileUpdate(BaseModel):
    """Profile update model."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    default_gym: Optional[str] = None
    default_location: Optional[str] = None
    current_grade: Optional[str] = None
    current_professor: Optional[str] = None
    current_instructor_id: Optional[int] = None
    primary_training_type: Optional[str] = None
    height_cm: Optional[int] = None
    target_weight_kg: Optional[float] = None
    weekly_sessions_target: Optional[int] = None
    weekly_hours_target: Optional[float] = None
    weekly_rolls_target: Optional[int] = None
    show_streak_on_dashboard: Optional[bool] = None
    show_weekly_goals: Optional[bool] = None
    avatar_url: Optional[str] = None


@router.get("/")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the user profile."""
    profile = service.get_profile(user_id=current_user["id"])
    if not profile:
        # Return empty profile if none exists
        return {
            "id": 1,
            "first_name": None,
            "last_name": None,
            "date_of_birth": None,
            "age": None,
            "sex": None,
            "city": None,
            "state": None,
            "default_gym": None,
            "current_grade": None,
            "current_professor": None,
        }
    return profile


@router.put("/")
async def update_profile(profile: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update the user profile."""
    updated = service.update_profile(
        user_id=current_user["id"],
        first_name=profile.first_name,
        last_name=profile.last_name,
        date_of_birth=profile.date_of_birth,
        sex=profile.sex,
        city=profile.city,
        state=profile.state,
        default_gym=profile.default_gym,
        default_location=profile.default_location,
        current_grade=profile.current_grade,
        current_professor=profile.current_professor,
        current_instructor_id=profile.current_instructor_id,
        primary_training_type=profile.primary_training_type,
        height_cm=profile.height_cm,
        target_weight_kg=profile.target_weight_kg,
        weekly_sessions_target=profile.weekly_sessions_target,
        weekly_hours_target=profile.weekly_hours_target,
        weekly_rolls_target=profile.weekly_rolls_target,
        show_streak_on_dashboard=profile.show_streak_on_dashboard,
        show_weekly_goals=profile.show_weekly_goals,
    )
    return updated


@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a profile photo.

    Accepts image files (jpg, png, webp, gif) up to 5MB.
    Returns the URL of the uploaded photo.
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # Generate unique filename: user_{user_id}_{timestamp}_{uuid}.{ext}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"user_{current_user['id']}_{timestamp}_{unique_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Update user's avatar_url in database
    avatar_url = f"/uploads/avatars/{filename}"
    user_repo.update_avatar(current_user["id"], avatar_url)

    return {
        "avatar_url": avatar_url,
        "filename": filename,
        "message": "Profile photo uploaded successfully"
    }


@router.delete("/photo")
async def delete_profile_photo(current_user: dict = Depends(get_current_user)):
    """
    Delete the current profile photo.

    Removes the file from disk and clears the avatar_url in the database.
    """
    user = user_repo.get_by_id(current_user["id"])
    if not user or not user.get("avatar_url"):
        raise HTTPException(status_code=404, detail="No profile photo to delete")

    avatar_url = user["avatar_url"]

    # Extract filename from URL (format: /uploads/avatars/filename.jpg)
    if avatar_url.startswith("/uploads/avatars/"):
        filename = avatar_url.replace("/uploads/avatars/", "")
        file_path = UPLOAD_DIR / filename

        # Delete file if it exists
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but continue to clear database entry
                print(f"Error deleting file {file_path}: {e}")

    # Clear avatar_url in database
    user_repo.update_avatar(current_user["id"], None)

    return {"message": "Profile photo deleted successfully"}
