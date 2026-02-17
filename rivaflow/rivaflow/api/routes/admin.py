"""Admin routes for gym and data management."""

import logging
import time

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Path, Query, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_admin_user
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.audit_service import AuditService
from rivaflow.core.services.gym_service import GymService
from rivaflow.db.repositories.feedback_repo import FeedbackRepository
from rivaflow.db.repositories.gym_class_repo import GymClassRepository
from rivaflow.db.repositories.gym_repo import GymRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


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


# Helper to check if user is admin
def require_admin(current_user: dict = Depends(get_admin_user)) -> dict:
    """
    Dependency to require admin access.

    Now uses centralized get_admin_user dependency which:
    - Returns 403 Forbidden (not 400) for non-admins
    - Logs unauthorized access attempts
    - Provides consistent admin auth across the app
    """
    return current_user


# Helper to get IP address from request
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check X-Forwarded-For header first (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    return "unknown"


# Gym management endpoints
@router.get("/gyms")
@limiter.limit("60/minute")
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

    return {"success": True, "gym": gym}


@router.put("/gyms/{gym_id}")
@limiter.limit("30/minute")
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

    return {"success": True, "gym": updated_gym}


@router.delete("/gyms/{gym_id}")
@limiter.limit("10/minute")
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

    return {"success": success}


@router.post("/gyms/{gym_id}/verify")
@limiter.limit("30/minute")
def verify_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """
    Verify a gym (mark as verified by admin).

    This endpoint marks a gym as verified, which:
    - Shows the gym in verified-only searches
    - Indicates the gym has been reviewed and approved by an admin
    - May give the gym priority in search results

    Returns:
        Updated gym with verified status
    """
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Update gym to verified
    gym_repo = GymRepository()
    updated = gym_repo.update(gym_id, verified=True)

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
        "success": True,
        "gym": updated,
        "message": f"Gym '{gym['name']}' has been verified",
    }


@router.post("/gyms/{gym_id}/reject")
@limiter.limit("30/minute")
def reject_gym(
    request: Request,
    gym_id: int = Path(..., gt=0),
    reason: str | None = Body(None, embed=True),
    current_user: dict = Depends(require_admin),
):
    """
    Reject a gym verification (mark as unverified or delete).

    This endpoint rejects a gym's verification. You can optionally provide
    a reason for the rejection which will be logged in the audit trail.

    Options:
    - Mark as unverified (keeps the gym but marks it unverified)
    - Delete the gym entirely if it's spam or invalid

    For now, this just marks the gym as unverified.

    Returns:
        Updated gym with unverified status
    """
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Update gym to unverified
    gym_repo = GymRepository()
    updated = gym_repo.update(gym_id, verified=False)

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
        "success": True,
        "gym": updated,
        "message": f"Gym '{gym['name']}' verification has been rejected",
    }


@router.post("/gyms/merge")
@limiter.limit("10/minute")
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
        success = gym_service.merge_gyms(
            merge_data.source_gym_id, merge_data.target_gym_id
        )

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
            "success": success,
            "message": f"Merged '{source['name']}' into '{target['name']}'",
        }
    except Exception as e:
        # Transaction will be rolled back automatically by the context manager
        logger.error(f"Failed to merge gyms: {e}")
        raise ValidationError("Failed to merge gyms")


# Dashboard endpoints
@router.get("/dashboard/stats")
@limiter.limit("60/minute")
def get_dashboard_stats(request: Request, current_user: dict = Depends(require_admin)):
    """Get platform statistics for admin dashboard."""
    from rivaflow.core.services.admin_service import AdminService

    stats = AdminService.get_dashboard_stats()

    # Add gym stats (still uses GymService)
    gym_service = GymService()
    total_gyms = len(gym_service.list_all(verified_only=False))
    pending_gyms = len(gym_service.get_pending_gyms())
    verified_gyms = total_gyms - pending_gyms

    return {
        **stats,
        "total_gyms": total_gyms,
        "verified_gyms": verified_gyms,
        "pending_gyms": pending_gyms,
    }


# User management endpoints
class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""

    is_active: bool | None = None
    is_admin: bool | None = None
    subscription_tier: str | None = Field(
        None, pattern="^(free|premium|lifetime_premium|admin)$"
    )
    is_beta_user: bool | None = None


@router.get("/users")
@limiter.limit("60/minute")
def list_users(
    request: Request,
    search: str | None = None,
    is_active: bool | None = None,
    is_admin: bool | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin),
):
    """List all users with optional filters (admin only)."""
    from rivaflow.core.services.admin_service import AdminService

    return AdminService.list_users(
        search=search,
        is_active=is_active,
        is_admin=is_admin,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}")
