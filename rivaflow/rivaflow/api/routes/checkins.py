"""API routes for daily check-ins."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/checkins", tags=["checkins"])
limiter = Limiter(key_func=get_remote_address)


class TomorrowIntentionUpdate(BaseModel):
    """Update tomorrow's intention."""

    tomorrow_intention: str


@router.get("/today")
@limiter.limit("60/minute")
def get_today_checkin(request: Request, current_user: dict = Depends(get_current_user)):
    """Get today's check-in status."""
    repo = CheckinRepository()
    today = date.today()
    checkin = repo.get_checkin(user_id=current_user["id"], check_date=today)

    if not checkin:
        return {"checked_in": False, "date": today.isoformat()}

    return {"checked_in": True, "date": today.isoformat(), **checkin}


@router.get("/week")
@limiter.limit("60/minute")
def get_week_checkins(request: Request, current_user: dict = Depends(get_current_user)):
    """Get this week's check-ins."""
    repo = CheckinRepository()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    checkins = []
    for i in range(7):
        check_date = week_start + timedelta(days=i)
        checkin = repo.get_checkin(user_id=current_user["id"], check_date=check_date)
        checkins.append(
            {
                "date": check_date.isoformat(),
                "checked_in": checkin is not None,
                "checkin_type": checkin.get("checkin_type") if checkin else None,
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
    today = date.today()

    # Check if today's check-in exists
    checkin = repo.get_checkin(user_id=current_user["id"], check_date=today)
    if not checkin:
        raise NotFoundError("No check-in found for today")

    # Update tomorrow's intention
    repo.update_tomorrow_intention(
        user_id=current_user["id"],
        check_date=today,
        intention=data.tomorrow_intention,
    )

    return {"success": True, "tomorrow_intention": data.tomorrow_intention}
