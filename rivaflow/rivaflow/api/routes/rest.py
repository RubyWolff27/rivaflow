"""Rest day routes."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.streak_service import StreakService
from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/rest", tags=["rest"])


@router.get("/recent")
@limiter.limit("30/minute")
def get_recent_rest_days(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get recent rest day check-ins."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    checkins = CheckinRepository.get_checkins_range(
        current_user["id"], start_date, end_date
    )
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


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def log_rest_day(
    request: Request,
    data: RestDayCreate,
    current_user: dict = Depends(get_current_user),
):
    """Log a rest day."""
    repo = CheckinRepository()
    check_date = (
        date.fromisoformat(data.check_date) if data.check_date else date.today()
    )

    checkin_id = repo.upsert_checkin(
        user_id=current_user["id"],
        check_date=check_date,
        checkin_type="rest",
        rest_type=data.rest_type,
        rest_note=data.rest_note,
    )

    # Update check-in streak (rest days count toward consistency)
    StreakService().record_checkin(
        current_user["id"], checkin_type="rest", checkin_date=check_date
    )

    return {
        "success": True,
        "checkin_id": checkin_id,
        "check_date": check_date.isoformat(),
        "checkin_type": "rest",
        "rest_type": data.rest_type,
    }
