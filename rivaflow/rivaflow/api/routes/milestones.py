"""API routes for milestone tracking."""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/achieved")
@limiter.limit("120/minute")
def get_achieved_milestones(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get all achieved milestones."""
    service = MilestoneService()
    achieved = service.get_all_achieved(user_id=current_user["id"])

    return {"milestones": achieved, "count": len(achieved)}


@router.get("/progress")
@limiter.limit("120/minute")
def get_milestone_progress(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get progress toward next milestones."""
    service = MilestoneService()
    progress = service.get_progress_to_next(user_id=current_user["id"])

    return {"progress": progress}


@router.get("/closest")
@limiter.limit("120/minute")
def get_closest_milestone(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get the closest upcoming milestone."""
    service = MilestoneService()
    closest = service.get_closest_milestone(user_id=current_user["id"])

    if not closest:
        return {"has_milestone": False}

    return {"has_milestone": True, **closest}


@router.get("/totals")
@limiter.limit("120/minute")
def get_current_totals(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get current totals for all milestone types."""
    service = MilestoneService()
    totals = service.get_current_totals(user_id=current_user["id"])

    return totals
