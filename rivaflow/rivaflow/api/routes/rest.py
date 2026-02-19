"""Rest day routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import (
    get_checkin_service,
    get_current_user,
    get_streak_service,
)
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.checkin_service import CheckinService
from rivaflow.core.services.streak_service import StreakService

router = APIRouter(prefix="/rest", tags=["rest"])


@router.get("/recent")
@limiter.limit("30/minute")
@route_error_handler("get_recent_rest_days", detail="Failed to get rest days")
def get_recent_rest_days(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    checkin_svc: CheckinService = Depends(get_checkin_service),
):
    """Get recent rest day check-ins."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    checkins = checkin_svc.get_checkins_range(current_user["id"], start_date, end_date)
    rest_days = [c for c in checkins if c["checkin_type"] == "rest"]
    return [
        {
            "id": r["id"],
            "rest_date": r["check_date"],
            "rest_type": r.get("rest_type"),
            "rest_note": r.get("rest_note"),
            "tomorrow_intention": r.get("tomorrow_intention"),
            "created_at": r["created_at"],
        }
        for r in rest_days
    ]


class RestDayCreate(BaseModel):
    """Create a rest day check-in."""

    rest_type: str | None = None  # active, full, injury, sick, travel, life
    rest_note: str | None = None
    check_date: str | None = None  # ISO date string, defaults to today
    tomorrow_intention: str | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
@route_error_handler("log_rest_day", detail="Failed to log rest day")
def log_rest_day(
    request: Request,
    data: RestDayCreate,
    current_user: dict = Depends(get_current_user),
    repo: CheckinService = Depends(get_checkin_service),
    streak_svc: StreakService = Depends(get_streak_service),
):
    """Log a rest day."""
    check_date = (
        date.fromisoformat(data.check_date) if data.check_date else date.today()
    )

    checkin_id = repo.upsert_checkin(
        user_id=current_user["id"],
        check_date=check_date,
        checkin_type="rest",
        rest_type=data.rest_type,
        rest_note=data.rest_note,
        tomorrow_intention=data.tomorrow_intention,
    )

    # Update check-in streak (rest days count toward consistency)
    streak_svc.record_checkin(
        current_user["id"], checkin_type="rest", checkin_date=check_date
    )

    return {
        "checkin_id": checkin_id,
        "check_date": check_date.isoformat(),
        "checkin_type": "rest",
        "rest_type": data.rest_type,
    }


@router.get("/by-date/{rest_date}")
@limiter.limit("30/minute")
@route_error_handler("get_rest_by_date", detail="Failed to get rest day")
def get_rest_by_date(
    request: Request,
    rest_date: str,
    current_user: dict = Depends(get_current_user),
    checkin_svc: CheckinService = Depends(get_checkin_service),
):
    """Get a rest day check-in by date."""
    try:
        check_date = date.fromisoformat(rest_date)
    except ValueError:
        raise ValidationError("Invalid date format")

    checkin = checkin_svc.get_checkin(
        current_user["id"], check_date, checkin_slot="morning"
    )
    if not checkin or checkin["checkin_type"] != "rest":
        raise NotFoundError("Rest day not found")

    return {
        "id": checkin["id"],
        "rest_date": checkin["check_date"],
        "rest_type": checkin.get("rest_type"),
        "rest_note": checkin.get("rest_note"),
        "tomorrow_intention": checkin.get("tomorrow_intention"),
        "created_at": checkin["created_at"],
    }


@router.delete("/{checkin_id}", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
@route_error_handler("delete_rest_day", detail="Failed to delete rest day")
def delete_rest_day(
    request: Request,
    checkin_id: int,
    current_user: dict = Depends(get_current_user),
    repo: CheckinService = Depends(get_checkin_service),
):
    """Delete a rest day check-in."""
    # Verify it exists and is a rest-type checkin
    checkin = repo.get_checkin_by_id(current_user["id"], checkin_id)
    if not checkin:
        raise NotFoundError("Rest day not found")
    if checkin["checkin_type"] != "rest":
        raise ValidationError("Not a rest day check-in")

    repo.delete_checkin(current_user["id"], checkin_id)
    return {"deleted_id": checkin_id}
