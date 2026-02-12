"""API routes for daily check-ins."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.streak_service import StreakService
from rivaflow.core.time_utils import user_today
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.profile_repo import ProfileRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checkins", tags=["checkins"])
limiter = Limiter(key_func=get_remote_address)


def _get_user_tz(user_id: int) -> str | None:
    """Get user's timezone from profile."""
    profile = ProfileRepository.get(user_id)
    return profile.get("timezone") if profile else None


class TomorrowIntentionUpdate(BaseModel):
    """Update tomorrow's intention."""

    tomorrow_intention: str


class MiddayCheckinCreate(BaseModel):
    """Create a midday check-in."""

    energy_level: int = Field(..., ge=1, le=5)
    midday_note: str | None = None


class EveningCheckinCreate(BaseModel):
    """Create an evening check-in."""

    did_not_train: bool = False
    rest_type: str | None = None
    rest_note: str | None = None
    training_quality: int | None = Field(None, ge=1, le=5)
    recovery_note: str | None = None
    tomorrow_intention: str | None = None


@router.get("/today")
@limiter.limit("60/minute")
def get_today_checkin(request: Request, current_user: dict = Depends(get_current_user)):
    """Get today's check-in status (all slots), using user's timezone."""
    repo = CheckinRepository()
    tz = _get_user_tz(current_user["id"])
    today = user_today(tz)
    slots = repo.get_day_checkins(user_id=current_user["id"], check_date=today)
    checked_in = any(v is not None for v in slots.values())

    return {
        "checked_in": checked_in,
        "date": today.isoformat(),
        "morning": slots["morning"],
        "midday": slots["midday"],
        "evening": slots["evening"],
    }


@router.get("/week")
@limiter.limit("60/minute")
def get_week_checkins(request: Request, current_user: dict = Depends(get_current_user)):
    """Get this week's check-ins with slot breakdown."""
    repo = CheckinRepository()
    tz = _get_user_tz(current_user["id"])
    today = user_today(tz)
    week_start = today - timedelta(days=today.weekday())

    checkins = []
    for i in range(7):
        check_date = week_start + timedelta(days=i)
        slots = repo.get_day_checkins(user_id=current_user["id"], check_date=check_date)
        slots_filled = sum(1 for v in slots.values() if v is not None)
        checkins.append(
            {
                "date": check_date.isoformat(),
                "checked_in": slots_filled > 0,
                "checkin_type": (
                    slots["morning"].get("checkin_type") if slots["morning"] else None
                ),
                "slots": slots,
                "slots_filled": slots_filled,
            }
        )

    return {"week_start": week_start.isoformat(), "checkins": checkins}


@router.put("/today/tomorrow")
@limiter.limit("60/minute")
def update_tomorrow_intention(
    request: Request,
    data: TomorrowIntentionUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update tomorrow's intention for today's check-in."""
    repo = CheckinRepository()
    tz = _get_user_tz(current_user["id"])
    today = user_today(tz)

    # Check if any slot exists today
    slots = repo.get_day_checkins(user_id=current_user["id"], check_date=today)
    if not any(v is not None for v in slots.values()):
        raise NotFoundError("No check-in found for today")

    repo.update_tomorrow_intention(
        user_id=current_user["id"],
        check_date=today,
        intention=data.tomorrow_intention,
    )

    return {"success": True, "tomorrow_intention": data.tomorrow_intention}


@router.post("/midday")
@limiter.limit("60/minute")
def create_midday_checkin(
    request: Request,
    data: MiddayCheckinCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create or update midday check-in."""
    repo = CheckinRepository()
    tz = _get_user_tz(current_user["id"])
    today = user_today(tz)
    checkin_id = repo.upsert_midday(
        user_id=current_user["id"],
        check_date=today,
        energy_level=data.energy_level,
        midday_note=data.midday_note,
    )
    # Update check-in streak
    StreakService().record_checkin(
        current_user["id"], checkin_type="midday", checkin_date=today
    )
    return {"success": True, "id": checkin_id}


@router.post("/evening")
@limiter.limit("60/minute")
def create_evening_checkin(
    request: Request,
    data: EveningCheckinCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create or update evening check-in."""
    try:
        repo = CheckinRepository()
        tz = _get_user_tz(current_user["id"])
        today = user_today(tz)
        checkin_id = repo.upsert_evening(
            user_id=current_user["id"],
            check_date=today,
            training_quality=data.training_quality,
            recovery_note=data.recovery_note,
            tomorrow_intention=data.tomorrow_intention,
            did_not_train=data.did_not_train,
            rest_type=data.rest_type,
            rest_note=data.rest_note,
        )
        # Update check-in streak (rest days count too)
        checkin_type = "rest" if data.did_not_train else "evening"
        StreakService().record_checkin(
            current_user["id"], checkin_type=checkin_type, checkin_date=today
        )
        return {"success": True, "id": checkin_id}
    except Exception as e:
        logger.exception(
            "Evening checkin failed for user %s: %s", current_user["id"], e
        )
        raise


@router.get("/yesterday")
@limiter.limit("60/minute")
def get_yesterday_checkin(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get yesterday's check-in data (for tomorrow_intention recall)."""
    repo = CheckinRepository()
    tz = _get_user_tz(current_user["id"])
    yesterday = user_today(tz) - timedelta(days=1)
    slots = repo.get_day_checkins(user_id=current_user["id"], check_date=yesterday)
    return {
        "date": yesterday.isoformat(),
        "morning": slots["morning"],
        "midday": slots["midday"],
        "evening": slots["evening"],
    }
