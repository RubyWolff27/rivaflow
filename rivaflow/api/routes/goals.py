"""Weekly goals and streak tracking endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.goals_service import GoalsService

router = APIRouter()
service = GoalsService()


class GoalTargetsUpdate(BaseModel):
    """Weekly goal targets update."""

    weekly_sessions_target: Optional[int] = None
    weekly_hours_target: Optional[float] = None
    weekly_rolls_target: Optional[int] = None


@router.get("/current-week")
async def get_current_week_progress():
    """Get current week's goal progress.

    Returns progress toward weekly targets:
    - Sessions, hours, rolls
    - Percentage completion
    - Days remaining
    - Completion status
    """
    try:
        return service.get_current_week_progress()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_goals_summary():
    """Get comprehensive goals and streaks overview.

    Returns:
    - Current week progress
    - Training streaks (consecutive days)
    - Goal completion streaks (consecutive weeks)
    - Recent 12-week trend
    """
    try:
        return service.get_goals_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaks/training")
async def get_training_streaks():
    """Get training session streaks (consecutive days trained)."""
    try:
        return service.get_training_streaks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/streaks/goals")
async def get_goal_completion_streaks():
    """Get weekly goal completion streaks."""
    try:
        return service.get_goal_completion_streak()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_recent_trend(weeks: int = 12):
    """Get goal completion trend for recent weeks.

    Args:
        weeks: Number of recent weeks to include (default 12)
    """
    try:
        if weeks < 1 or weeks > 52:
            raise HTTPException(status_code=400, detail="Weeks must be between 1 and 52")
        return service.get_recent_weeks_trend(weeks=weeks)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/targets")
async def update_goal_targets(targets: GoalTargetsUpdate):
    """Update weekly goal targets in profile.

    Body:
        weekly_sessions_target: Target sessions per week (e.g., 3)
        weekly_hours_target: Target hours per week (e.g., 4.5)
        weekly_rolls_target: Target rolls per week (e.g., 15)

    Returns updated profile.
    """
    try:
        profile = service.update_profile_goals(
            weekly_sessions_target=targets.weekly_sessions_target,
            weekly_hours_target=targets.weekly_hours_target,
            weekly_rolls_target=targets.weekly_rolls_target,
        )
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
