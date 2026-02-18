"""Admin routes for gym management (CRUD, merge, verify, classes, timetable)."""

import logging

from fastapi import APIRouter, Body, Depends, Path, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.audit_service import AuditService
from rivaflow.core.services.gym_service import GymService
from rivaflow.db.repositories.gym_class_repo import GymClassRepository

from .admin import get_client_ip, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


# Pydantic models
class GymCreateRequest(BaseModel):
    """Request model for creating a gym."""

    name: str = Field(..., min_length=1, max_length=200)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=50)
    country: str = Field("Australia", max_length=100)
    address: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=500)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    head_coach: str | None = Field(None, max_length=200)
    head_coach_belt: str | None = Field(None, max_length=20)
    google_maps_url: str | None = Field(None, max_length=1000)
    verified: bool = False


class GymUpdateRequest(BaseModel):
    """Request model for updating a gym."""

    name: str | None = Field(None, min_length=1, max_length=200)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=500)
    email: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=50)
    head_coach: str | None = Field(None, max_length=200)
    head_coach_belt: str | None = Field(None, max_length=20)
    google_maps_url: str | None = Field(None, max_length=1000)
    verified: bool | None = None


class GymMergeRequest(BaseModel):
    """Request model for merging gyms."""

    source_gym_id: int = Field(..., gt=0)
    target_gym_id: int = Field(..., gt=0)


class GymClassRequest(BaseModel):
    """Request model for a single gym class."""

    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    class_name: str = Field(..., min_length=1, max_length=200)
    class_type: str | None = Field(None, max_length=50)
    level: str | None = Field(None, max_length=50)


class BulkTimetableRequest(BaseModel):
    """Request model for bulk-setting a gym timetable."""

    classes: list[GymClassRequest]


