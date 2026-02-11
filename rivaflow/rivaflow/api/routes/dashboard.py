"""Dashboard API endpoints."""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ServiceError
from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.goals_service import GoalsService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.services.streak_service import StreakService
from rivaflow.core.utils.cache import cached
from rivaflow.db.repositories.readiness_repo import ReadinessRepository
from rivaflow.db.repositories.session_repo import SessionRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
limiter = Limiter(key_func=get_remote_address)


@cached(ttl_seconds=300, key_prefix="dashboard_summary")
def _get_dashboard_summary_cached(
    user_id: int,
    start_date: date,
    end_date: date,
    types: list[str] | None = None,
    tz: str | None = None,
):
    """
    Cached helper for dashboard summary.
    Cache TTL: 5 minutes
    """
    # Initialize services
    analytics = AnalyticsService()
    milestone_service = MilestoneService()
    streak_service = StreakService()
    goals_service = GoalsService()
    session_repo = SessionRepository()
    readiness_repo = ReadinessRepository()

    # Fetch data
    performance = analytics.get_performance_overview(
        user_id, start_date, end_date, types=types
    )

    # Get streak data
    session_streak = streak_service.get_streak(user_id, "session")
    checkin_streak = streak_service.get_streak(user_id, "checkin")

    # Get recent sessions
    recent_sessions = session_repo.get_recent(user_id, limit=10)

    # Get milestones
    closest_milestone = milestone_service.get_closest_milestone(user_id)
    milestone_progress = milestone_service.get_progress_to_next(user_id)

    # Get weekly goals progress
    weekly_goals = goals_service.get_current_week_progress(user_id, tz=tz)

    # Get latest readiness
    latest_readiness = readiness_repo.get_latest(user_id)

    # Get class type distribution
    class_type_distribution = {}
    for session in recent_sessions:
        class_type = session.get("class_type", "unknown")
        class_type_distribution[class_type] = (
            class_type_distribution.get(class_type, 0) + 1
        )

    return {
        "performance": {
            "summary": performance.get("summary", {}),
            "deltas": performance.get("deltas", {}),
            "daily_timeseries": performance.get("daily_timeseries", {}),
        },
        "streaks": {
            "session": session_streak,
            "checkin": checkin_streak,
        },
        "recent_sessions": recent_sessions[:5],  # Just top 5 for dashboard
        "milestones": {
            "closest": closest_milestone,
            "progress": milestone_progress[:3],  # Top 3 closest
        },
        "weekly_goals": weekly_goals,
        "readiness": latest_readiness,
        "class_type_distribution": class_type_distribution,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    }


@router.get("/summary")
@limiter.limit("60/minute")
def get_dashboard_summary(
    request: Request,
    start_date: date | None = Query(None, description="Start date for analytics"),
    end_date: date | None = Query(None, description="End date for analytics"),
    types: list[str] | None = Query(None, description="Filter by class types"),
    tz: str | None = Query(None, description="IANA timezone, e.g. Australia/Sydney"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all dashboard data in a single consolidated request.

    This endpoint combines data from multiple services:
    - Performance overview (sessions, submissions, intensity, etc.)
    - Training streaks (current and longest)
    - Recent sessions (last 10)
    - Upcoming milestones
    - Weekly goals progress
    - Latest readiness check

    Returns:
        Consolidated dashboard data
    """
    user_id = current_user["id"]

    # Set default date range using timezone-aware today
    from rivaflow.core.services.report_service import today_in_tz

    _today = today_in_tz(tz)
    if not start_date:
        start_date = _today - timedelta(days=30)
    if not end_date:
        end_date = _today

    try:
        # Use cached function (5-minute TTL)
        return _get_dashboard_summary_cached(
            user_id, start_date, end_date, types=types if types else None, tz=tz
        )

    except Exception as e:
        logger.error(f"Failed to load dashboard: {e}")
        raise ServiceError("Failed to load dashboard data")


@router.get("/quick-stats")
@limiter.limit("60/minute")
def get_quick_stats(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get quick stats for minimal dashboard.

    Returns just the essential numbers:
    - Total sessions
    - Total hours
    - Current streak
    - Next milestone

    Returns:
        Quick stats
    """
    user_id = current_user["id"]

    try:
        session_repo = SessionRepository()
        streak_service = StreakService()
        milestone_service = MilestoneService()

        # Get user stats efficiently (no unbounded query)
        stats = session_repo.get_user_stats(user_id)

        # Current streak
        session_streak = streak_service.get_streak(user_id, "session")

        # Next milestone
        closest_milestone = milestone_service.get_closest_milestone(user_id)

        return {
            "total_sessions": stats["total_sessions"],
            "total_hours": stats["total_hours"],
            "current_streak": session_streak.get("current_streak", 0),
            "next_milestone": closest_milestone,
        }

    except Exception as e:
        logger.error(f"Failed to load quick stats: {e}")
        raise ServiceError("Failed to load quick stats")


@router.get("/week-summary")
@limiter.limit("60/minute")
def get_week_summary(
    request: Request,
    week_offset: int = Query(
        0,
        ge=-52,
        le=0,
        description="Weeks back from current week (0 = this week, -1 = last week)",
    ),
    tz: str | None = Query(None, description="IANA timezone, e.g. Australia/Sydney"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get summary for a specific week.

    Args:
        week_offset: How many weeks back (0 = current week, -1 = last week, etc.)

    Returns:
        Week summary with sessions, goals progress, etc.
    """
    user_id = current_user["id"]

    try:
        # Calculate week start/end
        from rivaflow.core.services.report_service import today_in_tz

        today = today_in_tz(tz)
        current_week_start = today - timedelta(days=today.weekday())
        week_start = current_week_start + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)

        session_repo = SessionRepository()

        # Get sessions for the week
        sessions = session_repo.get_by_date_range(user_id, week_start, week_end)

        # Calculate stats
        total_sessions = len(sessions)
        total_hours = sum(s.get("duration_mins", 60) for s in sessions) / 60
        total_rolls = sum(s.get("rolls", 0) for s in sessions)

        # Class type breakdown
        class_types = {}
        for session in sessions:
            ct = session.get("class_type", "unknown")
            class_types[ct] = class_types.get(ct, 0) + 1

        # Weekly goals - just return None for now, goals are tracked separately
        weekly_goals = None

        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "is_current_week": week_offset == 0,
            "stats": {
                "total_sessions": total_sessions,
                "total_hours": round(total_hours, 1),
                "total_rolls": total_rolls,
            },
            "class_types": class_types,
            "goals": weekly_goals,
            "sessions": sessions,
        }

    except Exception as e:
        logger.error(f"Failed to load week summary: {e}")
        raise ServiceError("Failed to load week summary")
