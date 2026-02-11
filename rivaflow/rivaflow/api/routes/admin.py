"""Admin routes for gym and data management."""

import logging
import threading
import time

from fastapi import APIRouter, Body, Depends, Path, Query, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_admin_user
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.audit_service import AuditService
from rivaflow.core.services.gym_service import GymService
from rivaflow.db.repositories.feedback_repo import FeedbackRepository
from rivaflow.db.repositories.gym_repo import GymRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


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
    from datetime import datetime, timedelta

    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        # Helper function to safely extract count from query result
        def get_count(result):
            if not result:
                return 0
            # PostgreSQL with RealDictCursor returns dict, SQLite returns Row
            if isinstance(result, dict):
                # Get the first (and only) value from the dict
                return list(result.values())[0] or 0
            else:
                # SQLite Row object - supports integer indexing
                try:
                    return result[0]
                except (KeyError, IndexError, TypeError):
                    return 0

        # Total users
        cursor.execute(convert_query("SELECT COUNT(*) FROM users"))
        total_users = get_count(cursor.fetchone())

        # Active users (logged session in last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute(
            convert_query("""
            SELECT COUNT(DISTINCT user_id) FROM sessions
            WHERE session_date >= ?
        """),
            (thirty_days_ago,),
        )
        active_users = get_count(cursor.fetchone())

        # Total sessions
        cursor.execute(convert_query("SELECT COUNT(*) FROM sessions"))
        total_sessions = get_count(cursor.fetchone())

        # Total gyms
        gym_service = GymService()
        total_gyms = len(gym_service.list_all(verified_only=False))
        pending_gyms = len(gym_service.get_pending_gyms())
        verified_gyms = total_gyms - pending_gyms

        # Total comments
        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
        total_comments = get_count(cursor.fetchone())

        # New users this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            convert_query("""
            SELECT COUNT(*) FROM users
            WHERE created_at >= ?
        """),
            (week_ago,),
        )
        new_users_week = get_count(cursor.fetchone())

    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_week": new_users_week,
        "total_sessions": total_sessions,
        "total_gyms": total_gyms,
        "verified_gyms": verified_gyms,
        "pending_gyms": pending_gyms,
        "total_comments": total_comments,
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
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """List all users with optional filters (admin only)."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT id, email, first_name, last_name, is_active, is_admin, subscription_tier, is_beta_user, created_at FROM users WHERE 1=1"
        params = []

        if search:
            query += " AND (email LIKE ? OR first_name LIKE ? OR last_name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)

        if is_admin is not None:
            query += " AND is_admin = ?"
            params.append(is_admin)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(convert_query(query), params)
        users = cursor.fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM users WHERE 1=1"
        count_params = []
        if search:
            count_query += (
                " AND (email LIKE ? OR first_name LIKE ? OR last_name LIKE ?)"
            )
            count_params.extend([search_term, search_term, search_term])
        if is_active is not None:
            count_query += " AND is_active = ?"
            count_params.append(is_active)
        if is_admin is not None:
            count_query += " AND is_admin = ?"
            count_params.append(is_admin)

        cursor.execute(convert_query(count_query), count_params)
        row = cursor.fetchone()
        # Handle both PostgreSQL (dict) and SQLite (Row) results
        total_count = (
            list(row.values())[0] if isinstance(row, dict) else (row[0] if row else 0)
        )

        return {
            "users": [dict(row) for row in users],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }


