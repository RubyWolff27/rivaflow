"""API routes for milestone tracking."""
from fastapi import APIRouter
from rivaflow.core.services.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])


@router.get("/achieved")
def get_achieved_milestones():
    """Get all achieved milestones."""
    service = MilestoneService()
    achieved = service.get_all_achieved()

    return {"milestones": achieved, "count": len(achieved)}


@router.get("/progress")
def get_milestone_progress():
    """Get progress toward next milestones."""
    service = MilestoneService()
    progress = service.get_progress_to_next()

    return {"progress": progress}


@router.get("/closest")
def get_closest_milestone():
    """Get the closest upcoming milestone."""
    service = MilestoneService()
    closest = service.get_closest_milestone()

    if not closest:
        return {"has_milestone": False}

    return {
        "has_milestone": True,
        **closest
    }


@router.get("/totals")
def get_current_totals():
    """Get current totals for all milestone types."""
    service = MilestoneService()
    totals = service.get_current_totals()

    return totals
