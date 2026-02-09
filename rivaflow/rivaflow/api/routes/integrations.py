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


class AutoCreateRequest(BaseModel):
    enabled: bool


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
        return RedirectResponse(f"{frontend_url}/profile?whoop=error&reason=missing_params")

    try:
        service.handle_callback(code, state)
        return RedirectResponse(f"{frontend_url}/profile?whoop=connected")
    except Exception as e:
        logger.error(f"WHOOP callback failed: {e}", exc_info=True)
        return RedirectResponse(f"{frontend_url}/profile?whoop=error&reason=callback_failed")


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
    days: int = Query(7, ge=1, le=90, description="Days to sync (1-90)"),
    current_user: dict = Depends(get_current_user),
):
    """Trigger a workout sync from WHOOP."""
    _require_whoop_enabled()
    try:
        result = service.sync_workouts(current_user["id"], days_back=days)
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
            matches = service.workout_cache_repo.get_by_user_and_time_range(user_id, start, end)

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


@router.post("/whoop/sync-recovery")
def sync_recovery(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="Days to sync (1-90)"),
    current_user: dict = Depends(get_current_user),
):
    """Trigger a recovery/sleep data sync from WHOOP."""
    _require_whoop_enabled()
    try:
        result = service.sync_recovery(current_user["id"], days_back=days)
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


@router.get("/whoop/recovery/latest")
def get_latest_recovery(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get the latest WHOOP recovery data."""
    _require_whoop_enabled()
    try:
        data = service.get_latest_recovery(current_user["id"])
        return data or {"message": "No recovery data available"}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WHOOP not connected",
        )


@router.get("/whoop/scope-check")
def scope_check(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Check if the user's WHOOP scopes need re-authorization."""
    _require_whoop_enabled()
    return service.check_scope_compatibility(current_user["id"])


@router.get("/whoop/readiness/auto-fill")
def readiness_auto_fill(
    request: Request,
    date: str = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
):
    """Get auto-fill readiness values from WHOOP recovery data."""
    _require_whoop_enabled()
    if not date:
        from datetime import date as date_cls

        date = date_cls.today().isoformat()
    try:
        result = service.apply_recovery_to_readiness(current_user["id"], date)
        if result is None:
            return {"auto_fill": None, "message": "No WHOOP data for this date"}
        return {"auto_fill": result}
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WHOOP not connected",
        )


@router.get("/whoop/session/{session_id}/context")
def get_session_context(
    request: Request,
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get WHOOP recovery context for a specific session."""
    _require_whoop_enabled()
    user_id = current_user["id"]

    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.repositories.whoop_recovery_cache_repo import (
        WhoopRecoveryCacheRepository,
    )
    from rivaflow.db.repositories.whoop_workout_cache_repo import (
        WhoopWorkoutCacheRepository,
    )

    session = SessionRepository.get_by_id(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    s_date = str(session.get("session_date", ""))
    if not s_date:
        return {"recovery": None, "workout": None}

    # Find recovery for session date (or day before)
    recovery_data = None
    recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, s_date, s_date + "T23:59:59")
    if not recs:
        # Try day before
        from datetime import timedelta

        try:
            from datetime import date as date_cls

            d = date_cls.fromisoformat(s_date[:10])
            prev = (d - timedelta(days=1)).isoformat()
            recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, prev, prev + "T23:59:59")
        except (ValueError, TypeError):
            pass

    if recs:
        rec = recs[-1]
        dur_ms = rec.get("sleep_duration_ms")
        rem_ms = rec.get("rem_sleep_ms")
        sws_ms = rec.get("slow_wave_ms")
        recovery_data = {
            "score": rec.get("recovery_score"),
            "hrv_ms": rec.get("hrv_ms"),
            "resting_hr": rec.get("resting_hr"),
            "sleep_performance": rec.get("sleep_performance"),
            "sleep_duration_hours": (round(dur_ms / 3_600_000, 1) if dur_ms is not None else None),
            "rem_pct": (
                round(rem_ms / dur_ms * 100, 1)
                if rem_ms is not None and dur_ms and dur_ms > 0
                else None
            ),
            "sws_pct": (
                round(sws_ms / dur_ms * 100, 1)
                if sws_ms is not None and dur_ms and dur_ms > 0
                else None
            ),
        }

    # Find workout linked to session (or fall back to date match)
    workout_data = None
    wo = WhoopWorkoutCacheRepository.get_by_session_id(session_id)
    if not wo:
        # Fall back: find workout on same day
        from datetime import timedelta

        try:
            from datetime import date as date_cls

            d = date_cls.fromisoformat(s_date[:10])
            day_start = d.isoformat() + "T00:00:00"
            day_end = (d + timedelta(days=1)).isoformat() + "T00:00:00"
            candidates = WhoopWorkoutCacheRepository.get_by_user_and_time_range(
                user_id, day_start, day_end
            )
            if candidates:
                wo = candidates[0]
                # Link it for future lookups
                if wo.get("id"):
                    WhoopWorkoutCacheRepository.link_to_session(wo["id"], session_id)
        except (ValueError, TypeError):
            pass

    if wo:
        zones = wo.get("zone_durations")
        # Fallback: extract zone_duration from raw_data if not cached directly
        if not zones and wo.get("raw_data"):
            raw = wo["raw_data"]
            if isinstance(raw, dict):
                score = raw.get("score") or {}
                zones = score.get("zone_duration")
        if zones:
            workout_data = {
                "zone_durations": zones,
            }

    return {"recovery": recovery_data, "workout": workout_data}


@router.post("/whoop/auto-create-sessions")
def set_auto_create(
    body: AutoCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Toggle auto-creation of sessions from WHOOP BJJ workouts."""
    _require_whoop_enabled()
    return service.set_auto_create_sessions(current_user["id"], body.enabled)


@router.delete("/whoop")
def disconnect(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Disconnect WHOOP and clear all synced data."""
    _require_whoop_enabled()
    service.disconnect(current_user["id"])
    return {"disconnected": True}
