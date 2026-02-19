"""API routes for milestone tracking."""

from fastapi import APIRouter, Depends, Request

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import (
    get_current_user,
    get_milestone_service,
)
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("/achieved")
@limiter.limit("120/minute")
@route_error_handler("get_achieved_milestones", detail="Failed to get milestones")
def get_achieved_milestones(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: MilestoneService = Depends(get_milestone_service),
):
    """Get all achieved milestones."""
    achieved = service.get_all_achieved(user_id=current_user["id"])

    return {"milestones": achieved, "count": len(achieved)}


@router.get("/progress")
@limiter.limit("120/minute")
@route_error_handler(
    "get_milestone_progress", detail="Failed to get milestone progress"
)
def get_milestone_progress(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: MilestoneService = Depends(get_milestone_service),
):
    """Get progress toward next milestones."""
    progress = service.get_progress_to_next(user_id=current_user["id"])

    return {"progress": progress}


@router.get("/closest")
@limiter.limit("120/minute")
@route_error_handler("get_closest_milestone", detail="Failed to get closest milestone")
def get_closest_milestone(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: MilestoneService = Depends(get_milestone_service),
):
    """Get the closest upcoming milestone."""
    closest = service.get_closest_milestone(user_id=current_user["id"])

    if not closest:
        return {"has_milestone": False}

    return {"has_milestone": True, **closest}


@router.get("/totals")
@limiter.limit("120/minute")
@route_error_handler("get_current_totals", detail="Failed to get current totals")
def get_current_totals(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: MilestoneService = Depends(get_milestone_service),
):
    """Get current totals for all milestone types."""
    totals = service.get_current_totals(user_id=current_user["id"])

    return totals
