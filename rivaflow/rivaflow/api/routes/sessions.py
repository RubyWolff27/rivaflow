"""Session management endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import AuthorizationError, NotFoundError
from rivaflow.core.models import SessionCreate, SessionUpdate
from rivaflow.core.services.privacy_service import PrivacyService
from rivaflow.core.services.session_service import SessionService

router = APIRouter()
service = SessionService()
limiter = Limiter(key_func=get_remote_address)


@router.post("/")
@limiter.limit("60/minute")
async def create_session(
    request: Request,
    session: SessionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new training session."""
    # Convert SessionRollData models to dicts if present
    session_rolls_dict = None
    if session.session_rolls:
        session_rolls_dict = [roll.model_dump() for roll in session.session_rolls]

    # Convert SessionTechniqueCreate models to dicts if present
    session_techniques_dict = None
    if session.session_techniques:
        session_techniques_dict = [tech.model_dump() for tech in session.session_techniques]

    session_id = service.create_session(
        user_id=current_user["id"],
        session_date=session.session_date,
        class_time=session.class_time,
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
    created_session = service.get_session(user_id=current_user["id"], session_id=session_id)
    return created_session


@router.put("/{session_id}")
@limiter.limit("60/minute")
async def update_session(
    request: Request,
    session_id: int,
    session: SessionUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing training session."""
    try:
        # Convert SessionTechniqueCreate models to dicts if present
        session_techniques_dict = None
        if session.session_techniques is not None:
            session_techniques_dict = [tech.model_dump() for tech in session.session_techniques]

        updated = service.update_session(
            user_id=current_user["id"],
            session_id=session_id,
            session_date=session.session_date,
            class_time=session.class_time,
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
            visibility_level=(session.visibility_level.value if session.visibility_level else None),
            instructor_id=session.instructor_id,
            instructor_name=session.instructor_name,
            session_techniques=session_techniques_dict,
            whoop_strain=session.whoop_strain,
            whoop_calories=session.whoop_calories,
            whoop_avg_hr=session.whoop_avg_hr,
            whoop_max_hr=session.whoop_max_hr,
        )
        if not updated:
            raise NotFoundError(f"Session {session_id} not found or access denied")
        return updated
    except HTTPException:
        raise


@router.delete("/{session_id}")
@limiter.limit("60/minute")
async def delete_session(
    request: Request, session_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a training session."""
    deleted = service.delete_session(user_id=current_user["id"], session_id=session_id)
    if not deleted:
        raise NotFoundError(f"Session {session_id} not found or access denied")
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}")
async def get_session(
    session_id: int,
    apply_privacy: bool = False,
    include_navigation: bool = Query(
        default=True, description="Include previous/next session IDs for navigation"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Get a session by ID with optional navigation info.

    Args:
        session_id: Session ID
        apply_privacy: If True, apply privacy redaction based on session's visibility_level.
                      Default False for owner access (current single-user mode).
                      Future: Will be True when viewer_id != owner_id.
        include_navigation: If True, include previous_session_id and next_session_id for navigation.
    """
    session = service.get_session(user_id=current_user["id"], session_id=session_id)
    if not session:
        raise NotFoundError(f"Session {session_id} not found or access denied")

    # Apply privacy redaction if requested (for future social features)
    if apply_privacy:
        visibility = session.get("visibility_level", "private")
        session = PrivacyService.redact_session(session, visibility=visibility)
        if session is None:
            raise AuthorizationError("Session is private")

    # Add navigation info for easier browsing
    if include_navigation:
        navigation = service.get_adjacent_sessions(current_user["id"], session_id)
        session["navigation"] = navigation

    return session


@router.get("/")
async def list_sessions(
    limit: int = Query(default=10, ge=1, le=1000),
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """List recent sessions.

    Args:
        limit: Maximum number of sessions to return (1-1000)
        apply_privacy: If True, apply privacy redaction to each session.
                      Default False for owner access (current single-user mode).
    """
    sessions = service.get_recent_sessions(user_id=current_user["id"], limit=limit)

    if apply_privacy:
        sessions = PrivacyService.redact_sessions_list(sessions, default_visibility="private")

    return sessions


@router.get("/range/{start_date}/{end_date}")
async def get_sessions_by_range(
    start_date: date,
    end_date: date,
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get sessions within a date range.

    Args:
        start_date: Range start date
        end_date: Range end date
        apply_privacy: If True, apply privacy redaction to each session.
                      Default False for owner access (current single-user mode).
    """
    sessions = service.get_sessions_by_date_range(
        user_id=current_user["id"], start_date=start_date, end_date=end_date
    )

    if apply_privacy:
        sessions = PrivacyService.redact_sessions_list(sessions, default_visibility="private")

    return sessions


@router.get("/autocomplete/data")
async def get_autocomplete_data(current_user: dict = Depends(get_current_user)):
    """Get data for autocomplete suggestions."""
    return service.get_autocomplete_data(user_id=current_user["id"])


@router.get("/{session_id}/with-rolls")
async def get_session_with_rolls(
    session_id: int,
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get a session with detailed roll records.

    Args:
        session_id: Session ID
        apply_privacy: If True, apply privacy redaction.
                      Note: detailed_rolls is a SENSITIVE_FIELD and will be
                      excluded unless visibility is "full".
                      Default False for owner access (current single-user mode).
    """
    session = service.get_session_with_rolls(user_id=current_user["id"], session_id=session_id)
    if not session:
        raise NotFoundError("Session not found")

    if apply_privacy:
        visibility = session.get("visibility_level", "private")
        session = PrivacyService.redact_session(session, visibility=visibility)
        if session is None:
            raise AuthorizationError("Session is private")

    return session


@router.get("/partner/{partner_id}/stats")
async def get_partner_stats(partner_id: int, current_user: dict = Depends(get_current_user)):
    """Get training statistics for a specific partner."""
    stats = service.get_partner_stats(user_id=current_user["id"], partner_id=partner_id)
    return stats
