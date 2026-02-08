"""Public gym routes for authenticated users."""

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.services.gym_service import GymService

router = APIRouter(prefix="/gyms", tags=["gyms"])
limiter = Limiter(key_func=get_remote_address)


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