@router.get("/users/{user_id}")
@limiter.limit("60/minute")
def get_user_details(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Get detailed user information (admin only)."""
    from rivaflow.db.database import convert_query, get_connection
    from rivaflow.db.repositories.user_repo import UserRepository

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    # Get user stats
    with get_connection() as conn:
        cursor = conn.cursor()

        # Helper to extract count from result (works with both PostgreSQL dict and SQLite Row)
        def extract_count(result):
            if not result:
                return 0
            return list(result.values())[0] if isinstance(result, dict) else result[0]

        # Session count
        cursor.execute(
            convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"), (user_id,)
        )
        session_count = extract_count(cursor.fetchone())

        # Comment count
        cursor.execute(
            convert_query("SELECT COUNT(*) FROM activity_comments WHERE user_id = ?"),
            (user_id,),
        )
        comment_count = extract_count(cursor.fetchone())

        # Followers
        cursor.execute(
            convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE following_user_id = ?
        """),
            (user_id,),
        )
        followers_count = extract_count(cursor.fetchone())

        # Following
        cursor.execute(
            convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE follower_user_id = ?
        """),
            (user_id,),
        )
        following_count = extract_count(cursor.fetchone())

    return {
        **user,
        "stats": {
            "sessions": session_count,
            "comments": comment_count,
            "followers": followers_count,
            "following": following_count,
        },
    }


@router.put("/users/{user_id}")
@limiter.limit("30/minute")
def update_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    user_data: UserUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update user (admin only)."""
    from rivaflow.db.database import convert_query, get_connection
    from rivaflow.db.repositories.user_repo import UserRepository

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    # Valid fields that can be updated (whitelist for SQL safety)
    valid_admin_update_fields = {
        "is_active",
        "is_admin",
        "subscription_tier",
        "is_beta_user",
    }

    changes = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        field_values = {
            "is_active": user_data.is_active,
            "is_admin": user_data.is_admin,
            "subscription_tier": user_data.subscription_tier,
            "is_beta_user": user_data.is_beta_user,
        }

        for field, value in field_values.items():
            if field not in valid_admin_update_fields:
                raise ValueError(f"Invalid field: {field}")
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
                changes[field] = value

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            cursor.execute(convert_query(query), params)
            conn.commit()

    updated_user = UserRepository.get_by_id(user_id)

    # Audit log
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
    from rivaflow.db.database import convert_query, get_connection
    from rivaflow.db.repositories.user_repo import UserRepository

    if user_id == current_user["id"]:
        raise ValidationError("Cannot delete your own account")

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    user_email = user["email"]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_query("DELETE FROM users WHERE id = ?"), (user_id,))
        conn.commit()

    # Audit log
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
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """List all comments for moderation (admin only)."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            convert_query("""
            SELECT
                c.id, c.user_id, c.activity_type, c.activity_id,
                c.comment_text, c.created_at,
                u.email, u.first_name, u.last_name
            FROM activity_comments c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """),
            (limit, offset),
        )

        comments = [dict(row) for row in cursor.fetchall()]

        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
        row = cursor.fetchone()
        # Handle both PostgreSQL (dict) and SQLite (Row) results
        total = (
            list(row.values())[0] if isinstance(row, dict) else (row[0] if row else 0)
        )

        return {
            "comments": comments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


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
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, name, category, subcategory, custom, user_id,
                   gi_applicable, nogi_applicable
            FROM movements_glossary WHERE 1=1
        """
        params = []

        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")

        if category:
            query += " AND category = ?"
            params.append(category)

        if custom_only:
            query += " AND custom = 1"

        query += " ORDER BY name"

        cursor.execute(convert_query(query), params)
        techniques = [dict(row) for row in cursor.fetchall()]

        return {
            "techniques": techniques,
            "count": len(techniques),
        }


@router.delete("/techniques/{technique_id}")
@limiter.limit("10/minute")
def delete_technique(
    request: Request,
    technique_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a technique (admin only)."""
    from rivaflow.db.database import convert_query, get_connection

    # Get technique name before deleting
    technique_name = None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT name FROM movements_glossary WHERE id = ?"),
            (technique_id,),
        )
        row = cursor.fetchone()
        if row:
            technique_name = row["name"] if hasattr(row, "__getitem__") else row[0]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("DELETE FROM movements_glossary WHERE id = ?"),
            (technique_id,),
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise NotFoundError(f"Technique {technique_id} not found")

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="technique.delete",
        target_type="technique",
        target_id=technique_id,
        details={"name": technique_name} if technique_name else {},
        ip_address=get_client_ip(request),
    )

    return {"success": True, "message": "Technique deleted"}


# Audit log endpoints
@router.get("/audit-logs")
@limiter.limit("60/minute")
def get_audit_logs(
    request: Request,
    limit: int = 100,
    offset: int = 0,
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


# Email broadcast
class BroadcastEmailRequest(BaseModel):
    """Request model for admin email broadcast."""

    subject: str = Field(..., min_length=1, max_length=200)
    html_body: str = Field(..., min_length=1)
    text_body: str | None = None


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
    body: BroadcastEmailRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Send a broadcast email to all active users (admin only)."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "SELECT id, email, first_name FROM users" " WHERE is_active = ?"
            ),
            (1,),
        )
        rows = cursor.fetchall()
        users = [dict(r) for r in rows]

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

    # Send in background thread
    t = threading.Thread(
        target=_send_broadcast_background,
        args=(users, body.subject, body.html_body, body.text_body),
        daemon=True,
    )
    t.start()

    return {
        "success": True,
        "message": f"Broadcast queued for {recipient_count} recipients",
        "recipient_count": recipient_count,
    }
