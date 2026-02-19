"""API routes for daily check-ins."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import (
    get_checkin_service,
    get_current_user,
    get_streak_service,
)
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.checkin_service import CheckinService
from rivaflow.core.services.streak_service import StreakService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/checkins", tags=["checkins"])


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
@route_error_handler("get_today_checkin", detail="Failed to get today's check-in")
def get_today_checkin(
    request: Request,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
):
    """Get today's check-in status (all slots), using user's timezone."""
    today = svc.get_today(current_user["id"])
    slots = svc.get_day_checkins(user_id=current_user["id"], check_date=today)
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
@route_error_handler("get_week_checkins", detail="Failed to get week check-ins")
def get_week_checkins(
    request: Request,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
):
    """Get this week's check-ins with slot breakdown."""
    today = svc.get_today(current_user["id"])
    week_start = today - timedelta(days=today.weekday())

    checkins = []
    for i in range(7):
        check_date = week_start + timedelta(days=i)
        slots = svc.get_day_checkins(user_id=current_user["id"], check_date=check_date)
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
@route_error_handler("update_tomorrow_intention", detail="Failed to update intention")
def update_tomorrow_intention(
    request: Request,
    data: TomorrowIntentionUpdate,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
):
    """Update tomorrow's intention for today's check-in."""
    today = svc.get_today(current_user["id"])

    # Check if any slot exists today
    slots = svc.get_day_checkins(user_id=current_user["id"], check_date=today)
    if not any(v is not None for v in slots.values()):
        raise NotFoundError("No check-in found for today")

    svc.update_tomorrow_intention(
        user_id=current_user["id"],
        check_date=today,
        intention=data.tomorrow_intention,
    )

    return {"tomorrow_intention": data.tomorrow_intention}


@router.post("/midday")
@limiter.limit("60/minute")
@route_error_handler("create_midday_checkin", detail="Failed to create midday check-in")
def create_midday_checkin(
    request: Request,
    data: MiddayCheckinCreate,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
    streak_svc: StreakService = Depends(get_streak_service),
):
    """Create or update midday check-in."""
    today = svc.get_today(current_user["id"])
    checkin_id = svc.upsert_midday(
        user_id=current_user["id"],
        check_date=today,
        energy_level=data.energy_level,
        midday_note=data.midday_note,
    )
    # Update check-in streak
    streak_svc.record_checkin(
        current_user["id"], checkin_type="midday", checkin_date=today
    )
    return {"id": checkin_id}


@router.post("/evening")
@limiter.limit("60/minute")
@route_error_handler(
    "create_evening_checkin", detail="Failed to create evening check-in"
)
def create_evening_checkin(
    request: Request,
    data: EveningCheckinCreate,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
    streak_svc: StreakService = Depends(get_streak_service),
):
    """Create or update evening check-in."""
    today = svc.get_today(current_user["id"])
    checkin_id = svc.upsert_evening(
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
    streak_svc.record_checkin(
        current_user["id"], checkin_type=checkin_type, checkin_date=today
    )
    return {"id": checkin_id}


@router.get("/yesterday")
@limiter.limit("60/minute")
@route_error_handler(
    "get_yesterday_checkin", detail="Failed to get yesterday's check-in"
)
def get_yesterday_checkin(
    request: Request,
    current_user: dict = Depends(get_current_user),
    svc: CheckinService = Depends(get_checkin_service),
):
    """Get yesterday's check-in data (for tomorrow_intention recall)."""
    yesterday = svc.get_today(current_user["id"]) - timedelta(days=1)
    slots = svc.get_day_checkins(user_id=current_user["id"], check_date=yesterday)
    return {
        "date": yesterday.isoformat(),
        "morning": slots["morning"],
        "midday": slots["midday"],
        "evening": slots["evening"],
    }
