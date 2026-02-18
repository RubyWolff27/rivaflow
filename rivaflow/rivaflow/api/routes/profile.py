"""Profile management endpoints."""

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.api.response_models import ProfileResponse
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.profile_service import ProfileService

router = APIRouter()


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
    target_weight_date: str | None = None
    weekly_sessions_target: int | None = None
    weekly_hours_target: float | None = None
    weekly_rolls_target: int | None = None
    weekly_bjj_sessions_target: int | None = None
    weekly_sc_sessions_target: int | None = None
    weekly_mobility_sessions_target: int | None = None
    show_streak_on_dashboard: bool | None = None
    show_weekly_goals: bool | None = None
    timezone: str | None = None
    avatar_url: str | None = None
    primary_gym_id: int | None = None
    activity_visibility: str | None = None


@router.get("/onboarding-status")
@limiter.limit("120/minute")
@route_error_handler("get_onboarding_status", detail="Failed to get onboarding status")
def get_onboarding_status(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get onboarding checklist status derived from existing data."""
    from rivaflow.db.repositories.readiness_repo import ReadinessRepository
    from rivaflow.db.repositories.session_repo import SessionRepository

    service = ProfileService()
    user_id = current_user["id"]
    profile = service.get_profile(user_id=user_id)

    # Profile completion
    profile_fields = {
        "name": bool(profile and profile.get("first_name")),
        "gym": bool(profile and profile.get("default_gym")),
        "belt": bool(profile and profile.get("current_grade")),
        "dob": bool(profile and profile.get("date_of_birth")),
        "session_goal": bool(profile and profile.get("weekly_sessions_target")),
    }
    filled = sum(1 for v in profile_fields.values() if v)
    total_fields = len(profile_fields)
    missing = [k for k, v in profile_fields.items() if not v]

    has_readiness = ReadinessRepository.get_latest(user_id) is not None
    stats = SessionRepository.get_user_stats(user_id)
    has_session = stats.get("total_sessions", 0) > 0
    has_goals = bool(
        profile
        and (
            profile.get("weekly_sessions_target")
            or profile.get("weekly_hours_target")
            or profile.get("weekly_rolls_target")
        )
    )

    steps = [
        {
            "key": "profile",
            "label": "Fill in your profile",
            "done": filled >= 3,
        },
        {
            "key": "readiness",
            "label": "Log your first daily check-in",
            "done": has_readiness,
        },
        {
            "key": "session",
            "label": "Log your first training session",
            "done": has_session,
        },
        {
            "key": "goals",
            "label": "Set weekly training goals",
            "done": has_goals,
        },
    ]

    completed = sum(1 for s in steps if s["done"])
    return {
        "steps": steps,
        "completed": completed,
        "total": len(steps),
        "all_done": completed == len(steps),
        "profile_completion": {
            "filled": filled,
            "total": total_fields,
            "percentage": round(filled / total_fields * 100),
            "missing": missing,
        },
    }


@router.get("/", response_model=ProfileResponse)
@limiter.limit("120/minute")
@route_error_handler("get_profile", detail="Failed to get profile")
def get_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """Get the user profile."""
    service = ProfileService()
    profile = service.get_profile(user_id=current_user["id"])
    if not profile:
        # Return empty profile if none exists
        return {
            "id": current_user["id"],
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


@router.put("/", response_model=ProfileResponse)
@limiter.limit("30/minute")
@route_error_handler("update_profile", detail="Failed to update profile")
def update_profile(
    request: Request,
    profile: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update the user profile."""
    service = ProfileService()
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
        target_weight_date=profile.target_weight_date,
        weekly_sessions_target=profile.weekly_sessions_target,
        weekly_hours_target=profile.weekly_hours_target,
        weekly_rolls_target=profile.weekly_rolls_target,
        weekly_bjj_sessions_target=profile.weekly_bjj_sessions_target,
        weekly_sc_sessions_target=profile.weekly_sc_sessions_target,
        weekly_mobility_sessions_target=profile.weekly_mobility_sessions_target,
        show_streak_on_dashboard=profile.show_streak_on_dashboard,
        show_weekly_goals=profile.show_weekly_goals,
        timezone=profile.timezone,
        primary_gym_id=profile.primary_gym_id,
        activity_visibility=profile.activity_visibility,
    )
    return updated


@router.post("/photo")
@limiter.limit("30/minute")
@route_error_handler("upload_profile_photo", detail="Failed to upload photo")
async def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a profile photo.

    Accepts image files (jpg, png, webp, gif) up to 5MB.
    Returns the URL of the uploaded photo.
    """
    service = ProfileService()
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
@limiter.limit("30/minute")
@route_error_handler("delete_profile_photo", detail="Failed to delete photo")
def delete_profile_photo(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """
    Delete the current profile photo.

    Removes the file from disk and clears the avatar_url in the database.
    """
    service = ProfileService()
    # Delegate to service layer
    result = service.delete_profile_photo(user_id=current_user["id"])
    return result
