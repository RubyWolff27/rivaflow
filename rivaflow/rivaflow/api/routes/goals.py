"""Weekly goals and streak tracking endpoints."""

import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import RivaFlowException, ValidationError
from rivaflow.core.services.goals_service import GoalsService

logger = logging.getLogger(__name__)

router = APIRouter()
service = GoalsService()


class GoalTargetsUpdate(BaseModel):
    """Weekly goal targets update."""

    weekly_sessions_target: int | None = None
    weekly_hours_target: float | None = None
    weekly_rolls_target: int | None = None


@router.get("/current-week")
async def get_current_week_progress(current_user: dict = Depends(get_current_user)):
    """Get current week's goal progress.

    Returns progress toward weekly targets:
    - Sessions, hours, rolls
    - Percentage completion
    - Days remaining
    - Completion status
    """
    try:
        logger.info(f"Getting current week progress for user_id={current_user['id']}")
        result = service.get_current_week_progress(user_id=current_user["id"])
        logger.info(
            f"Successfully retrieved current week progress for user_id={current_user['id']}"
        )
        return result
    except (RivaFlowException, HTTPException):
        raise
    except Exception as e:
        logger.error(
            f"ERROR in get_current_week_progress for user_id={current_user['id']}"
        )
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get current week progress: {str(e)}"
        )


@router.get("/summary")
async def get_goals_summary(current_user: dict = Depends(get_current_user)):
    """Get comprehensive goals and streaks overview.

    Returns:
    - Current week progress
    - Training streaks (consecutive days)
    - Goal completion streaks (consecutive weeks)
    - Recent 12-week trend
    """
    return service.get_goals_summary(user_id=current_user["id"])


@router.get("/streaks/training")
async def get_training_streaks(current_user: dict = Depends(get_current_user)):
    """Get training session streaks (consecutive days trained)."""
    return service.get_training_streaks(user_id=current_user["id"])


@router.get("/streaks/goals")
async def get_goal_completion_streaks(current_user: dict = Depends(get_current_user)):
    """Get weekly goal completion streaks."""
    return service.get_goal_completion_streak(user_id=current_user["id"])


@router.get("/trend")
async def get_recent_trend(
    weeks: int = 12, current_user: dict = Depends(get_current_user)
):
    """Get goal completion trend for recent weeks.

    Args:
        weeks: Number of recent weeks to include (default 12)
    """
    try:
        if weeks < 1 or weeks > 52:
            raise ValidationError("Weeks must be between 1 and 52")
        return service.get_recent_weeks_trend(user_id=current_user["id"], weeks=weeks)
    except HTTPException:
        raise


@router.put("/targets")
async def update_goal_targets(
    targets: GoalTargetsUpdate, current_user: dict = Depends(get_current_user)
):
    """Update weekly goal targets in profile.

    Body:
        weekly_sessions_target: Target sessions per week (e.g., 3)
        weekly_hours_target: Target hours per week (e.g., 4.5)
        weekly_rolls_target: Target rolls per week (e.g., 15)

    Returns updated profile.
    """
    profile = service.update_profile_goals(
        user_id=current_user["id"],
        weekly_sessions_target=targets.weekly_sessions_target,
        weekly_hours_target=targets.weekly_hours_target,
        weekly_rolls_target=targets.weekly_rolls_target,
    )
    return profile
