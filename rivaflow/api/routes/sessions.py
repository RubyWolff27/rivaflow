"""Session management endpoints."""
from fastapi import APIRouter, HTTPException
from datetime import date
from typing import Optional

from rivaflow.core.services.session_service import SessionService
from rivaflow.core.models import SessionCreate, SessionUpdate

router = APIRouter()
service = SessionService()


@router.post("/")
async def create_session(session: SessionCreate):
    """Create a new training session."""
    try:
        # Convert SessionRollData models to dicts if present
        session_rolls_dict = None
        if session.session_rolls:
            session_rolls_dict = [roll.model_dump() for roll in session.session_rolls]

        # Convert SessionTechniqueCreate models to dicts if present
        session_techniques_dict = None
        if session.session_techniques:
            session_techniques_dict = [tech.model_dump() for tech in session.session_techniques]

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
            instructor_id=session.instructor_id,
            instructor_name=session.instructor_name,
            session_rolls=session_rolls_dict,
            session_techniques=session_techniques_dict,
            whoop_strain=session.whoop_strain,
            whoop_calories=session.whoop_calories,
            whoop_avg_hr=session.whoop_avg_hr,
            whoop_max_hr=session.whoop_max_hr,
        )
        created_session = service.get_session(session_id)
        return created_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}")
async def update_session(session_id: int, session: SessionUpdate):
    """Update an existing training session."""
    try:
        # Convert SessionTechniqueCreate models to dicts if present
        session_techniques_dict = None
        if session.session_techniques is not None:
            session_techniques_dict = [tech.model_dump() for tech in session.session_techniques]

        updated = service.update_session(
            session_id=session_id,
            session_date=session.session_date,
            class_type=session.class_type.value if session.class_type else None,
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
            visibility_level=session.visibility_level.value if session.visibility_level else None,
            instructor_id=session.instructor_id,
            instructor_name=session.instructor_name,
            session_techniques=session_techniques_dict,
            whoop_strain=session.whoop_strain,
            whoop_calories=session.whoop_calories,
            whoop_avg_hr=session.whoop_avg_hr,
            whoop_max_hr=session.whoop_max_hr,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        return updated
    except HTTPException:
        raise
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


@router.get("/{session_id}/with-rolls")
async def get_session_with_rolls(session_id: int):
    """Get a session with detailed roll records."""
    session = service.get_session_with_rolls(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/partner/{partner_id}/stats")
async def get_partner_stats(partner_id: int):
    """Get training statistics for a specific partner."""
    try:
        stats = service.get_partner_stats(partner_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