@limiter.limit("60/minute")
def get_user_details(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Get detailed user information (admin only)."""
    from rivaflow.core.services.admin_service import AdminService

    result = AdminService.get_user_details(user_id)
    if not result:
        raise NotFoundError(f"User {user_id} not found")
    return result


@router.put("/users/{user_id}")
@limiter.limit("30/minute")
def update_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    user_data: UserUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update user (admin only)."""
    from rivaflow.core.services.admin_service import AdminService
    from rivaflow.db.repositories.user_repo import UserRepository

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    changes = {
        k: v
        for k, v in {
            "is_active": user_data.is_active,
            "is_admin": user_data.is_admin,
            "subscription_tier": user_data.subscription_tier,
            "is_beta_user": user_data.is_beta_user,
        }.items()
        if v is not None
    }

    updated_user = AdminService.update_user(user_id, changes)

    if changes:
        AuditService.log(
            actor_id=current_user["id"],
            action="user.update",
            target_type="user",
            target_id=user_id,
            details={"changes": changes, "email": user["email"]},
            ip_address=get_client_ip(request),
        )

    return {"success": True, "user": updated_user}


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
def delete_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete user (admin only). Cascades to all related data."""
    from rivaflow.core.services.admin_service import AdminService
    from rivaflow.db.repositories.user_repo import UserRepository

    if user_id == current_user["id"]:
        raise ValidationError("Cannot delete your own account")

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    user_email = user["email"]
    AdminService.delete_user(user_id)

    AuditService.log(
        actor_id=current_user["id"],
        action="user.delete",
        target_type="user",
        target_id=user_id,
        details={"email": user_email},
        ip_address=get_client_ip(request),
    )

    return {"success": True, "message": f"User {user_email} deleted"}


# Content moderation endpoints
@router.get("/comments")
@limiter.limit("60/minute")
def list_all_comments(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin),
):
    """List all comments for moderation (admin only)."""
    from rivaflow.core.services.admin_service import AdminService

    return AdminService.list_comments(limit=limit, offset=offset)


@router.delete("/comments/{comment_id}")
@limiter.limit("10/minute")
def delete_comment(
    request: Request,
    comment_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a comment (admin only)."""
    from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository

    success = ActivityCommentRepository.delete_admin(comment_id)
    if not success:
        raise NotFoundError(f"Comment {comment_id} not found")

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="comment.delete",
        target_type="comment",
        target_id=comment_id,
        details={},
        ip_address=get_client_ip(request),
    )

    return {"success": True, "message": "Comment deleted"}


