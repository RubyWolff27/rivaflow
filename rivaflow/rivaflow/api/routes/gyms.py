"""Public gym routes for authenticated users."""

from fastapi import APIRouter, Depends, Path, Query, Request

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.gym_service import GymService

router = APIRouter(prefix="/gyms", tags=["gyms"])


@router.get("")
@limiter.limit("120/minute")
def list_gyms(
    request: Request,
    verified_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
):
    """List gyms available for selection (authenticated users)."""
    gym_service = GymService()
    gyms = gym_service.list_all(verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.get("/search")
@limiter.limit("120/minute")
def search_gyms(
    request: Request,
    q: str = "",
    verified_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
):
    """Search gyms by name or location (authenticated users)."""
    if not q or len(q) < 2:
        return {"gyms": []}

    gym_service = GymService()
    gyms = gym_service.search(q, verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.get("/{gym_id}/timetable")
@limiter.limit("120/minute")
def get_timetable(
    request: Request,
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Get full weekly timetable for a gym."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym {gym_id} not found")
    timetable = gym_service.get_timetable(gym_id)
    return {"gym_id": gym_id, "gym_name": gym["name"], "timetable": timetable}


@router.get("/{gym_id}/timetable/today")
@limiter.limit("120/minute")
def get_todays_classes(
    request: Request,
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """Get today's classes at a gym."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym {gym_id} not found")
    classes = gym_service.get_todays_classes(gym_id)
    return {
        "gym_id": gym_id,
        "gym_name": gym["name"],
        "classes": classes,
    }
