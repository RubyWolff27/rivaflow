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
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Cookie, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user, require_write_scope
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.db.repositories.whoop_repo import WhoopRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whoop", tags=["whoop"])

# Root-mounted (no /api/v1 prefix) for a short, bookmarkable cockpit URL.
short_router = APIRouter(tags=["whoop"])

_UNAUTH_HTML = (
    "<h1 style='font-family:system-ui;color:#eee;background:#111'>Unauthorized</h1>"
)


def _resolve_dashboard_key(raw: str) -> dict | None:
    """Resolve a dashboard URL/cookie key to its api_keys row, or None.

    Accepts either a full `rf_pk_` key or a read-only `rf_vk_` view key — the
    dashboards are read-only, so a leaked view URL cannot forge writes (the
    write routes reject a 'read'-scoped key via require_write_scope).
    """
    from rivaflow.db.repositories.api_key_repo import (
        API_KEY_PREFIXES,
        ApiKeyRepository,
    )

    if not raw or not raw.startswith(API_KEY_PREFIXES):
        return None
    return ApiKeyRepository.get_active_by_hash(ApiKeyRepository.hash_key(raw))


@short_router.get("/cockpit", response_class=HTMLResponse)
def cockpit_short(key: str = "", rf_key: str = Cookie(default="")) -> HTMLResponse:
    """Short bookmarkable cockpit: `https://api.rivaflow.app/cockpit`. Pass ?key=YOUR_KEY once and it's
    stored in a cookie, so you can bookmark the bare URL afterwards. Same key-auth as /api/v1/whoop/cockpit.
    """
    from rivaflow.core.whoop_analytics import cockpit_page

    k = key or rf_key
    api_key = _resolve_dashboard_key(k)
    if not api_key:
        return HTMLResponse(
            "<body style='font-family:system-ui;background:#0b1120;color:#e2e8f0;padding:24px'>"
            "<h2>WHOOP Cockpit</h2><p>Add <code>?key=YOUR_KEY</code> to this URL once "
            "(your rf_vk_… view key), then bookmark the bare page.</p></body>",
            status_code=401,
        )
    resp = HTMLResponse(cockpit_page(api_key["user_id"]))
    if key:  # first visit carried the key → remember it so revisits can be keyless
        resp.set_cookie(
            "rf_key",
            key,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 365,
        )
    return resp


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
    device_tz: str | None = None  # IANA tz the phone last reported (e.g. travel)
    raw_frames: list[RawFrame] = Field(default_factory=list)
    hr: list[HrSample] = Field(default_factory=list)
    rr: list[RrSample] = Field(default_factory=list)
    hrv: list[HrvSample] = Field(default_factory=list)
    battery: list[BatterySample] = Field(default_factory=list)


def _persist_device_tz(user_id: int, device_tz: str | None) -> None:
    """Validate + persist the phone-reported device tz on the profile (WhoopProfile
    seam, Wave 3.6) — one UPDATE per genuine change, not per ingest batch. An
    invalid/unknown IANA name is logged and ignored; the ingest still returns 200.
    """
    if not device_tz:
        return
    try:
        ZoneInfo(device_tz)
    except Exception:
        logger.info("Ignoring invalid device_tz=%r for user %s", device_tz, user_id)
        return

    from rivaflow.db.repositories.base_repository import BaseRepository

    row = BaseRepository._fetchone(
        "SELECT device_tz FROM profile WHERE user_id = ?", (user_id,)
    )
    if row is None or row.get("device_tz") == device_tz:
        return  # no profile row yet, or already up to date — skip the write
    BaseRepository._execute(
        "UPDATE profile SET device_tz = ? WHERE user_id = ?", (device_tz, user_id)
    )


def _span(payload: WhoopIngest) -> tuple[str | None, str | None]:
    """Min/max ts across everything in the batch (for the capture-health heartbeat)."""
    ts = (
        [f.ts for f in payload.raw_frames]
        + [s.ts for s in payload.hr]
        + [s.ts for s in payload.rr]
        + [s.ts for s in payload.hrv]
        + [s.ts for s in payload.battery]
    )
    return (min(ts), max(ts)) if ts else (None, None)


