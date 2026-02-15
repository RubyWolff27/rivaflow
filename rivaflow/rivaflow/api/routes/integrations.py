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
        from urllib.parse import quote

        safe_error = quote(error, safe="")
        return RedirectResponse(
            f"{frontend_url}/profile?whoop=error&reason={safe_error}"
        )

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
    except ExternalServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync workouts from WHOOP",
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
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )


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
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout or session not found",
        )


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
    except ExternalServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync recovery data from WHOOP",
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
    recs = WhoopRecoveryCacheRepository.get_by_date_range(
        user_id, s_date, s_date + "T23:59:59"
    )
    if not recs:
        # Try day before
        from datetime import timedelta

        try:
            from datetime import date as date_cls

            d = date_cls.fromisoformat(s_date[:10])
            prev = (d - timedelta(days=1)).isoformat()
            recs = WhoopRecoveryCacheRepository.get_by_date_range(
                user_id, prev, prev + "T23:59:59"
            )
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
            "sleep_duration_hours": (
                round(dur_ms / 3_600_000, 1) if dur_ms is not None else None
            ),
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
    wo_source = "linked" if wo else None
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
                wo_source = "date_match"
                # Link it for future lookups
                if wo.get("id"):
                    WhoopWorkoutCacheRepository.link_to_session(wo["id"], session_id)
        except (ValueError, TypeError):
            pass

    if wo:
        zones = wo.get("zone_durations")
        zone_source = "cache" if zones else None
        # Fallback: extract zone_duration from raw_data if not cached directly
        if not zones and wo.get("raw_data"):
            raw = wo["raw_data"]
            if isinstance(raw, dict):
                score = raw.get("score") or {}
                zones = score.get("zone_duration")
                if zones:
                    zone_source = "raw_data"
        # Auto-refresh from WHOOP API if zone data is missing
        if not zones and wo.get("whoop_workout_id"):
            try:
                token = service.get_valid_access_token(user_id)
                fresh = service.client.get_workout_by_id(token, wo["whoop_workout_id"])
                fresh_score = fresh.get("score") or {}
                zones = fresh_score.get("zone_duration")
                if zones:
                    zone_source = "api_refresh"
                    # Update cache for future requests
                    import json

                    from rivaflow.db.database import convert_query, get_connection

                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            convert_query(
                                "UPDATE whoop_workout_cache "
                                "SET zone_durations = ?, raw_data = ?, "
                                "score_state = ? WHERE id = ?"
                            ),
                            (
                                json.dumps(zones),
                                json.dumps(fresh),
                                fresh.get("score_state"),
                                wo["id"],
                            ),
                        )
            except Exception:
                logger.warning(
                    "Auto-refresh failed for workout %s",
                    wo.get("whoop_workout_id"),
                    exc_info=True,
                )
        workout_data = {
            "zone_durations": zones,
            "score_state": wo.get("score_state"),
            "strain": wo.get("strain"),
            "avg_heart_rate": wo.get("avg_heart_rate"),
            "max_heart_rate": wo.get("max_heart_rate"),
            "calories": wo.get("calories"),
            "kilojoules": wo.get("kilojoules"),
            "sport_name": wo.get("sport_name"),
        }
        logger.info(
            "Session %s context: workout=%s score_state=%s "
            "zone_source=%s has_raw=%s",
            session_id,
            wo_source,
            wo.get("score_state"),
            zone_source,
            bool(wo.get("raw_data")),
        )
    else:
        logger.info(
            "Session %s context: no workout found (date=%s)",
            session_id,
            s_date,
        )

    return {"recovery": recovery_data, "workout": workout_data}


@router.get("/whoop/zones/batch")
def get_zones_batch(
    request: Request,
    session_ids: str = Query(..., description="Comma-separated session IDs"),
    current_user: dict = Depends(get_current_user),
):
    """Get HR zone data for multiple sessions at once."""
    _require_whoop_enabled()

    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.repositories.whoop_workout_cache_repo import (
        WhoopWorkoutCacheRepository,
    )

    ids = [int(s.strip()) for s in session_ids.split(",") if s.strip().isdigit()][
        :50
    ]  # cap at 50

    user_id = current_user["id"]

    # Batch ownership check (single query instead of N get_by_id calls)
    owned_ids = SessionRepository.get_owned_ids(user_id, ids)

    # Batch fetch all linked workouts (single query instead of N loops)
    owned_list = [sid for sid in ids if sid in owned_ids]
    workouts_map = WhoopWorkoutCacheRepository.get_by_session_ids(owned_list)

    result: dict[str, dict | None] = {}
    for sid in ids:
        if sid not in owned_ids:
            result[str(sid)] = None
            continue
        wo = workouts_map.get(sid)
        if not wo:
            result[str(sid)] = None
            continue
        zones = wo.get("zone_durations")
        if not zones and wo.get("raw_data"):
            raw = wo["raw_data"]
            if isinstance(raw, dict):
                score = raw.get("score") or {}
                zones = score.get("zone_duration")
        result[str(sid)] = (
            {
                "zone_durations": zones,
                "strain": wo.get("strain"),
                "calories": wo.get("calories"),
                "score_state": wo.get("score_state"),
            }
            if zones or wo.get("score_state")
            else None
        )

    return {"zones": result}


@router.get("/whoop/zones/weekly")
def get_zones_weekly(
    request: Request,
    week_offset: int = Query(0, ge=-52, le=0, description="Weeks back (0=current)"),
    tz: str | None = Query(None, description="IANA timezone"),
    current_user: dict = Depends(get_current_user),
):
    """Get aggregated HR zone totals for a week."""
    _require_whoop_enabled()
    user_id = current_user["id"]

    from datetime import timedelta

    from rivaflow.core.services.report_service import today_in_tz
    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.repositories.whoop_workout_cache_repo import (
        WhoopWorkoutCacheRepository,
    )

    today = today_in_tz(tz)
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)

    sessions = SessionRepository.get_by_date_range(user_id, week_start, week_end)

    zone_keys = [
        "zone_one_milli",
        "zone_two_milli",
        "zone_three_milli",
        "zone_four_milli",
        "zone_five_milli",
    ]
    totals = {k: 0 for k in zone_keys}
    session_count = 0

    for s in sessions:
        wo = WhoopWorkoutCacheRepository.get_by_session_id(s["id"])
        if not wo:
            continue
        zones = wo.get("zone_durations")
        if not zones and wo.get("raw_data"):
            raw = wo["raw_data"]
            if isinstance(raw, dict):
                score = raw.get("score") or {}
                zones = score.get("zone_duration")
        if zones:
            session_count += 1
            for k in zone_keys:
                totals[k] += zones.get(k, 0)

    return {
        "totals": totals,
        "session_count": session_count,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }


@router.post("/whoop/auto-create-sessions")
def set_auto_create(
    body: AutoCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Toggle auto-creation of sessions from WHOOP BJJ workouts."""
    _require_whoop_enabled()
    return service.set_auto_create_sessions(current_user["id"], body.enabled)


@router.post("/whoop/auto-fill-readiness")
def set_auto_fill_readiness(
    body: AutoCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Toggle auto-fill readiness from WHOOP recovery data."""
    _require_whoop_enabled()
    return service.set_auto_fill_readiness(current_user["id"], body.enabled)


@router.delete("/whoop")
def disconnect(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Disconnect WHOOP and clear all synced data."""
    _require_whoop_enabled()
    service.disconnect(current_user["id"])
    return {"disconnected": True}
