"""Session management endpoints."""

import logging
from datetime import date

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    Request,
    Response,
    status,
)

from rivaflow.api.rate_limit import limiter
from rivaflow.api.response_models import (
    SessionResponse,
    SessionScoreResponse,
)
from rivaflow.core.dependencies import get_current_user, get_session_service
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import AuthorizationError, NotFoundError
from rivaflow.core.models import SessionCreate, SessionUpdate
from rivaflow.core.services.privacy_service import PrivacyService
from rivaflow.core.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _trigger_post_session_insight(user_id: int, session_id: int) -> None:
    """Best-effort AI insight generation after session creation."""
    try:
        from rivaflow.core.services.grapple.ai_insight_service import (
            generate_post_session_insight,
        )

        await generate_post_session_insight(user_id, session_id)
    except Exception:
        logger.debug(
            "Post-session insight generation skipped",
            exc_info=True,
        )


def _trigger_post_session_hooks(user_id: int, session_date: str) -> None:
    """Best-effort milestone check and streak recording after session."""
    try:
        from rivaflow.core.services.milestone_service import MilestoneService
        from rivaflow.core.services.notification_service import (
            NotificationService,
        )

        new_milestones = MilestoneService().check_all_milestones(user_id)
        for ms in new_milestones:
            try:
                NotificationService.create_milestone_notification(
                    user_id, ms.get("milestone_label", "")
                )
            except Exception:
                logger.debug("Milestone notification failed", exc_info=True)
    except Exception:
        logger.debug("Post-session milestone check skipped", exc_info=True)

    try:
        from rivaflow.core.services.notification_service import (
            NotificationService,
        )
        from rivaflow.core.services.streak_service import StreakService

        checkin_date = date.fromisoformat(str(session_date)[:10])
        result = StreakService().record_checkin(
            user_id, checkin_type="session", checkin_date=checkin_date
        )
        if result.get("streak_extended"):
            streak = result.get("checkin_streak") or {}
            current = streak.get("current_streak", 0)
            try:
                NotificationService.create_streak_notification(
                    user_id, "check-in", current
                )
            except Exception:
                logger.debug("Streak notification failed", exc_info=True)
    except Exception:
        logger.debug("Post-session streak recording skipped", exc_info=True)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
@limiter.limit("60/minute")
@route_error_handler("create_session", detail="Failed to create session")
def create_session(
    request: Request,
    session: SessionCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Create a new training session."""
    # Convert SessionRollData models to dicts if present
    session_rolls_dict = None
    if session.session_rolls:
        session_rolls_dict = [roll.model_dump() for roll in session.session_rolls]

    # Convert SessionTechniqueCreate models to dicts if present
    session_techniques_dict = None
    if session.session_techniques:
        session_techniques_dict = [
            tech.model_dump() for tech in session.session_techniques
        ]

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
        attacks_attempted=session.attacks_attempted,
        attacks_successful=session.attacks_successful,
        defenses_attempted=session.defenses_attempted,
        defenses_successful=session.defenses_successful,
    )
    created_session = service.get_session(
        user_id=current_user["id"], session_id=session_id
    )

    # Best-effort background hooks
    background_tasks.add_task(
        _trigger_post_session_insight,
        current_user["id"],
        session_id,
    )
    background_tasks.add_task(
        _trigger_post_session_hooks,
        current_user["id"],
        str(session.session_date),
    )

    return created_session


@router.put("/{session_id}", response_model=SessionResponse)
@limiter.limit("60/minute")
@route_error_handler("update_session", detail="Failed to update session")
def update_session(
    request: Request,
    session_id: int,
    session: SessionUpdate,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Update an existing training session."""
    # Convert SessionRollData models to dicts if present
    session_rolls_dict = None
    if session.session_rolls is not None:
        session_rolls_dict = [roll.model_dump() for roll in session.session_rolls]

    # Convert SessionTechniqueCreate models to dicts if present
    session_techniques_dict = None
    if session.session_techniques is not None:
        session_techniques_dict = [
            tech.model_dump() for tech in session.session_techniques
        ]

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
        visibility_level=(
            session.visibility_level.value if session.visibility_level else None
        ),
        instructor_id=session.instructor_id,
        instructor_name=session.instructor_name,
        session_rolls=session_rolls_dict,
        session_techniques=session_techniques_dict,
        whoop_strain=session.whoop_strain,
        whoop_calories=session.whoop_calories,
        whoop_avg_hr=session.whoop_avg_hr,
        whoop_max_hr=session.whoop_max_hr,
        attacks_attempted=session.attacks_attempted,
        attacks_successful=session.attacks_successful,
        defenses_attempted=session.defenses_attempted,
        defenses_successful=session.defenses_successful,
        needs_review=session.needs_review,
    )
    if not updated:
        raise NotFoundError(f"Session {session_id} not found or access denied")
    return updated


