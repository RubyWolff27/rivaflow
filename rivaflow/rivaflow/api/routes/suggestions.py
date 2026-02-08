"""Training suggestion endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.suggestion_engine import SuggestionEngine

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
engine = SuggestionEngine()


@router.get("/today")
@limiter.limit("60/minute")
def get_today_suggestion(
    request: Request,
    target_date: date | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Get today's training suggestion."""
    return engine.get_suggestion(user_id=current_user["id"], target_date=target_date)
