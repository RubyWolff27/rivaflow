"""API routes for milestone tracking."""

from fastapi import APIRouter, Depends

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("/achieved")
def get_achieved_milestones(current_user: dict = Depends(get_current_user)):
    """Get all achieved milestones."""
    service = MilestoneService()
    achieved = service.get_all_achieved(user_id=current_user["id"])

    return {"milestones": achieved, "count": len(achieved)}


@router.get("/progress")
def get_milestone_progress(current_user: dict = Depends(get_current_user)):
    """Get progress toward next milestones."""
    service = MilestoneService()
    progress = service.get_progress_to_next(user_id=current_user["id"])

    return {"progress": progress}


@router.get("/closest")
def get_closest_milestone(current_user: dict = Depends(get_current_user)):
    """Get the closest upcoming milestone."""
    service = MilestoneService()
    closest = service.get_closest_milestone(user_id=current_user["id"])

    if not closest:
        return {"has_milestone": False}

    return {"has_milestone": True, **closest}


@router.get("/totals")
def get_current_totals(current_user: dict = Depends(get_current_user)):
    """Get current totals for all milestone types."""
    service = MilestoneService()
    totals = service.get_current_totals(user_id=current_user["id"])

    return totals
