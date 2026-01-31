"""Admin routes for gym and data management."""
from fastapi import APIRouter, Depends, Path, Body
from pydantic import BaseModel, Field
from typing import Optional

from rivaflow.db.repositories.gym_repo import GymRepository
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models
class GymCreateRequest(BaseModel):
    """Request model for creating a gym."""
    name: str = Field(..., min_length=1, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: str = Field("USA", max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    head_coach: Optional[str] = Field(None, max_length=200)
    verified: bool = False


class GymUpdateRequest(BaseModel):
    """Request model for updating a gym."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    head_coach: Optional[str] = Field(None, max_length=200)
    verified: Optional[bool] = None


class GymMergeRequest(BaseModel):
    """Request model for merging gyms."""
    source_gym_id: int = Field(..., gt=0)
    target_gym_id: int = Field(..., gt=0)


# Helper to check if user is admin
def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require admin access."""
    # Check if user has admin role
    if not current_user.get("is_admin"):
        # Fallback: check email domain for backwards compatibility
        if not current_user.get("email", "").endswith(("@rivaflow.com", "@admin.com")):
            # Fallback: allow user_id = 1 for backwards compatibility
            if current_user.get("id") != 1:
                raise ValidationError("Admin access required")
    return current_user


# Gym management endpoints
@router.get("/gyms")
async def list_gyms(
    verified_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """List all gyms (admin only)."""
    gyms = GymRepository.list_all(verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.get("/gyms/pending")
async def get_pending_gyms(current_user: dict = Depends(require_admin)):
    """Get all pending (unverified) gyms."""
    pending = GymRepository.get_pending_gyms()
    return {
        "pending_gyms": pending,
        "count": len(pending),
    }


@router.get("/gyms/search")
async def search_gyms(
    q: str = "",
    verified_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """Search gyms by name or location."""
    if not q or len(q) < 2:
        return {"gyms": []}
    
    gyms = GymRepository.search(q, verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.post("/gyms")
async def create_gym(
    request: GymCreateRequest,
    current_user: dict = Depends(require_admin),
):
    """Create a new gym (admin only)."""
    gym = GymRepository.create(
        name=request.name,
        city=request.city,
        state=request.state,
        country=request.country,
        address=request.address,
        website=request.website,
        email=request.email,
        phone=request.phone,
        head_coach=request.head_coach,
        verified=request.verified,
        added_by_user_id=current_user["id"],
    )
    return {"success": True, "gym": gym}


@router.put("/gyms/{gym_id}")
async def update_gym(
    gym_id: int = Path(..., gt=0),
    request: GymUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update a gym (admin only)."""
    gym = GymRepository.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")
    
    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    updated_gym = GymRepository.update(gym_id, **update_data)
    return {"success": True, "gym": updated_gym}


@router.delete("/gyms/{gym_id}")
async def delete_gym(
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a gym (admin only)."""
    gym = GymRepository.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")
    
    success = GymRepository.delete(gym_id)
    return {"success": success}


@router.post("/gyms/merge")
async def merge_gyms(
    request: GymMergeRequest,
    current_user: dict = Depends(require_admin),
):
    """Merge duplicate gyms (admin only)."""
    # Verify both gyms exist
    source = GymRepository.get_by_id(request.source_gym_id)
    target = GymRepository.get_by_id(request.target_gym_id)
    
    if not source:
        raise NotFoundError(f"Source gym {request.source_gym_id} not found")
    if not target:
        raise NotFoundError(f"Target gym {request.target_gym_id} not found")
    
    success = GymRepository.merge_gyms(request.source_gym_id, request.target_gym_id)
    return {
        "success": success,
        "message": f"Merged '{source['name']}' into '{target['name']}'",
    }