@router.delete("/{session_id}")
@limiter.limit("60/minute")
@route_error_handler("delete_session", detail="Failed to delete session")
def delete_session(
    request: Request,
    session_id: int,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Delete a training session."""
    deleted = service.delete_session(user_id=current_user["id"], session_id=session_id)
    if not deleted:
        raise NotFoundError(f"Session {session_id} not found or access denied")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}", response_model=SessionResponse)
@route_error_handler("get_session", detail="Failed to get session")
def get_session(
    session_id: int,
    apply_privacy: bool = False,
    include_navigation: bool = Query(
        default=True, description="Include previous/next session IDs for navigation"
    ),
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
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


@router.get("/", response_model=list[SessionResponse])
@route_error_handler("list_sessions", detail="Failed to list sessions")
def list_sessions(
    limit: int = Query(default=10, ge=1, le=1000),
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """List recent sessions.

    Args:
        limit: Maximum number of sessions to return (1-1000)
        apply_privacy: If True, apply privacy redaction to each session.
                      Default False for owner access (current single-user mode).
    """
    sessions = service.get_recent_sessions(user_id=current_user["id"], limit=limit)

    if apply_privacy:
        sessions = PrivacyService.redact_sessions_list(
            sessions, default_visibility="private"
        )

    return sessions


@router.get("/range/{start_date}/{end_date}")
@route_error_handler("get_sessions_by_range", detail="Failed to get sessions")
def get_sessions_by_range(
    start_date: date,
    end_date: date,
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
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
        sessions = PrivacyService.redact_sessions_list(
            sessions, default_visibility="private"
        )

    return sessions


@router.get("/autocomplete/data")
@route_error_handler("get_autocomplete_data", detail="Failed to get autocomplete data")
def get_autocomplete_data(
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Get data for autocomplete suggestions."""
    return service.get_autocomplete_data(user_id=current_user["id"])


@router.get("/{session_id}/insights")
@route_error_handler("get_session_insights", detail="Failed to get session insights")
def get_session_insights(
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get Strava-like insights for a specific session."""
    from rivaflow.core.services.session_insight_service import (
        SessionInsightService,
    )

    insight_service = SessionInsightService()
    result = insight_service.get_session_insights(
        user_id=current_user["id"], session_id=session_id
    )
    if not result.get("insights") and result.get("insights") is None:
        raise NotFoundError(f"Session {session_id} not found")
    return result


@router.get("/{session_id}/with-rolls")
@route_error_handler(
    "get_session_with_rolls", detail="Failed to get session with rolls"
)
def get_session_with_rolls(
    session_id: int,
    apply_privacy: bool = False,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Get a session with detailed roll records.

    Args:
        session_id: Session ID
        apply_privacy: If True, apply privacy redaction.
                      Note: detailed_rolls is a SENSITIVE_FIELD and will be
                      excluded unless visibility is "full".
                      Default False for owner access (current single-user mode).
    """
    session = service.get_session_with_rolls(
        user_id=current_user["id"], session_id=session_id
    )
    if not session:
        raise NotFoundError("Session not found")

    if apply_privacy:
        visibility = session.get("visibility_level", "private")
        session = PrivacyService.redact_session(session, visibility=visibility)
        if session is None:
            raise AuthorizationError("Session is private")

    return session


@router.get("/partner/{partner_id}/stats")
@route_error_handler("get_partner_stats", detail="Failed to get partner stats")
def get_partner_stats(
    partner_id: int,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Get training statistics for a specific partner."""
    stats = service.get_partner_stats(user_id=current_user["id"], partner_id=partner_id)
    return stats


# --- Session scoring endpoints ------------------------------------------------


@router.get("/{session_id}/score", response_model=SessionScoreResponse)
@route_error_handler("get_session_score", detail="Failed to get session score")
def get_session_score(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """Get the performance score and breakdown for a session."""
    session = service.get_session(user_id=current_user["id"], session_id=session_id)
    if not session:
        raise NotFoundError(f"Session {session_id} not found")

    return {
        "session_id": session_id,
        "session_score": session.get("session_score"),
        "score_breakdown": session.get("score_breakdown"),
        "score_version": session.get("score_version"),
    }


@router.post("/{session_id}/score/recalculate")
@limiter.limit("30/minute")
@route_error_handler("recalculate_session_score", detail="Failed to recalculate score")
def recalculate_session_score(
    request: Request,
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Force recalculate the performance score for a session."""
    from rivaflow.core.services.session_scoring_service import (
        SessionScoringService,
    )

    scoring = SessionScoringService()
    breakdown = scoring.recalculate_session(current_user["id"], session_id)
    if not breakdown:
        raise NotFoundError(f"Session {session_id} not found")
    return {
        "session_id": session_id,
        "session_score": breakdown["total"],
        "score_breakdown": breakdown,
    }


@router.post("/scores/backfill")
@limiter.limit("5/minute")
@route_error_handler("backfill_scores", detail="Failed to backfill scores")
def backfill_scores(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Score all unscored sessions for the current user."""
    from rivaflow.core.services.session_scoring_service import (
        SessionScoringService,
    )

    scoring = SessionScoringService()
    result = scoring.backfill_user_scores(current_user["id"])
    return result
