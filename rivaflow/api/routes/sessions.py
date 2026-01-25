"""Session management endpoints."""
from fastapi import APIRouter, HTTPException
from datetime import date
from typing import Optional

from rivaflow.core.services.session_service import SessionService
from rivaflow.core.models import SessionCreate

router = APIRouter()
service = SessionService()


@router.post("/")
async def create_session(session: SessionCreate):
    """Create a new training session."""
    try:
        session_id = service.create_session(
            session_date=session.session_date,
            class_type=session.class_type.value,
            gym_name=session.gym_name,
            location=session.location,
            duration_mins=session.duration_mins,
            intensity=session.intensity,
            rolls=session.rolls,
            submissions_for=session.submissions_for,
            submissions_against=session.submissions_against,
            partners=session.partners,
            techniques=session.techniques,
            notes=session.notes,
            visibility_level=session.visibility_level.value,
        )
        created_session = service.get_session(session_id)
        return created_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: int):
    """Get a session by ID."""
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/")
async def list_sessions(limit: int = 10):
    """List recent sessions."""
    return service.get_recent_sessions(limit)


@router.get("/range/{start_date}/{end_date}")
async def get_sessions_by_range(start_date: date, end_date: date):
    """Get sessions within a date range."""
    return service.get_sessions_by_date_range(start_date, end_date)


@router.get("/autocomplete/data")
async def get_autocomplete_data():
    """Get data for autocomplete suggestions."""
    return service.get_autocomplete_data()
