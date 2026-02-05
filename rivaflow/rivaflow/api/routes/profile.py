"""Profile management endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.profile_service import ProfileService

router = APIRouter()
service = ProfileService()


class ProfileUpdate(BaseModel):
    """Profile update model."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    sex: str | None = None
    city: str | None = None
    state: str | None = None
    default_gym: str | None = None
    default_location: str | None = None
    current_grade: str | None = None
    current_professor: str | None = None
    current_instructor_id: int | None = None
    primary_training_type: str | None = None
    height_cm: int | None = None
    target_weight_kg: float | None = None
    weekly_sessions_target: int | None = None
    weekly_hours_target: float | None = None
    weekly_rolls_target: int | None = None
    weekly_bjj_sessions_target: int | None = None
    weekly_sc_sessions_target: int | None = None
    weekly_mobility_sessions_target: int | None = None
    show_streak_on_dashboard: bool | None = None
    show_weekly_goals: bool | None = None
    avatar_url: str | None = None


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
async def update_profile(
    profile: ProfileUpdate, current_user: dict = Depends(get_current_user)
):
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
        weekly_bjj_sessions_target=profile.weekly_bjj_sessions_target,
        weekly_sc_sessions_target=profile.weekly_sc_sessions_target,
        weekly_mobility_sessions_target=profile.weekly_mobility_sessions_target,
        show_streak_on_dashboard=profile.show_streak_on_dashboard,
        show_weekly_goals=profile.show_weekly_goals,
    )
    return updated


@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
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
        filename=file.filename or "photo.jpg",
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
