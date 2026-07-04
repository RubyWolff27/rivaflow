"""Garmin metrics endpoints.

- POST /garmin/daily   — batch ingest from the Mac push job (RivaFlowGarminPush).
- GET  /garmin/daily   — daily key-metric series for the Health-tab trend charts.
- GET  /garmin/summary — most recent day's metrics for the summary cards.

Per-session Garmin biometrics are NOT served here — they ride on the session
object (see SessionResponse garmin_* fields) and are set via the session update
path. This module owns only the daily metrics.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.models import GarminDailyIngest
from rivaflow.db.repositories.garmin_daily_repo import GarminDailyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/garmin", tags=["garmin"])


@router.post("/daily")
@route_error_handler(
    "garmin_daily_ingest", detail="Failed to ingest Garmin daily metrics"
)
def ingest_daily(
    payload: GarminDailyIngest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Upsert a batch of daily Garmin metrics for the authenticated user."""
    user_id: int = current_user["id"]
    count = 0
    for metric in payload.metrics:
        fields = metric.model_dump(exclude={"metric_date"})
        GarminDailyRepository.upsert(user_id, metric.metric_date, **fields)
        count += 1
    logger.info("Garmin daily ingest — user_id=%s upserted=%s", user_id, count)
    return {"upserted": count}


@router.get("/daily")
@route_error_handler("garmin_daily_list", detail="Failed to fetch Garmin daily metrics")
def list_daily(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Daily key metrics for the last `days`, oldest first (for trend charts)."""
    return GarminDailyRepository.get_range(current_user["id"], days)


@router.get("/summary")
@route_error_handler("garmin_summary", detail="Failed to fetch Garmin summary")
def summary(current_user: dict = Depends(get_current_user)) -> dict:
    """Most recent day of Garmin metrics (for the summary cards)."""
    return {"latest": GarminDailyRepository.get_latest(current_user["id"])}
