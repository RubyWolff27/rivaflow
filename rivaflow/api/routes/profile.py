"""Profile management endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.profile_service import ProfileService

router = APIRouter()
service = ProfileService()


class ProfileUpdate(BaseModel):
    """Profile update model."""
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    default_gym: Optional[str] = None
    current_grade: Optional[str] = None


@router.get("/")
async def get_profile():
    """Get the user profile."""
    profile = service.get_profile()
    if not profile:
        # Return empty profile if none exists
        return {
            "id": 1,
            "date_of_birth": None,
            "age": None,
            "sex": None,
            "default_gym": None,
            "current_grade": None,
        }
    return profile


@router.put("/")
async def update_profile(profile: ProfileUpdate):
    """Update the user profile."""
    try:
        updated = service.update_profile(
            date_of_birth=profile.date_of_birth,
            sex=profile.sex,
            default_gym=profile.default_gym,
            current_grade=profile.current_grade,
        )
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
