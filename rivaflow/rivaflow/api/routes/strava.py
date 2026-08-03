"""Strava integration endpoints.

Mounted at /api/v1/integrations/strava. Replaces the capture path lost when the
Mac-side Garmin push job died with the device — a Wahoo (or any tracker that
auto-uploads to Strava) now reaches RivaFlow through Strava's API.

- GET  /authorize   — build the consent URL
- GET  /callback    — OAuth redirect target (browser, not XHR)
- GET  /status      — connection state for the settings screen
- POST /sync        — pull recent activities
- POST /backfill    — pull an explicit date range (this is the July repair)
- GET  /importable  — unlinked activities plus their suggested class type
- POST /import      — turn one cached activity into a session
- POST /dismiss     — hide an activity from the import list
- POST /auto-create-sessions — toggle auto-creation
- DELETE /          — disconnect
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user, require_write_scope
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.strava_service import StravaService
from rivaflow.core.settings import settings
from rivaflow.db.repositories.strava_repo import StravaRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/strava", tags=["strava"])


class AutoCreateToggle(BaseModel):
    enabled: bool


class ImportRequest(BaseModel):
    activity_cache_id: int


class DismissRequest(BaseModel):
    activity_cache_id: int
    dismissed: bool = True


class BackfillRequest(BaseModel):
    """An explicit date range to re-pull. Inclusive of both endpoints."""

    start_date: str = Field(description="ISO date, e.g. 2026-07-01")
    end_date: str = Field(description="ISO date, e.g. 2026-07-31")
    auto_create: bool | None = Field(
        default=None,
        description="Override the connection's auto-create preference for this run.",
    )


def _parse_day(value: str, end_of_day: bool = False) -> datetime:
    try:
        day = datetime.fromisoformat(value).date()
    except ValueError as exc:
        raise ValidationError(
            f"Invalid date '{value}' — expected ISO YYYY-MM-DD"
        ) from exc
    moment = time.max if end_of_day else time.min
    return datetime.combine(day, moment, tzinfo=UTC)


@router.get("/status")
@route_error_handler("strava_status", detail="Failed to fetch Strava status")
def status(current_user: dict = Depends(get_current_user)) -> dict:
    """Connection state — drives the Connected Devices card."""
    return StravaService.get_status(current_user["id"])


@router.get("/authorize")
@route_error_handler("strava_authorize", detail="Failed to build Strava authorize URL")
def authorize(current_user: dict = Depends(get_current_user)) -> dict:
    """Consent URL for the connect button."""
    return {"authorization_url": StravaService.build_authorize_url(current_user["id"])}


@router.get("/callback")
@route_error_handler("strava_callback", detail="Strava authorisation failed")
def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    scope: str | None = Query(default=None),
) -> RedirectResponse:
    """OAuth redirect target.

    Deliberately unauthenticated: the browser arrives here from Strava without
    the app's auth header. The `state` token is what binds the callback to the
    user who started the flow, and it is single-use.
    """
    if error or not code or not state:
        logger.warning(
            "Strava callback rejected — error=%s", error or "missing code/state"
        )
        return RedirectResponse(
            f"{settings.STRAVA_CONNECT_REDIRECT}?strava=error", status_code=302
        )

    StravaService.complete_oauth(state=state, code=code, scope=scope)
    return RedirectResponse(
        f"{settings.STRAVA_CONNECT_REDIRECT}?strava=connected", status_code=302
    )


@router.post("/sync")
@limiter.limit("10/minute")
@route_error_handler("strava_sync", detail="Failed to sync Strava activities")
def sync(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Pull the last `days` of activities and cache them."""
    return StravaService.sync(current_user["id"], days=days)


@router.post("/backfill")
@limiter.limit("5/minute")
@route_error_handler("strava_backfill", detail="Failed to backfill Strava activities")
def backfill(
    request: Request,
    body: BackfillRequest,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Re-pull an explicit date range.

    Safe to re-run: the activity cache upserts on the Strava activity id and
    session creation skips anything already linked, so repeating a range repairs
    gaps instead of duplicating.
    """
    start = _parse_day(body.start_date)
    end = _parse_day(body.end_date, end_of_day=True)
    return StravaService.sync(
        current_user["id"], after=start, before=end, auto_create=body.auto_create
    )


@router.get("/importable")
@route_error_handler("strava_importable", detail="Failed to list Strava activities")
def importable(
    limit: int = Query(default=100, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Cached activities with no session yet, plus the class type they'd import as."""
    activities = StravaService.list_importable(current_user["id"], limit)
    return {"activities": activities, "count": len(activities)}


@router.post("/import")
@route_error_handler("strava_import", detail="Failed to import Strava activity")
def import_activity(
    body: ImportRequest,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Create a session from one cached activity."""
    user_id = current_user["id"]
    cached = StravaRepository.get_activity(user_id, body.activity_cache_id)
    if not cached:
        raise NotFoundError(f"Strava activity {body.activity_cache_id} not found")

    session_id = StravaService.import_activity(user_id, cached)
    if session_id is None:
        raise ValidationError("Activity is already linked to a session")
    return {"session_id": session_id}


@router.post("/dismiss")
@route_error_handler("strava_dismiss", detail="Failed to dismiss Strava activity")
def dismiss(
    body: DismissRequest,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Hide (or unhide) an activity so syncs stop offering it."""
    ok = StravaRepository.dismiss(
        current_user["id"], body.activity_cache_id, body.dismissed
    )
    if not ok:
        raise NotFoundError(f"Strava activity {body.activity_cache_id} not found")
    return {"dismissed": body.dismissed}


@router.post("/auto-create-sessions")
@route_error_handler(
    "strava_auto_create", detail="Failed to update Strava auto-create setting"
)
def set_auto_create(
    body: AutoCreateToggle,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Toggle whether syncs auto-create needs-review sessions."""
    StravaRepository.set_auto_create(current_user["id"], body.enabled)
    return {"auto_create_sessions": body.enabled}


@router.delete("")
@route_error_handler("strava_disconnect", detail="Failed to disconnect Strava")
def disconnect(current_user: dict = Depends(require_write_scope)) -> dict:
    """Drop stored tokens. Imported sessions and the activity cache are kept."""
    return {"disconnected": StravaService.disconnect(current_user["id"])}
