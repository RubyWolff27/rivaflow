"""Admin routes for user management, content moderation, techniques, audit logs, and feedback."""

import logging

from fastapi import APIRouter, Body, Depends, Path, Query, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_admin_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.audit_service import AuditService
from rivaflow.core.services.feedback_service import FeedbackService

from .admin import get_client_ip, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


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
@route_error_handler("list_users", detail="Failed to list users")
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
@route_error_handler("get_user_details", detail="Failed to get user details")
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
@route_error_handler("update_user", detail="Failed to update user")
def update_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    user_data: UserUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update user (admin only)."""
    from rivaflow.core.services.admin_service import AdminService
    from rivaflow.core.services.user_service import UserService

    user = UserService().get_user_by_id(user_id)
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

    return updated_user


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
@route_error_handler("delete_user", detail="Failed to delete user")
def delete_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete user (admin only). Cascades to all related data."""
    from rivaflow.core.services.admin_service import AdminService
    from rivaflow.core.services.user_service import UserService

    if user_id == current_user["id"]:
        raise ValidationError("Cannot delete your own account")

    user = UserService().get_user_by_id(user_id)
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

    return {"message": f"User {user_email} deleted"}


# Content moderation endpoints
@router.get("/comments")
@limiter.limit("60/minute")
@route_error_handler("list_all_comments", detail="Failed to list comments")
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
@route_error_handler("delete_comment", detail="Failed to delete comment")
def delete_comment(
    request: Request,
    comment_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a comment (admin only)."""
    from rivaflow.core.services.admin_service import AdminService

    success = AdminService.delete_comment(comment_id)
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

    return {"message": "Comment deleted"}


# Technique management endpoints
@router.get("/techniques")
@limiter.limit("60/minute")
@route_error_handler("list_techniques", detail="Failed to list techniques")
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
@route_error_handler("delete_technique", detail="Failed to delete technique")
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

    return {"message": "Technique deleted"}


# Audit log endpoints
@router.get("/audit-logs")
@limiter.limit("60/minute")
@route_error_handler("get_audit_logs", detail="Failed to get audit logs")
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
@route_error_handler("get_all_feedback", detail="Failed to get feedback")
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
    service = FeedbackService()
    feedback_list = service.list_all(
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    stats = service.get_stats()

    return {
        "feedback": feedback_list,
        "count": len(feedback_list),
        "stats": stats,
    }


@router.put("/feedback/{feedback_id}/status")
@route_error_handler(
    "update_feedback_status", detail="Failed to update feedback status"
)
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
    service = FeedbackService()

    # Check if feedback exists
    feedback = service.get_by_id(feedback_id)
    if not feedback:
        raise NotFoundError("Feedback not found")

    # Update status
    success = service.update_status(
        feedback_id=feedback_id,
        status=request.status,
        admin_notes=request.admin_notes,
    )

    if not success:
        raise ValidationError("Failed to update feedback status")

    # Get updated feedback
    updated = service.get_by_id(feedback_id)

    return updated


@router.get("/feedback/stats")
@route_error_handler("get_feedback_stats", detail="Failed to get feedback stats")
def get_feedback_stats(current_user: dict = Depends(get_admin_user)):
    """
    Get feedback statistics (admin endpoint).

    Returns:
        Statistics about feedback submissions
    """
    service = FeedbackService()
    stats = service.get_stats()

    return stats
