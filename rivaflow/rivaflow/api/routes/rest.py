"""Rest day routes."""

from datetime import date

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.streak_service import StreakService
from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/rest", tags=["rest"])


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
