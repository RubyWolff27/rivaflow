"""API routes for activity feed."""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from rivaflow.db.repositories import SessionRepository, ReadinessRepository
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.core.services.feed_service import FeedService
from rivaflow.core.dependencies import get_current_user

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/activity")
def get_activity_feed(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10000),
    days_back: Optional[int] = Query(default=30, ge=1, le=365),
    enrich_social: bool = Query(default=False),
    current_user: dict = Depends(get_current_user)
):
    """
    Get unified activity feed showing all user activity.
    Returns sessions, readiness check-ins, and rest days in chronological order.
    """
    return FeedService.get_my_feed(
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
        days_back=days_back,
        enrich_social=enrich_social,
    )


@router.get("/contacts")
def get_contacts_feed(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0, le=10000),
    days_back: Optional[int] = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity feed from users that this user follows (contacts feed).
    Only shows activities with visibility_level != 'private' with privacy redaction applied.
    Always includes social data (likes, comments).
    """
    return FeedService.get_contacts_feed(
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
        days_back=days_back,
    )
