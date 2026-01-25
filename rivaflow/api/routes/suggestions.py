"""Training suggestion endpoints."""
from fastapi import APIRouter
from datetime import date
from typing import Optional

from rivaflow.core.services.suggestion_engine import SuggestionEngine

router = APIRouter()
engine = SuggestionEngine()


@router.get("/today")
async def get_today_suggestion(target_date: Optional[date] = None):
    """Get today's training suggestion."""
    return engine.get_suggestion(target_date)
