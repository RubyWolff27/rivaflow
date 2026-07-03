"""Subscription-free WHOOP data-platform endpoints (Phase 1a).

- POST /whoop/ingest — batched, idempotent, raw-first ingest from the Goose iOS app
  (WhoopVpsUploader). Stores every raw BLE frame (even undecoded) plus decoded
  HR / RR / HRV / battery streams, all scoped to the authenticated user.
- GET  /whoop/capture-health — last-seen heartbeat + recent ingest volume, for
  gap detection (WHOOP is the only biometric source now that Garmin is gone).

Session-level rollups and the R22 decode land in later phases; this owns capture.
See docs DATA-PLATFORM-BUILD-PLAN.md in the goose-whoop5 repo.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.db.repositories.whoop_repo import WhoopRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whoop", tags=["whoop"])


class RawFrame(BaseModel):
    ts: str
    char_uuid: str
    hex: str
    packet_type: int | None = None
    seq: int | None = None
    session_id: str | None = None


class HrSample(BaseModel):
    ts: str
    bpm: int
    session_id: str | None = None


class RrSample(BaseModel):
    ts: str
    rr_ms: int
    session_id: str | None = None


class HrvSample(BaseModel):
    ts: str
    rmssd: float | None = None
    rr_count: int | None = None
    window_s: int | None = None
    at_rest: bool | None = None


class BatterySample(BaseModel):
    ts: str
    soc: int | None = None
    charging: bool | None = None


class WhoopIngest(BaseModel):
    """Batched upload from the Goose iOS app (offline-buffered, retry-safe)."""

    device: str | None = None
    kind: str | None = "realtime"  # 'realtime' | 'historical_drain'
    batch_id: str | None = None
    raw_frames: list[RawFrame] = Field(default_factory=list)
    hr: list[HrSample] = Field(default_factory=list)
    rr: list[RrSample] = Field(default_factory=list)
    hrv: list[HrvSample] = Field(default_factory=list)
    battery: list[BatterySample] = Field(default_factory=list)


def _span(payload: WhoopIngest) -> tuple[str | None, str | None]:
    """Min/max ts across everything in the batch (for the capture-health heartbeat)."""
    ts = (
        [f.ts for f in payload.raw_frames] + [s.ts for s in payload.hr]
        + [s.ts for s in payload.rr] + [s.ts for s in payload.hrv]
        + [s.ts for s in payload.battery]
    )
    return (min(ts), max(ts)) if ts else (None, None)


@router.post("/ingest")
@route_error_handler("whoop_ingest", detail="Failed to ingest WHOOP data")
def ingest(payload: WhoopIngest, current_user: dict = Depends(get_current_user)) -> dict:
    """Idempotent raw-first ingest for the authenticated user."""
    user_id: int = current_user["id"]

    raw = WhoopRepository.ingest_raw_frames(user_id, [f.model_dump() for f in payload.raw_frames])
    hr = WhoopRepository.ingest_hr(user_id, [s.model_dump() for s in payload.hr])
    rr = WhoopRepository.ingest_rr(user_id, [s.model_dump() for s in payload.rr])
    hrv = WhoopRepository.ingest_hrv(user_id, [s.model_dump() for s in payload.hrv])
    battery = WhoopRepository.ingest_battery(user_id, [s.model_dump() for s in payload.battery])

    counts = {
        "raw": raw["received"], "rejected": raw["rejected"],
        "hr": hr, "rr": rr, "hrv": hrv, "battery": battery,
    }
    span_start, span_end = _span(payload)
    WhoopRepository.log_ingest(user_id, payload.device, payload.kind, counts, span_start, span_end)

    logger.info(
        "WHOOP ingest — user_id=%s device=%s kind=%s raw=%s rejected=%s hr=%s rr=%s hrv=%s batt=%s",
        user_id, payload.device, payload.kind, raw["received"], raw["rejected"], hr, rr, hrv, battery,
    )
    return {"accepted": counts, "span": {"start": span_start, "end": span_end}}


@router.get("/capture-health")
@route_error_handler("whoop_capture_health", detail="Failed to fetch WHOOP capture health")
def capture_health(current_user: dict = Depends(get_current_user)) -> dict:
    """Last-seen heartbeat + recent ingest volume for gap detection."""
    from rivaflow.db.database import convert_query
    from rivaflow.db.repositories.base_repository import BaseRepository

    latest = BaseRepository._fetchone(
        convert_query(
            "SELECT ingested_at, device, kind, raw_frames, hr, rr, hrv, span_start, span_end "
            "FROM whoop_ingest_log WHERE user_id = ? ORDER BY ingested_at DESC LIMIT 1"
        ),
        (current_user["id"],),
    )
    return {"latest": latest}


# ── Read + analytics (Phase 2 / shared access: RivaFlow UI, health dashboard, LLM/MCP) ──


@router.get("/hr")
@route_error_handler("whoop_hr", detail="Failed to fetch WHOOP heart rate")
def hr_series(
    hours: int = Query(6, ge=1, le=168),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Recent HR series (last `hours`)."""
    return WhoopRepository.recent_hr(current_user["id"], hours)


@router.get("/hrv")
@route_error_handler("whoop_hrv", detail="Failed to fetch WHOOP HRV")
def hrv_series(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Daily resting HRV (RMSSD), derived from RR intervals — the recovery signal."""
    from rivaflow.core.whoop_analytics import daily_resting_rmssd

    return daily_resting_rmssd(current_user["id"], days)


@router.get("/readiness")
@route_error_handler("whoop_readiness", detail="Failed to compute readiness")
def readiness(current_user: dict = Depends(get_current_user)) -> dict:
    """Ruby Readiness Score — at-rest HRV vs rolling baseline. Sabbath-silent (Sunday rest)."""
    from rivaflow.core.whoop_analytics import compute_readiness

    is_sabbath = date.today().weekday() == 6  # Sunday = Ruby's rest day (adjust if Saturday-Sabbath)
    return compute_readiness(current_user["id"], today_is_sabbath=is_sabbath)


@router.get("/session-analytics")
@route_error_handler("whoop_session_analytics", detail="Failed to compute BJJ session analytics")
def session_analytics(
    start: str,
    end: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """BJJ roll analytics for a [start, end] window: HR zones, avg/max, best between-round recovery."""
    from rivaflow.core.whoop_analytics import bjj_session_analytics

    return bjj_session_analytics(current_user["id"], start, end)


@router.get("/sleep")
@route_error_handler("whoop_sleep", detail="Failed to compute sleep")
def sleep(current_user: dict = Depends(get_current_user)) -> dict:
    """Last night's sleep (HR-based duration + timing) — server-side, no client compute."""
    from rivaflow.core.whoop_analytics import nightly_sleep

    return nightly_sleep(current_user["id"])


@router.get("/resting-hr")
@route_error_handler("whoop_resting_hr", detail="Failed to compute resting HR")
def resting_hr(
    days: int = Query(14, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Daily resting HR (5th-percentile of each day's HR)."""
    from rivaflow.core.whoop_analytics import daily_resting_hr

    return daily_resting_hr(current_user["id"], days)


@router.get("/summary")
@route_error_handler("whoop_summary", detail="Failed to build WHOOP summary")
def summary(current_user: dict = Depends(get_current_user)) -> dict:
    """One-call rollup for a thin display client: readiness + HRV + resting HR + last night's sleep.
    The whole point of the server-side architecture — the phone/dashboard fetches this and just renders it."""
    from rivaflow.core.whoop_analytics import whoop_summary

    is_sabbath = date.today().weekday() == 6
    return whoop_summary(current_user["id"], today_is_sabbath=is_sabbath)
