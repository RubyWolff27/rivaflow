"""WHOOP integration API routes."""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ExternalServiceError, NotFoundError
from rivaflow.core.services.whoop_service import WhoopService
from rivaflow.core.settings import settings

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)

service = WhoopService()


# ============================================================================
# Feature flag guard
# ============================================================================


def _require_whoop_enabled():
    """Raise 404 if the WHOOP feature flag is off."""
    if not settings.ENABLE_WHOOP_INTEGRATION:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="WHOOP integration is not enabled",
        )


# ============================================================================
# Request / Response models
# ============================================================================


class MatchRequest(BaseModel):
    session_id: int
    workout_cache_id: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/whoop/authorize")
def authorize(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Return the WHOOP OAuth authorization URL."""
    _require_whoop_enabled()
    user_id = current_user["id"]
    url = service.initiate_oauth(user_id)
    return {"authorization_url": url}


@router.get("/whoop/callback")
def callback(
    request: Request,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """Process the OAuth callback from WHOOP.

    This endpoint is NOT JWT-protected — the state token authenticates
    the request.  On success, redirects to the frontend profile page.
    """
    _require_whoop_enabled()
    frontend_url = settings.APP_BASE_URL

    if error:
        logger.warning(f"WHOOP OAuth error: {error}")
        return RedirectResponse(f"{frontend_url}/profile?whoop=error&reason={error}")

    if not code or not state:
        return RedirectResponse(
            f"{frontend_url}/profile?whoop=error&reason=missing_params"
        )

    try:
        service.handle_callback(code, state)
        return RedirectResponse(f"{frontend_url}/profile?whoop=connected")
    except Exception as e:
        logger.error(f"WHOOP callback failed: {e}", exc_info=True)
        return RedirectResponse(
            f"{frontend_url}/profile?whoop=error&reason=callback_failed"
        )


@router.get("/whoop/status")
def get_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Return the user's WHOOP connection status."""
    _require_whoop_enabled()
    return service.get_connection_status(current_user["id"])


@router.post("/whoop/sync")
def sync_workouts(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Trigger a workout sync from WHOOP."""
    _require_whoop_enabled()
    try:
        result = service.sync_workouts(current_user["id"])
        return result
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WHOOP not connected",
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.get("/whoop/workouts")
def get_workouts(
    request: Request,
    session_id: int | None = Query(None),
    session_date: str | None = Query(None),
    class_time: str | None = Query(None),
    duration_mins: int | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get cached WHOOP workouts, optionally matched to a session.

    If session_id is provided, returns workouts matched to that session.
    If session_date + class_time + duration_mins are provided, matches
    by those parameters (for new/unsaved sessions).
    """
    _require_whoop_enabled()
    user_id = current_user["id"]

    try:
        if session_id:
            matches = service.find_matching_workouts(user_id, session_id)
        elif session_date and class_time and duration_mins:
            matches = service.find_matching_workouts_by_params(
                user_id, session_date, class_time, duration_mins
            )
        else:
            # Return recent cached workouts (no matching)
            from datetime import datetime, timedelta

            end = datetime.now(UTC).isoformat()
            start = (datetime.now(UTC) - timedelta(days=7)).isoformat()
            matches = service.workout_cache_repo.get_by_user_and_time_range(
                user_id, start, end
            )

        return {"workouts": matches, "count": len(matches)}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/whoop/match")
def match_workout(
    request: Request,
    body: MatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Link a cached WHOOP workout to a session."""
    _require_whoop_enabled()
    try:
        updated = service.apply_workout_to_session(
            current_user["id"], body.session_id, body.workout_cache_id
        )
        return updated
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/whoop")
def disconnect(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Disconnect WHOOP and clear all synced data."""
    _require_whoop_enabled()
    service.disconnect(current_user["id"])
    return {"disconnected": True}
