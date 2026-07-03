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

from fastapi import APIRouter, Depends
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
