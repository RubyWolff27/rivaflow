"""Training suggestion endpoints."""

from datetime import date

from fastapi import APIRouter, Depends

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.suggestion_engine import SuggestionEngine

router = APIRouter()
engine = SuggestionEngine()


@router.get("/today")
async def get_today_suggestion(
    target_date: date | None = None, current_user: dict = Depends(get_current_user)
):
    """Get today's training suggestion."""
    return engine.get_suggestion(user_id=current_user["id"], target_date=target_date)