@router.post("/ingest")
@limiter.limit("120/minute")
@route_error_handler("whoop_ingest", detail="Failed to ingest WHOOP data")
def ingest(
    request: Request,
    payload: WhoopIngest,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Idempotent raw-first ingest for the authenticated user.

    Rate limit (120/min) is a flood backstop for a leaked key — generous
    enough for the phone's chained backlog-drain bursts, tight enough to stop
    unbounded raw-frame pollution.
    """
    user_id: int = current_user["id"]

    _persist_device_tz(user_id, payload.device_tz)

    raw = WhoopRepository.ingest_raw_frames(
        user_id, [f.model_dump() for f in payload.raw_frames]
    )
    hr = WhoopRepository.ingest_hr(user_id, [s.model_dump() for s in payload.hr])
    rr = WhoopRepository.ingest_rr(user_id, [s.model_dump() for s in payload.rr])
    hrv = WhoopRepository.ingest_hrv(user_id, [s.model_dump() for s in payload.hrv])
    battery = WhoopRepository.ingest_battery(
        user_id, [s.model_dump() for s in payload.battery]
    )

    counts = {
        "raw": raw["received"],
        "rejected": raw["rejected"],
        "hr": hr,
        "rr": rr,
        "hrv": hrv,
        "battery": battery,
    }
    span_start, span_end = _span(payload)
    WhoopRepository.log_ingest(
        user_id, payload.device, payload.kind, counts, span_start, span_end
    )

    logger.info(
        "WHOOP ingest — user_id=%s device=%s kind=%s raw=%s rejected=%s hr=%s rr=%s hrv=%s batt=%s",
        user_id,
        payload.device,
        payload.kind,
        raw["received"],
        raw["rejected"],
        hr,
        rr,
        hrv,
        battery,
    )
    return {"accepted": counts, "span": {"start": span_start, "end": span_end}}


@router.get("/capture-health")
@route_error_handler(
    "whoop_capture_health", detail="Failed to fetch WHOOP capture health"
)
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


class TagCreate(BaseModel):
    """A journal tag for one local day (P1 — Capture & Labels)."""

    day: str = Field(..., description="Local day 'YYYY-MM-DD'")
    tag: str = Field(..., min_length=1, max_length=64)


@router.post("/tag")
@route_error_handler("whoop_add_tag", detail="Failed to add tag")
def add_tag_endpoint(
    req: TagCreate, current_user: dict = Depends(require_write_scope)
) -> dict:
    """Tag a local day (alcohol, late-training, ill, poor-sleep, travel, sabbath-rest…). Idempotent.
    Feeds B11 behaviour correlation and the B6 validation gate (an 'ill' tag is an illness-onset label).
    """
    WhoopRepository.add_tag(current_user["id"], req.day, req.tag)
    return {"added": {"day": req.day, "tag": req.tag}}


@router.get("/tags")
@route_error_handler("whoop_list_tags", detail="Failed to list tags")
def list_tags_endpoint(
    start: str = "", end: str = "", current_user: dict = Depends(get_current_user)
) -> list[dict]:
    """List the user's tags, optionally bounded to [start, end] local days."""
    return WhoopRepository.list_tags(current_user["id"], start or None, end or None)


@router.delete("/tag")
@route_error_handler("whoop_remove_tag", detail="Failed to remove tag")
def remove_tag_endpoint(
    day: str, tag: str, current_user: dict = Depends(require_write_scope)
) -> dict:
    """Remove one (day, tag)."""
    WhoopRepository.remove_tag(current_user["id"], day, tag)
    return {"removed": {"day": day, "tag": tag}}


class WhoopSessionCreate(BaseModel):
    """A timestamped workout session — a real start/end window so per-second HR can attach."""

    activity: str = Field(..., min_length=1, max_length=64)
    started_at: str = Field(..., description="ISO8601 start timestamp")
    ended_at: str | None = Field(
        None, description="ISO8601 end timestamp (optional if still open)"
    )


class WhoopSessionEnd(BaseModel):
    """Close an open workout session."""

    ended_at: str = Field(..., description="ISO8601 end timestamp")


@router.post("/session")
@limiter.limit("30/minute")
@route_error_handler("whoop_create_session", detail="Failed to create session")
def create_session_endpoint(
    request: Request,
    req: WhoopSessionCreate,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Log a timestamped workout session. The window lets the cockpit attach in-window WHOOP HR and
    compute the deep-dive (curve, zones, load, hardness)."""
    session_id = WhoopRepository.create_whoop_session(
        current_user["id"], req.activity, req.started_at, req.ended_at
    )
    return {"id": session_id}


@router.patch("/session/{session_id}/end")
@limiter.limit("30/minute")
@route_error_handler("whoop_end_session", detail="Failed to end session")
def end_session_endpoint(
    request: Request,
    session_id: int,
    req: WhoopSessionEnd,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """Close an open workout session by stamping its end time."""
    ok = WhoopRepository.end_whoop_session(session_id, req.ended_at, current_user["id"])
    if not ok:
        raise NotFoundError(f"WHOOP session {session_id} not found")
    return {"ended": {"id": session_id, "ended_at": req.ended_at}}


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

    is_sabbath = (
        datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    )  # Sunday = Ruby's rest day (adjust if Saturday-Sabbath)
    return compute_readiness(current_user["id"], today_is_sabbath=is_sabbath)


@router.get("/strain-target")
@route_error_handler("whoop_strain_target", detail="Failed to compute strain target")
def strain_target_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B5 — today's prescribed strain target (0–21) from readiness, capped when Strained. Sabbath-silent."""
    from rivaflow.core.whoop_analytics import strain_target

    is_sabbath = (
        datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    )  # Sunday = Ruby's rest day
    return strain_target(current_user["id"], today_is_sabbath=is_sabbath)


@router.get("/sleep-analysis")
@route_error_handler("whoop_sleep_analysis", detail="Failed to compute sleep analysis")
def sleep_analysis_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B9 + B10 — sleep need/debt vs the >9h need + bedtime regularity."""
    from rivaflow.core.whoop_analytics import sleep_analysis

    return sleep_analysis(current_user["id"])


@router.get("/acwr")
@route_error_handler("whoop_acwr", detail="Failed to compute ACWR")
def acwr_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B7 — acute:chronic workload ratio (Gabbett injury-risk window)."""
    from rivaflow.core.whoop_analytics import training_acwr

    return training_acwr(current_user["id"])


@router.get("/recovery-cost")
@route_error_handler("whoop_recovery_cost", detail="Failed to compute recovery cost")
def recovery_cost_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B12 — prior-day load → next-day HRV coupling (personal recovery cost per dose)."""
    from rivaflow.core.whoop_analytics import recovery_cost_coupling

    return recovery_cost_coupling(current_user["id"])


@router.get("/prevention")
@route_error_handler(
    "whoop_prevention", detail="Failed to compute baseline-deviation watch"
)
def prevention_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B6 — Baseline-Deviation Watch: multi-signal deviation from personal baseline. Safety channel (fires
    Sunday). Detects deviation, never disease — not a medical device."""
    from rivaflow.core.whoop_analytics import prevention_watch

    return prevention_watch(current_user["id"])


@router.get("/longevity")
@route_error_handler("whoop_longevity", detail="Failed to compute longevity metrics")
def longevity_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B14 + B15 — passive VO2max (banded) + cardio-age proxy (web; proxy, not clinical)."""
    from rivaflow.core.whoop_analytics import longevity_metrics

    return longevity_metrics(current_user["id"])


@router.get("/resilience")
@route_error_handler("whoop_resilience", detail="Failed to compute resilience")
def resilience_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B16 — resilience (14d bounce-back) + 31d cumulative stress."""
    from rivaflow.core.whoop_analytics import resilience_metrics

    return resilience_metrics(current_user["id"])


@router.get("/circadian")
@route_error_handler("whoop_circadian", detail="Failed to compute circadian rhythm")
def circadian_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B17 — cosinor circadian rhythm of time-of-day HR."""
    from rivaflow.core.whoop_analytics import circadian_rhythm

    return circadian_rhythm(current_user["id"])


@router.get("/dfa")
@route_error_handler("whoop_dfa", detail="Failed to compute DFA alpha1")
def dfa_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B18 — DFA α1 (experimental, artifact-gated)."""
    from rivaflow.core.whoop_analytics import dfa_analysis

    return dfa_analysis(current_user["id"])


@router.get("/realtime-stress")
@route_error_handler(
    "whoop_realtime_stress", detail="Failed to compute realtime stress"
)
def realtime_stress_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B13 — HRV-based real-time stress (experimental; at-rest only)."""
    from rivaflow.core.whoop_analytics import realtime_stress

    return realtime_stress(current_user["id"])


@router.get("/assessment")
@route_error_handler("whoop_assessment", detail="Failed to compute assessment")
def assessment_endpoint(
    period: str = "week", current_user: dict = Depends(get_current_user)
) -> dict:
    """B19 — weekly/monthly assessment narrative. ?period=week|month."""
    from rivaflow.core.whoop_analytics import period_assessment_for

    days = 30 if period == "month" else 7
    return period_assessment_for(current_user["id"], period, days)


@router.get("/prevention-backtest")
@route_error_handler(
    "whoop_prevention_backtest", detail="Failed to backtest prevention engine"
)
def prevention_backtest_endpoint(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """B6 — per-day tier timeline over recent history (feeds the validation gate)."""
    from rivaflow.core.whoop_analytics import prevention_backtest

    return {"timeline": prevention_backtest(current_user["id"])}


@router.get("/prevention-validate")
@route_error_handler(
    "whoop_prevention_validate", detail="Failed to validate prevention engine"
)
def prevention_validate_endpoint(
    onsets: str = "", current_user: dict = Depends(get_current_user)
) -> dict:
    """B6 validation & tuning gate — backtest the engine against retrospectively-tagged illness onsets and
    score it vs the acceptance target. ?onsets=YYYY-MM-DD,YYYY-MM-DD (from the journal/tagging path).
    """
    from rivaflow.core.whoop_analytics import (
        prevention_validation,
        prevention_validation_live,
    )

    dates = {d.strip() for d in onsets.split(",") if d.strip()}
    if dates:
        return prevention_validation(current_user["id"], dates)
    # No explicit onsets → use the real 'ill' journal tags (P1).
    return prevention_validation_live(current_user["id"])


@router.get("/digest")
@route_error_handler("whoop_digest", detail="Failed to compile digest")
def digest_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """P2 — once-daily digest preview (readiness + strain + prevention, tier→channel routed). Sabbath-aware."""
    from rivaflow.core.whoop_analytics import morning_digest

    is_sabbath = datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    return morning_digest(current_user["id"], today_is_sabbath=is_sabbath)


@router.post("/digest/deliver")
@route_error_handler("whoop_digest_deliver", detail="Failed to deliver digest")
def deliver_digest_endpoint(current_user: dict = Depends(require_write_scope)) -> dict:
    """P2 — deliver today's digest: applies the cooldown and records any safety alert that fires. Called
    once each morning by the briefing cron (idempotent per day/key)."""
    from rivaflow.core.whoop_analytics import deliver_digest

    return deliver_digest(current_user["id"])


@router.get("/prevention-log")
@route_error_handler("whoop_prevention_log", detail="Failed to fetch prevention log")
def prevention_log_endpoint(
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """P2/P3.4 — timeline of fired safety alerts (the prevention log)."""
    from rivaflow.core.whoop_analytics import prevention_log

    return prevention_log(current_user["id"])


@router.get("/behaviour")
@route_error_handler(
    "whoop_behaviour", detail="Failed to compute behaviour correlation"
)
def behaviour_endpoint(
    tag: str, current_user: dict = Depends(get_current_user)
) -> dict:
    """B11 — effect of a tagged behaviour on lnRMSSD (tagged nights vs untagged), from the journal tags."""
    from rivaflow.core.whoop_analytics import behaviour_for_tag

    return behaviour_for_tag(current_user["id"], tag)


@router.get("/hrv-lab")
@route_error_handler("whoop_hrv_lab", detail="Failed to compute HRV lab")
def hrv_lab_endpoint(current_user: dict = Depends(get_current_user)) -> dict:
    """B4 — frequency-domain (Lomb-Scargle LF/HF) + Poincaré HRV over the longest clean ≥5-min resting window."""
    from rivaflow.core.whoop_analytics import hrv_lab

    return hrv_lab(current_user["id"])


@router.get("/session-analytics")
@route_error_handler(
    "whoop_session_analytics", detail="Failed to compute BJJ session analytics"
)
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


@router.get("/respiratory")
@route_error_handler("whoop_respiratory", detail="Failed to compute respiratory rate")
def respiratory(current_user: dict = Depends(get_current_user)) -> dict:
    """Respiratory rate from RR-interval oscillation (RSA)."""
    from rivaflow.core.whoop_analytics import respiratory_rate

    return respiratory_rate(current_user["id"])


@router.get("/cardio-load")
@route_error_handler("whoop_cardio_load", detail="Failed to compute cardio load")
def cardio_load(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Daily cardio load / strain (HR-zone TRIMP, ~0-21 scale)."""
    from rivaflow.core.whoop_analytics import daily_cardio_load

    return daily_cardio_load(current_user["id"], days)


@router.get("/stress")
@route_error_handler("whoop_stress", detail="Failed to compute stress")
def stress(current_user: dict = Depends(get_current_user)) -> dict:
    """Current stress proxy (HR elevation within reserve, 0-100)."""
    from rivaflow.core.whoop_analytics import today_stress

    return today_stress(current_user["id"])


# whoop_summary recomputes readiness/HRV/sleep/strain from the raw HR/RR tables on every call —
# 26-35s at ~280k HR rows (2026-07-08 access logs), which times out the phone tiles and stacks a
# fresh 30s recompute under every retry. New data only lands every ~2.5 min (uploader flush), so a
# short-TTL in-process copy loses nothing a client could observe. Per-worker duplication is fine.
_SUMMARY_CACHE: dict[tuple[int, bool], tuple[float, dict]] = {}
_SUMMARY_TTL_S = 300.0


def _cached_whoop_summary(user_id: int, today_is_sabbath: bool) -> dict:
    from rivaflow.core.whoop_analytics import whoop_summary

    key = (user_id, today_is_sabbath)
    now = time.monotonic()
    hit = _SUMMARY_CACHE.get(key)
    if hit and hit[0] > now:
        return hit[1]
    result = whoop_summary(user_id, today_is_sabbath=today_is_sabbath)
    _SUMMARY_CACHE[key] = (now + _SUMMARY_TTL_S, result)
    return result


@router.get("/summary")
@route_error_handler("whoop_summary", detail="Failed to build WHOOP summary")
def summary(current_user: dict = Depends(get_current_user)) -> dict:
    """One-call rollup for a thin display client: readiness + HRV + resting HR + last night's sleep.
    The whole point of the server-side architecture — the phone/dashboard fetches this and just renders it.
    """
    is_sabbath = datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    return _cached_whoop_summary(current_user["id"], today_is_sabbath=is_sabbath)


class CoachTurn(BaseModel):
    """One turn of the recovery/readiness coach chat (Wave 2.1)."""

    message: str = Field(..., min_length=1, max_length=2000)
    history: list[dict] = Field(
        default_factory=list,
        description="Trailing conversation as [{role:'user'|'assistant', content:str}, …]",
    )


@router.post("/coach")
@limiter.limit("30/minute")
@route_error_handler("whoop_coach", detail="Failed to get coach response")
async def coach(
    request: Request,
    req: CoachTurn,
    current_user: dict = Depends(require_write_scope),
) -> dict:
    """WHOOP recovery & readiness coach — server-side and provider-agnostic (Wave 2.1).

    Reasons over the SAME `whoop_summary` the phone renders (so answers cite the
    numbers Ruby sees) and generates via `GrappleLLMClient` — provider + model are
    a server config row, so swapping the model is an env edit, no app rebuild.
    Write-scoped: a paid outbound LLM call is a side-effect, so a read-only view
    key cannot invoke it. Rate-limited as an LLM-budget backstop.
    """
    from rivaflow.core.services import whoop_coach

    is_sabbath = datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    try:
        return await whoop_coach.answer(
            current_user["id"],
            req.message,
            history=req.history,
            today_is_sabbath=is_sabbath,
        )
    except RuntimeError as exc:
        # No LLM provider configured, or every provider failed — degrade gracefully
        # rather than 500, so the phone shows a message instead of a broken chat.
        logger.warning("Coach unavailable for user %s: %s", current_user["id"], exc)
        return {
            "reply": (
                "I can't reach the coaching model right now — your numbers are still "
                "live on your dashboard. Try again in a moment."
            ),
            "provider": None,
            "model": None,
            "tokens": None,
            "unavailable": True,
        }


@router.get("/cockpit-metrics")
@route_error_handler("whoop_cockpit_metrics", detail="Failed to read cockpit metrics")
def cockpit_metrics(current_user: dict = Depends(get_current_user)) -> dict:
    """The structured metrics JSON behind the cockpit snapshot — the same data
    the deep-dive HTML was rendered from, served instantly (one SELECT) instead
    of the ~40s recompute. The stable contract for the phone and a future model
    narrator layer. Returns {metrics, deriver_version, rendered_at} or nulls
    until the first snapshot exists.
    """
    import json

    row = WhoopRepository.get_cockpit_metrics(current_user["id"])
    if not row or not row.get("metrics_json"):
        return {"metrics": None, "deriver_version": None, "rendered_at": None}
    return {
        "metrics": json.loads(row["metrics_json"]),
        "deriver_version": row.get("deriver_version"),
        "rendered_at": str(row.get("rendered_at")),
    }


@router.get("/cockpit", response_class=HTMLResponse)
def cockpit(key: str) -> HTMLResponse:
    """P3 — server-rendered web deep-dive cockpit (analyst panels). Zero client compute; key-auth like /view."""
    from rivaflow.core.whoop_analytics import cockpit_page

    api_key = _resolve_dashboard_key(key)
    if not api_key:
        return HTMLResponse(_UNAUTH_HTML, status_code=401)
    return HTMLResponse(cockpit_page(api_key["user_id"]))


@router.get("/view", response_class=HTMLResponse)
def view(key: str) -> HTMLResponse:
    """Server-rendered thin-display dashboard — the phone/browser opens a URL and the VPS renders the
    metrics into HTML. Zero client compute. Personal tool: auth via the owner's own api-key query param.
    """
    api_key = _resolve_dashboard_key(key)
    if not api_key:
        return HTMLResponse(_UNAUTH_HTML, status_code=401)

    is_sabbath = datetime.now(ZoneInfo("Australia/Melbourne")).weekday() == 6
    s = _cached_whoop_summary(api_key["user_id"], today_is_sabbath=is_sabbath)
    return HTMLResponse(_render_whoop_view(s))


def _local_hm(iso_str: str) -> str:
    """UTC ISO timestamp → Melbourne HH:MM for display."""
    try:
        return (
            datetime.fromisoformat(iso_str)
            .astimezone(ZoneInfo("Australia/Melbourne"))
            .strftime("%H:%M")
        )
    except (ValueError, TypeError):
        return str(iso_str)[11:16]


def _render_whoop_view(s: dict) -> str:
    r = s.get("readiness") or {}
    hrv = s.get("hrv_today") or {}
    rhr = s.get("resting_hr_today") or {}
    sleep = s.get("sleep") or {}
    state_colors = {
        "Prime": "#34d399",
        "Balanced": "#60a5fa",
        "Strained": "#fbbf24",
        "Rundown": "#f87171",
        "Building": "#94a3b8",
        "Rest": "#a78bfa",
    }
    accent = state_colors.get(r.get("state", "Building"), "#94a3b8")
    score = r.get("score")
    hero_val = f"{score}" if score is not None else (r.get("state") or "—")
    hrv_val = f"{hrv.get('rmssd')}" if hrv.get("rmssd") is not None else "—"
    rhr_val = f"{rhr.get('resting_hr')}" if rhr.get("resting_hr") is not None else "—"
    sleep_val = f"{sleep.get('duration_hours')}" if sleep.get("available") else "—"
    sleep_q = sleep.get("quality_score")
    sleep_sub = (
        f"{_local_hm(sleep.get('sleep_start',''))}–{_local_hm(sleep.get('sleep_end',''))}"
        + (f" · quality {sleep_q}" if sleep_q is not None else "")
        if sleep.get("available")
        else (sleep.get("reason") or "no data")
    )
    resp = s.get("respiratory_rate") or {}
    resp_val = f"{resp.get('respiratory_rate')}" if resp.get("available") else "—"
    cardio = s.get("cardio_load_today") or {}
    cardio_val = (
        f"{cardio.get('cardio_load')}" if cardio.get("cardio_load") is not None else "—"
    )
    stress = s.get("stress") or {}
    stress_val = f"{stress.get('stress')}" if stress.get("available") else "—"
    trend = s.get("hrv_trend") or []
    trend_pts = (
        " · ".join(f"{p['day'][5:]}: {p['rmssd']}" for p in trend[-7:]) or "building…"
    )
    return _WHOOP_VIEW_TEMPLATE.format(
        accent=accent,
        state=r.get("state", "—"),
        headline=r.get("headline", ""),
        hero_val=hero_val,
        hrv_val=hrv_val,
        rhr_val=rhr_val,
        sleep_val=sleep_val,
        sleep_sub=sleep_sub,
        rhr_sub=f"min {rhr.get('min_hr','—')} · {rhr.get('samples',0)} samples",
        resp_val=resp_val,
        cardio_val=cardio_val,
        stress_val=stress_val,
        trend_pts=trend_pts,
    )


_WHOOP_VIEW_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="120"><title>WHOOP · RivaFlow</title>
<style>
  *{{box-sizing:border-box;margin:0}}
  body{{font-family:-apple-system,system-ui,sans-serif;background:#0a0a0c;color:#e8e8ea;
       padding:20px;max-width:640px;margin:0 auto;-webkit-font-smoothing:antialiased}}
  h1{{font-size:13px;text-transform:uppercase;letter-spacing:.12em;color:#71717a;font-weight:600;margin-bottom:16px}}
  .hero{{background:linear-gradient(160deg,{accent}22,#141418);border:1px solid {accent}44;
        border-radius:20px;padding:24px;margin-bottom:14px}}
  .hero .state{{color:{accent};font-weight:800;font-size:17px}}
  .hero .num{{font-size:64px;font-weight:800;line-height:1;margin:6px 0;font-variant-numeric:tabular-nums}}
  .hero .head{{color:#a1a1aa;font-size:14px;margin-top:8px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
  .card{{background:#141418;border:1px solid #26262b;border-radius:16px;padding:18px}}
  .card .lbl{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#71717a;font-weight:600}}
  .card .v{{font-size:34px;font-weight:800;margin-top:6px;font-variant-numeric:tabular-nums}}
  .card .u{{font-size:15px;color:#71717a;font-weight:600}}
  .card .sub{{font-size:12px;color:#8a8a92;margin-top:6px}}
  .trend{{background:#141418;border:1px solid #26262b;border-radius:16px;padding:16px;margin-top:12px}}
  .trend .lbl{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#71717a;font-weight:600;margin-bottom:8px}}
  .trend .pts{{font-size:13px;color:#c4c4c8;font-variant-numeric:tabular-nums;line-height:1.7}}
  .foot{{color:#52525b;font-size:11px;text-align:center;margin-top:18px}}
</style></head><body>
  <h1>Recovery · RivaFlow</h1>
  <div class="hero">
    <div class="state">{state}</div>
    <div class="num">{hero_val}</div>
    <div class="head">{headline}</div>
  </div>
  <div class="grid">
    <div class="card"><div class="lbl">HRV</div><div class="v">{hrv_val}<span class="u"> ms</span></div><div class="sub">resting RMSSD, today</div></div>
    <div class="card"><div class="lbl">Resting HR</div><div class="v">{rhr_val}<span class="u"> bpm</span></div><div class="sub">{rhr_sub}</div></div>
    <div class="card"><div class="lbl">Sleep</div><div class="v">{sleep_val}<span class="u"> h</span></div><div class="sub">{sleep_sub}</div></div>
    <div class="card"><div class="lbl">Respiratory</div><div class="v">{resp_val}<span class="u"> rpm</span></div><div class="sub">from RR oscillation (RSA)</div></div>
    <div class="card"><div class="lbl">Cardio Load</div><div class="v">{cardio_val}<span class="u"> /21</span></div><div class="sub">HR-zone strain, today</div></div>
    <div class="card"><div class="lbl">Stress</div><div class="v">{stress_val}<span class="u"> /100</span></div><div class="sub">HR elevation vs resting</div></div>
  </div>
  <div class="trend"><div class="lbl">HRV · last 7 days</div><div class="pts">{trend_pts}</div></div>
  <div class="foot">RivaFlow · self-hosted · auto-refreshes every 2 min</div>
</body></html>"""
