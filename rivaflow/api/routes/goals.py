"""Weekly goals and streak tracking endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.goals_service import GoalsService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
service = GoalsService()


class GoalTargetsUpdate(BaseModel):
    """Weekly goal targets update."""

    weekly_sessions_target: Optional[int] = None
    weekly_hours_target: Optional[float] = None
    weekly_rolls_target: Optional[int] = None


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
        return service.get_current_week_progress(user_id=current_user["id"])
    # Global error handler will catch unexpected exceptions

    pass


@router.get("/summary")
async def get_goals_summary(current_user: dict = Depends(get_current_user)):
    """Get comprehensive goals and streaks overview.

    Returns:
    - Current week progress
    - Training streaks (consecutive days)
    - Goal completion streaks (consecutive weeks)
    - Recent 12-week trend
    """
    try:
        return service.get_goals_summary(user_id=current_user["id"])
    # Global error handler will catch unexpected exceptions

    pass


@router.get("/streaks/training")
async def get_training_streaks(current_user: dict = Depends(get_current_user)):
    """Get training session streaks (consecutive days trained)."""
    try:
        return service.get_training_streaks(user_id=current_user["id"])
    # Global error handler will catch unexpected exceptions

    pass


@router.get("/streaks/goals")
async def get_goal_completion_streaks(current_user: dict = Depends(get_current_user)):
    """Get weekly goal completion streaks."""
    try:
        return service.get_goal_completion_streak(user_id=current_user["id"])
    # Global error handler will catch unexpected exceptions

    pass


@router.get("/trend")
async def get_recent_trend(weeks: int = 12, current_user: dict = Depends(get_current_user)):
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
    # Global error handler will catch unexpected exceptions

    pass


@router.put("/targets")
async def update_goal_targets(targets: GoalTargetsUpdate, current_user: dict = Depends(get_current_user)):
    """Update weekly goal targets in profile.

    Body:
        weekly_sessions_target: Target sessions per week (e.g., 3)
        weekly_hours_target: Target hours per week (e.g., 4.5)
        weekly_rolls_target: Target rolls per week (e.g., 15)

    Returns updated profile.
    """
    try:
        profile = service.update_profile_goals(
            user_id=current_user["id"],
            weekly_sessions_target=targets.weekly_sessions_target,
            weekly_hours_target=targets.weekly_hours_target,
            weekly_rolls_target=targets.weekly_rolls_target,
        )
        return profile
    # Global error handler will catch unexpected exceptions

    pass