# Gym management endpoints
@router.get("/gyms")
@limiter.limit("60/minute")
@route_error_handler("list_gyms", detail="Failed to list gyms")
def list_gyms(
    request: Request,
    verified_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """List all gyms (admin only)."""
    gym_service = GymService()
    gyms = gym_service.list_all(verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.get("/gyms/pending")
@limiter.limit("60/minute")
@route_error_handler("get_pending_gyms", detail="Failed to get pending gyms")
def get_pending_gyms(request: Request, current_user: dict = Depends(require_admin)):
    """Get all pending (unverified) gyms."""
    gym_service = GymService()
    pending = gym_service.get_pending_gyms()
    return {
        "pending_gyms": pending,
        "count": len(pending),
    }


@router.get("/gyms/search")
@limiter.limit("60/minute")
@route_error_handler("search_gyms", detail="Failed to search gyms")
def search_gyms(
    request: Request,
    q: str = "",
    verified_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """Search gyms by name or location."""
    if not q or len(q) < 2:
        return {"gyms": []}

    gym_service = GymService()
    gyms = gym_service.search(q, verified_only=verified_only)
    return {
        "gyms": gyms,
        "count": len(gyms),
    }


@router.post("/gyms")
@limiter.limit("30/minute")
@route_error_handler("create_gym", detail="Failed to create gym")
def create_gym(
    request: Request,
    gym_data: GymCreateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Create a new gym (admin only)."""
    gym_service = GymService()
    gym = gym_service.create(
        name=gym_data.name,
        city=gym_data.city,
        state=gym_data.state,
        country=gym_data.country,
        address=gym_data.address,
        website=gym_data.website,
        email=gym_data.email,
        phone=gym_data.phone,
        head_coach=gym_data.head_coach,
        head_coach_belt=gym_data.head_coach_belt,
        google_maps_url=gym_data.google_maps_url,
        verified=gym_data.verified,
        added_by_user_id=current_user["id"],
    )

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.create",
        target_type="gym",
        target_id=gym["id"],
        details={"name": gym["name"], "verified": gym_data.verified},
        ip_address=get_client_ip(request),
    )

    return gym


@router.put("/gyms/{gym_id}")
@limiter.limit("30/minute")
@route_error_handler("update_gym", detail="Failed to update gym")
def update_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    gym_data: GymUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update a gym (admin only)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Filter out None values
    update_data = {k: v for k, v in gym_data.model_dump().items() if v is not None}

    updated_gym = gym_service.update(gym_id, **update_data)

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.update",
        target_type="gym",
        target_id=gym_id,
        details={"changes": update_data, "name": gym["name"]},
        ip_address=get_client_ip(request),
    )

    return updated_gym


@router.delete("/gyms/{gym_id}")
@limiter.limit("10/minute")
@route_error_handler("delete_gym", detail="Failed to delete gym")
def delete_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a gym (admin only)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    gym_name = gym["name"]
    success = gym_service.delete(gym_id)

    # Audit log
    if success:
        AuditService.log(
            actor_id=current_user["id"],
            action="gym.delete",
            target_type="gym",
            target_id=gym_id,
            details={"name": gym_name},
            ip_address=get_client_ip(request),
        )

    return {"message": "Gym deleted"} if success else {"message": "Gym deletion failed"}


@router.post("/gyms/{gym_id}/verify")
@limiter.limit("30/minute")
@route_error_handler("verify_gym", detail="Failed to verify gym")
def verify_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Verify a gym (mark as verified by admin)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Update gym to verified
    updated = gym_service.update(gym_id, verified=True)

    if not updated:
        raise ValidationError("Failed to verify gym")

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.verify",
        target_type="gym",
        target_id=gym_id,
        details={"name": gym["name"], "verified": True},
        ip_address=get_client_ip(request),
    )

    return {
        "gym": updated,
        "message": f"Gym '{gym['name']}' has been verified",
    }


@router.post("/gyms/{gym_id}/reject")
@limiter.limit("30/minute")
@route_error_handler("reject_gym", detail="Failed to reject gym")
def reject_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    reason: str | None = Body(None, embed=True),
    current_user: dict = Depends(require_admin),
):
    """Reject a gym verification (mark as unverified)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Update gym to unverified
    updated = gym_service.update(gym_id, verified=False)

    if not updated:
        raise ValidationError("Failed to reject gym")

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.reject",
        target_type="gym",
        target_id=gym_id,
        details={"name": gym["name"], "verified": False, "reason": reason},
        ip_address=get_client_ip(request),
    )

    return {
        "gym": updated,
        "message": f"Gym '{gym['name']}' verification has been rejected",
    }


@router.post("/gyms/merge")
@limiter.limit("10/minute")
@route_error_handler("merge_gyms", detail="Failed to merge gyms")
def merge_gyms(
    request: Request,
    merge_data: GymMergeRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Merge duplicate gyms (admin only)."""
    # Prevent merging a gym into itself
    if merge_data.source_gym_id == merge_data.target_gym_id:
        raise ValidationError("Cannot merge a gym into itself")

    # Verify both gyms exist
    gym_service = GymService()
    source = gym_service.get_by_id(merge_data.source_gym_id)
    target = gym_service.get_by_id(merge_data.target_gym_id)

    if not source:
        raise NotFoundError(f"Source gym {merge_data.source_gym_id} not found")
    if not target:
        raise NotFoundError(f"Target gym {merge_data.target_gym_id} not found")

    try:
        gym_service.merge_gyms(merge_data.source_gym_id, merge_data.target_gym_id)

        # Audit log
        AuditService.log(
            actor_id=current_user["id"],
            action="gym.merge",
            target_type="gym",
            target_id=merge_data.target_gym_id,
            details={
                "source_gym_id": merge_data.source_gym_id,
                "source_gym_name": source["name"],
                "target_gym_name": target["name"],
            },
            ip_address=get_client_ip(request),
        )

        return {
            "message": f"Merged '{source['name']}' into '{target['name']}'",
        }
    except Exception as e:
        # Transaction will be rolled back automatically by the context manager
        logger.error(f"Failed to merge gyms: {e}")
        raise ValidationError("Failed to merge gyms")


# ── Gym timetable management ──


@router.post("/gyms/{gym_id}/timetable")
@limiter.limit("30/minute")
@route_error_handler("set_timetable", detail="Failed to set timetable")
def set_timetable(
    request: Request,
    gym_id: int = Path(..., gt=0),
    body: BulkTimetableRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Bulk-set timetable for a gym (replaces all existing classes)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym {gym_id} not found")

    repo = GymClassRepository()
    class_dicts = [c.model_dump() for c in body.classes]
    ids = repo.bulk_replace(gym_id, class_dicts)

    gym_service._invalidate_timetable_cache(gym_id)

    AuditService.log(
        actor_id=current_user["id"],
        action="gym.timetable.set",
        target_type="gym",
        target_id=gym_id,
        details={
            "name": gym["name"],
            "class_count": len(ids),
        },
        ip_address=get_client_ip(request),
    )

    return {
        "gym_id": gym_id,
        "classes_created": len(ids),
    }


@router.post("/gyms/{gym_id}/classes")
@limiter.limit("30/minute")
@route_error_handler("add_class", detail="Failed to add class")
def add_class(
    request: Request,
    gym_id: int = Path(..., gt=0),
    body: GymClassRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Add a single class to a gym timetable."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym {gym_id} not found")

    repo = GymClassRepository()
    class_id = repo.create(
        gym_id=gym_id,
        day_of_week=body.day_of_week,
        start_time=body.start_time,
        end_time=body.end_time,
        class_name=body.class_name,
        class_type=body.class_type,
        level=body.level,
    )

    gym_service._invalidate_timetable_cache(gym_id)

    AuditService.log(
        actor_id=current_user["id"],
        action="gym.class.add",
        target_type="gym_class",
        target_id=class_id,
        details={
            "gym_name": gym["name"],
            "class_name": body.class_name,
        },
        ip_address=get_client_ip(request),
    )

    return {"class_id": class_id}


@router.put("/gyms/{gym_id}/classes/{class_id}")
@limiter.limit("30/minute")
@route_error_handler("update_class", detail="Failed to update class")
def update_class(
    request: Request,
    gym_id: int = Path(..., gt=0),
    class_id: int = Path(..., gt=0),
    body: GymClassRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update a gym class."""
    repo = GymClassRepository()
    updated = repo.update(
        class_id,
        day_of_week=body.day_of_week,
        start_time=body.start_time,
        end_time=body.end_time,
        class_name=body.class_name,
        class_type=body.class_type,
        level=body.level,
    )
    if not updated:
        raise NotFoundError(f"Class {class_id} not found")

    gym_service = GymService()
    gym_service._invalidate_timetable_cache(gym_id)

    return updated


@router.delete("/gyms/{gym_id}/classes/{class_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_class", detail="Failed to delete class")
def delete_class(
    request: Request,
    gym_id: int = Path(..., gt=0),
    class_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a gym class."""
    repo = GymClassRepository()
    deleted = repo.delete(class_id)
    if not deleted:
        raise NotFoundError(f"Class {class_id} not found")

    gym_service = GymService()
    gym_service._invalidate_timetable_cache(gym_id)

    AuditService.log(
        actor_id=current_user["id"],
        action="gym.class.delete",
        target_type="gym_class",
        target_id=class_id,
        details={"gym_id": gym_id},
        ip_address=get_client_ip(request),
    )

    return {"message": "Class deleted"}
