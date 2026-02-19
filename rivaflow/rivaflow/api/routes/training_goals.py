"""Monthly training goals endpoints."""

import logging
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user, get_training_goals_service
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.training_goals_service import TrainingGoalsService

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateTrainingGoal(BaseModel):
    """Request body for creating a training goal."""

    goal_type: str  # 'frequency' | 'technique'
    metric: str  # 'sessions' | 'hours' | 'rolls' | 'submissions' | 'technique_count'
    target_value: int
    month: str  # 'YYYY-MM'
    movement_id: int | None = None
    class_type_filter: str | None = None


class UpdateTrainingGoal(BaseModel):
    """Request body for updating a training goal."""

    target_value: int | None = None
    is_active: bool | None = None


@router.post("/")
@route_error_handler("create_goal", detail="Failed to create goal")
def create_goal(
    body: CreateTrainingGoal,
    current_user: dict = Depends(get_current_user),
    service: TrainingGoalsService = Depends(get_training_goals_service),
):
    """Create a new monthly training goal."""
    try:
        return service.create_goal(
            user_id=current_user["id"],
            goal_type=body.goal_type,
            metric=body.metric,
            target_value=body.target_value,
            month=body.month,
            movement_id=body.movement_id,
            class_type_filter=body.class_type_filter,
        )
    except ValidationError:
        raise


@router.get("/")
@route_error_handler("list_goals", detail="Failed to list goals")
def list_goals(
    month: str | None = None,
    current_user: dict = Depends(get_current_user),
    service: TrainingGoalsService = Depends(get_training_goals_service),
):
    """List training goals for a month with progress. Defaults to current month."""
    if not month:
        month = date.today().strftime("%Y-%m")
    try:
        return service.get_goals_with_progress(user_id=current_user["id"], month=month)
    except ValidationError:
        raise


@router.get("/{goal_id}")
@route_error_handler("get_goal", detail="Failed to get goal")
def get_goal(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    service: TrainingGoalsService = Depends(get_training_goals_service),
):
    """Get a single training goal with progress."""
    try:
        return service.get_goal_with_progress(
            user_id=current_user["id"], goal_id=goal_id
        )
    except NotFoundError:
        raise NotFoundError("Goal not found")


@router.put("/{goal_id}")
@route_error_handler("update_goal", detail="Failed to update goal")
def update_goal(
    goal_id: int,
    body: UpdateTrainingGoal,
    current_user: dict = Depends(get_current_user),
    service: TrainingGoalsService = Depends(get_training_goals_service),
):
    """Update a training goal's target_value or is_active."""
    try:
        return service.update_goal(
            user_id=current_user["id"],
            goal_id=goal_id,
            target_value=body.target_value,
            is_active=body.is_active,
        )
    except NotFoundError:
        raise NotFoundError("Goal not found")
    except ValidationError:
        raise


@router.delete("/{goal_id}")
@route_error_handler("delete_goal", detail="Failed to delete goal")
def delete_goal(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    service: TrainingGoalsService = Depends(get_training_goals_service),
):
    """Delete a training goal."""
    try:
        service.delete_goal(user_id=current_user["id"], goal_id=goal_id)
        return {"message": "Goal deleted"}
    except NotFoundError:
        raise NotFoundError("Goal not found")
