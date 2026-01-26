"""API routes for daily check-ins."""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/checkins", tags=["checkins"])


class TomorrowIntentionUpdate(BaseModel):
    """Update tomorrow's intention."""
    tomorrow_intention: str


@router.get("/today")
def get_today_checkin():
    """Get today's check-in status."""
    repo = CheckinRepository()
    today = date.today()
    checkin = repo.get_checkin(today)

    if not checkin:
        return {"checked_in": False, "date": today.isoformat()}

    return {
        "checked_in": True,
        "date": today.isoformat(),
        **checkin
    }


@router.get("/week")
def get_week_checkins():
    """Get this week's check-ins."""
    repo = CheckinRepository()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    checkins = []
    for i in range(7):
        check_date = week_start + timedelta(days=i)
        checkin = repo.get_checkin(check_date)
        checkins.append({
            "date": check_date.isoformat(),
            "checked_in": checkin is not None,
            "checkin_type": checkin.get("checkin_type") if checkin else None,
        })

    return {"week_start": week_start.isoformat(), "checkins": checkins}


@router.put("/today/tomorrow")
def update_tomorrow_intention(data: TomorrowIntentionUpdate):
    """Update tomorrow's intention for today's check-in."""
    repo = CheckinRepository()
    today = date.today()

    # Check if today's check-in exists
    checkin = repo.get_checkin(today)
    if not checkin:
        raise HTTPException(status_code=404, detail="No check-in found for today")

    # Update tomorrow's intention
    repo.update_tomorrow_intention(today, data.tomorrow_intention)

    return {"success": True, "tomorrow_intention": data.tomorrow_intention}
