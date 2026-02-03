"""Training suggestion endpoints."""
from fastapi import APIRouter, Depends
from datetime import date
from typing import Optional

from rivaflow.core.services.suggestion_engine import SuggestionEngine
from rivaflow.core.dependencies import get_current_user

router = APIRouter()
engine = SuggestionEngine()


@router.get("/today")
async def get_today_suggestion(target_date: Optional[date] = None, current_user: dict = Depends(get_current_user)):
    """Get today's training suggestion."""
    return engine.get_suggestion(user_id=current_user["id"], target_date=target_date)