# Technique management endpoints
@router.get("/techniques")
@limiter.limit("60/minute")
def list_techniques(
    request: Request,
    search: str | None = None,
    category: str | None = None,
    custom_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """List all techniques for admin management."""
    from rivaflow.core.services.admin_service import AdminService

    return AdminService.list_techniques(
        search=search,
        category=category,
        custom_only=custom_only,
    )


@router.delete("/techniques/{technique_id}")
@limiter.limit("10/minute")
def delete_technique(
    request: Request,
    technique_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a technique (admin only)."""
    from rivaflow.core.services.admin_service import AdminService

    technique_name = AdminService.delete_technique(technique_id)
    if technique_name is None:
        raise NotFoundError(f"Technique {technique_id} not found")

    AuditService.log(
        actor_id=current_user["id"],
        action="technique.delete",
        target_type="technique",
        target_id=technique_id,
        details={"name": technique_name},
        ip_address=get_client_ip(request),
    )

    return {"success": True, "message": "Technique deleted"}


# Audit log endpoints
@router.get("/audit-logs")
@limiter.limit("60/minute")
def get_audit_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    actor_id: int | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    current_user: dict = Depends(require_admin),
):
    """Get audit logs with optional filters (admin only)."""
    logs = AuditService.get_logs(
        limit=limit,
        offset=offset,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
    )

    total = AuditService.get_total_count(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
    )

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# Feedback management endpoints
class FeedbackUpdateStatusRequest(BaseModel):
    """Admin model for updating feedback status."""

    status: str = Field(..., pattern="^(new|reviewing|resolved|closed)$")
    admin_notes: str | None = Field(None, max_length=1000)


@router.get("/feedback")
def get_all_feedback(
    status: str | None = Query(None, pattern="^(new|reviewing|resolved|closed)$"),
    category: str | None = Query(
        None, pattern="^(bug|feature|improvement|question|other)$"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user),
):
    """
    Get all feedback submissions (admin endpoint).

    Filters:
    - status: Filter by status (new, reviewing, resolved, closed)
    - category: Filter by category (bug, feature, improvement, question, other)

    Returns:
        List of all feedback submissions with statistics
    """
    repo = FeedbackRepository()
    feedback_list = repo.list_all(
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    stats = repo.get_stats()

    return {
        "feedback": feedback_list,
        "count": len(feedback_list),
        "stats": stats,
    }


@router.put("/feedback/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int = Path(..., gt=0),
    request: FeedbackUpdateStatusRequest = Body(...),
    current_user: dict = Depends(get_admin_user),
):
    """
    Update the status of a feedback submission (admin endpoint).

    Status values:
    - new: Newly submitted
    - reviewing: Under review
    - resolved: Issue resolved
    - closed: Closed without resolution

    Returns:
        Updated feedback submission
    """
    repo = FeedbackRepository()

    # Check if feedback exists
    feedback = repo.get_by_id(feedback_id)
    if not feedback:
        raise NotFoundError("Feedback not found")

    # Update status
    success = repo.update_status(
        feedback_id=feedback_id,
        status=request.status,
        admin_notes=request.admin_notes,
    )

    if not success:
        raise ValidationError("Failed to update feedback status")

    # Get updated feedback
    updated = repo.get_by_id(feedback_id)

    return {
        "success": True,
        "feedback": updated,
    }


@router.get("/feedback/stats")
def get_feedback_stats(current_user: dict = Depends(get_admin_user)):
    """
    Get feedback statistics (admin endpoint).

    Returns:
        Statistics about feedback submissions
    """
    repo = FeedbackRepository()
    stats = repo.get_stats()

    return stats


# ── Gym timetable management ──


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


@router.post("/gyms/{gym_id}/timetable")
@limiter.limit("30/minute")
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
        "success": True,
        "gym_id": gym_id,
        "classes_created": len(ids),
    }


@router.post("/gyms/{gym_id}/classes")
@limiter.limit("30/minute")
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

    return {"success": True, "class_id": class_id}


@router.put("/gyms/{gym_id}/classes/{class_id}")
@limiter.limit("30/minute")
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

    return {"success": True, "class": updated}


@router.delete("/gyms/{gym_id}/classes/{class_id}")
@limiter.limit("30/minute")
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

    return {"success": True}


# Email broadcast
class BroadcastEmailRequest(BaseModel):
    """Request model for admin email broadcast."""

    subject: str = Field(..., min_length=1, max_length=200)
    html_body: str = Field(..., min_length=1, max_length=500_000)
    text_body: str | None = Field(None, max_length=500_000)


def _send_broadcast_background(
    users: list[dict],
    subject: str,
    html_body: str,
    text_body: str | None,
) -> None:
    """Send broadcast emails in a background thread."""
    from rivaflow.core.services.email_service import EmailService

    email_service = EmailService()
    sent = 0
    failed = 0
    for user in users:
        try:
            first_name = user.get("first_name") or ""
            html = html_body.replace("{{first_name}}", first_name)
            text = (
                text_body.replace("{{first_name}}", first_name) if text_body else None
            )
            ok = email_service.send_email(
                to_email=user["email"],
                subject=subject,
                html_content=html,
                text_content=text,
            )
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1
            logger.debug(
                "Broadcast email failed for user %s",
                user.get("email"),
                exc_info=True,
            )
        time.sleep(0.1)
    logger.info(
        "Broadcast complete: %d sent, %d failed out of %d",
        sent,
        failed,
        len(users),
    )


@router.post("/email/broadcast")
@limiter.limit("5/hour")
def broadcast_email(
    request: Request,
    background_tasks: BackgroundTasks,
    body: BroadcastEmailRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Send a broadcast email to all active users (admin only)."""
    # Sanitize: reject HTML that contains script tags (XSS protection)
    if "<script" in body.html_body.lower():
        raise ValidationError(
            message="HTML body contains disallowed content",
            action="Remove any <script> tags from the email body.",
        )

    from rivaflow.core.services.admin_service import AdminService

    users = AdminService.get_broadcast_users()
    recipient_count = len(users)

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="email.broadcast",
        target_type="email",
        target_id=None,
        details={
            "subject": body.subject,
            "recipient_count": recipient_count,
        },
        ip_address=get_client_ip(request),
    )

    # Send in background task
    background_tasks.add_task(
        _send_broadcast_background,
        users,
        body.subject,
        body.html_body,
        body.text_body,
    )

    return {
        "success": True,
        "message": f"Broadcast queued for {recipient_count} recipients",
        "recipient_count": recipient_count,
    }
