"""API routes for daily check-ins."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/checkins", tags=["checkins"])


class TomorrowIntentionUpdate(BaseModel):
    """Update tomorrow's intention."""

    tomorrow_intention: str


@router.get("/today")
def get_today_checkin(current_user: dict = Depends(get_current_user)):
    """Get today's check-in status."""
    repo = CheckinRepository()
    today = date.today()
    checkin = repo.get_checkin(user_id=current_user["id"], check_date=today)

    if not checkin:
        return {"checked_in": False, "date": today.isoformat()}

    return {"checked_in": True, "date": today.isoformat(), **checkin}


@router.get("/week")
def get_week_checkins(current_user: dict = Depends(get_current_user)):
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
def update_tomorrow_intention(
    data: TomorrowIntentionUpdate, current_user: dict = Depends(get_current_user)
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
