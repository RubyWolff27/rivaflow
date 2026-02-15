"""Weekly goals and streak tracking endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.api.response_models import GoalsSummaryResponse, WeeklyGoalProgress
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import RivaFlowException, ValidationError
from rivaflow.core.services.goals_service import GoalsService

logger = logging.getLogger(__name__)

router = APIRouter()


class GoalTargetsUpdate(BaseModel):
    """Weekly goal targets update."""

    weekly_sessions_target: int | None = None
    weekly_hours_target: float | None = None
    weekly_rolls_target: int | None = None


@router.get("/current-week", response_model=WeeklyGoalProgress)
@limiter.limit("120/minute")
def get_current_week_progress(
    request: Request,
    tz: str | None = Query(None, description="IANA timezone, e.g. Australia/Sydney"),
    current_user: dict = Depends(get_current_user),
):
    """Get current week's goal progress.

    Returns progress toward weekly targets:
    - Sessions, hours, rolls
    - Percentage completion
    - Days remaining
    - Completion status
    """
    service = GoalsService()
    try:
        logger.info(f"Getting current week progress for user_id={current_user['id']}")
        result = service.get_current_week_progress(user_id=current_user["id"], tz=tz)
        logger.info(
            f"Successfully retrieved current week progress for user_id={current_user['id']}"
        )
        return result
    except (RivaFlowException, HTTPException):
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(
            "get_current_week_progress failed for user_id=%s: %s",
            current_user["id"],
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to get current week progress"
        )


@router.get("/summary", response_model=GoalsSummaryResponse)
@limiter.limit("120/minute")
def get_goals_summary(
    request: Request,
    tz: str | None = Query(None, description="IANA timezone, e.g. Australia/Sydney"),
    current_user: dict = Depends(get_current_user),
):
    """Get comprehensive goals and streaks overview.

    Returns:
    - Current week progress
    - Training streaks (consecutive days)
    - Goal completion streaks (consecutive weeks)
    - Recent 12-week trend
    """
    service = GoalsService()
    return service.get_goals_summary(user_id=current_user["id"], tz=tz)


@router.get("/streaks/training")
@limiter.limit("120/minute")
def get_training_streaks(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get training session streaks (consecutive days trained)."""
    service = GoalsService()
    return service.get_training_streaks(user_id=current_user["id"])


@router.get("/streaks/goals")
@limiter.limit("120/minute")
def get_goal_completion_streaks(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get weekly goal completion streaks."""
    service = GoalsService()
    return service.get_goal_completion_streak(user_id=current_user["id"])


@router.get("/trend")
@limiter.limit("120/minute")
def get_recent_trend(
    request: Request, weeks: int = 12, current_user: dict = Depends(get_current_user)
):
    """Get goal completion trend for recent weeks.

    Args:
        weeks: Number of recent weeks to include (default 12)
    """
    service = GoalsService()
    try:
        if weeks < 1 or weeks > 52:
            raise ValidationError("Weeks must be between 1 and 52")
        return service.get_recent_weeks_trend(user_id=current_user["id"], weeks=weeks)
    except HTTPException:
        raise


@router.put("/targets")
@limiter.limit("30/minute")
def update_goal_targets(
    request: Request,
    targets: GoalTargetsUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update weekly goal targets in profile.

    Body:
        weekly_sessions_target: Target sessions per week (e.g., 3)
        weekly_hours_target: Target hours per week (e.g., 4.5)
        weekly_rolls_target: Target rolls per week (e.g., 15)

    Returns updated profile.
    """
    service = GoalsService()
    profile = service.update_profile_goals(
        user_id=current_user["id"],
        weekly_sessions_target=targets.weekly_sessions_target,
        weekly_hours_target=targets.weekly_hours_target,
        weekly_rolls_target=targets.weekly_rolls_target,
    )
    return profile
