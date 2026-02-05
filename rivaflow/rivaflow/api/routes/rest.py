"""Rest day routes."""

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.db.repositories.checkin_repo import CheckinRepository

router = APIRouter(prefix="/rest", tags=["rest"])


class RestDayCreate(BaseModel):
    """Create a rest day check-in."""

    rest_type: str | None = None  # active, passive, injury
    rest_note: str | None = None
    check_date: str | None = None  # ISO date string, defaults to today


@router.post("/")
def log_rest_day(data: RestDayCreate, current_user: dict = Depends(get_current_user)):
    """Log a rest day."""
    repo = CheckinRepository()
    check_date = date.fromisoformat(data.check_date) if data.check_date else date.today()

    checkin_id = repo.upsert_checkin(
        user_id=current_user["id"],
        check_date=check_date,
        checkin_type="rest",
        rest_type=data.rest_type,
        rest_note=data.rest_note,
    )

    return {
        "success": True,
        "checkin_id": checkin_id,
        "check_date": check_date.isoformat(),
        "checkin_type": "rest",
        "rest_type": data.rest_type,
    }
