"""Profile management endpoints."""
from fastapi import APIRouter, Depends
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
    current_grade: Optional[str] = None
    current_professor: Optional[str] = None
    current_instructor_id: Optional[int] = None
    height_cm: Optional[int] = None
    target_weight_kg: Optional[float] = None
    weekly_sessions_target: Optional[int] = None
    weekly_hours_target: Optional[float] = None
    weekly_rolls_target: Optional[int] = None
    show_streak_on_dashboard: Optional[bool] = None
    show_weekly_goals: Optional[bool] = None


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
        current_grade=profile.current_grade,
        current_professor=profile.current_professor,
        current_instructor_id=profile.current_instructor_id,
        height_cm=profile.height_cm,
        target_weight_kg=profile.target_weight_kg,
        weekly_sessions_target=profile.weekly_sessions_target,
        weekly_hours_target=profile.weekly_hours_target,
        weekly_rolls_target=profile.weekly_rolls_target,
        show_streak_on_dashboard=profile.show_streak_on_dashboard,
        show_weekly_goals=profile.show_weekly_goals,
    )
    return updated
