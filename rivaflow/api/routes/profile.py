"""Profile management endpoints."""
from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.profile_service import ProfileService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
service = ProfileService()


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
    # Read file content
    content = await file.read()

    # Delegate to service layer for validation and processing
    result = service.upload_profile_photo(
        user_id=current_user["id"],
        file_content=content,
        filename=file.filename or "photo.jpg"
    )

    return result


@router.delete("/photo")
async def delete_profile_photo(current_user: dict = Depends(get_current_user)):
    """
    Delete the current profile photo.

    Removes the file from disk and clears the avatar_url in the database.
    """
    # Delegate to service layer
    result = service.delete_profile_photo(user_id=current_user["id"])
    return result
