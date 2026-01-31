"""Admin routes for gym and data management."""
from fastapi import APIRouter, Depends, Path, Body, Request
from pydantic import BaseModel, Field
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.db.repositories.gym_repo import GymRepository
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.audit_service import AuditService
from rivaflow.core.services.gym_service import GymService

router = APIRouter(prefix="/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


# Pydantic models
class GymCreateRequest(BaseModel):
    """Request model for creating a gym."""
    name: str = Field(..., min_length=1, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: str = Field("Australia", max_length=100)
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
    if not current_user.get("is_admin", False):
        raise ValidationError("Admin access required")
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
async def list_gyms(
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
async def get_pending_gyms(request: Request, current_user: dict = Depends(require_admin)):
    """Get all pending (unverified) gyms."""
    gym_service = GymService()
    pending = gym_service.get_pending_gyms()
    return {
        "pending_gyms": pending,
        "count": len(pending),
    }


@router.get("/gyms/search")
@limiter.limit("60/minute")
async def search_gyms(
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
async def create_gym(
    http_request: Request,
    request: GymCreateRequest,
    current_user: dict = Depends(require_admin),
):
    """Create a new gym (admin only)."""
    gym_service = GymService()
    gym = gym_service.create(
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

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.create",
        target_type="gym",
        target_id=gym["id"],
        details={"name": gym["name"], "verified": request.verified},
        ip_address=get_client_ip(http_request),
    )

    return {"success": True, "gym": gym}


@router.put("/gyms/{gym_id}")
@limiter.limit("30/minute")
async def update_gym(
    http_request: Request,
    gym_id: int = Path(..., gt=0),
    request: GymUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update a gym (admin only)."""
    gym_service = GymService()
    gym = gym_service.get_by_id(gym_id)
    if not gym:
        raise NotFoundError(f"Gym with id {gym_id} not found")

    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}

    updated_gym = gym_service.update(gym_id, **update_data)

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="gym.update",
        target_type="gym",
        target_id=gym_id,
        details={"changes": update_data, "name": gym["name"]},
        ip_address=get_client_ip(http_request),
    )

    return {"success": True, "gym": updated_gym}


@router.delete("/gyms/{gym_id}")
@limiter.limit("10/minute")
async def delete_gym(
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


@router.post("/gyms/merge")
@limiter.limit("10/minute")
async def merge_gyms(
    http_request: Request,
    request: GymMergeRequest,
    current_user: dict = Depends(require_admin),
):
    """Merge duplicate gyms (admin only)."""
    # Prevent merging a gym into itself
    if request.source_gym_id == request.target_gym_id:
        raise ValidationError("Cannot merge a gym into itself")

    # Verify both gyms exist
    gym_service = GymService()
    source = gym_service.get_by_id(request.source_gym_id)
    target = gym_service.get_by_id(request.target_gym_id)

    if not source:
        raise NotFoundError(f"Source gym {request.source_gym_id} not found")
    if not target:
        raise NotFoundError(f"Target gym {request.target_gym_id} not found")

    try:
        success = gym_service.merge_gyms(request.source_gym_id, request.target_gym_id)

        # Audit log
        AuditService.log(
            actor_id=current_user["id"],
            action="gym.merge",
            target_type="gym",
            target_id=request.target_gym_id,
            details={
                "source_gym_id": request.source_gym_id,
                "source_gym_name": source["name"],
                "target_gym_name": target["name"],
            },
            ip_address=get_client_ip(http_request),
        )

        return {
            "success": success,
            "message": f"Merged '{source['name']}' into '{target['name']}'",
        }
    except Exception as e:
        # Transaction will be rolled back automatically by the context manager
        raise ValidationError(f"Failed to merge gyms: {str(e)}")


# Dashboard endpoints
@router.get("/dashboard/stats")
@limiter.limit("60/minute")
async def get_dashboard_stats(request: Request, current_user: dict = Depends(require_admin)):
    """Get platform statistics for admin dashboard."""
    from rivaflow.db.repositories.user_repo import UserRepository
    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository
    from rivaflow.db.database import get_connection, convert_query
    from datetime import datetime, timedelta

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
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute(convert_query("""
            SELECT COUNT(DISTINCT user_id) FROM sessions
            WHERE session_date >= ?
        """), (thirty_days_ago,))
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
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM users
            WHERE created_at >= ?
        """), (week_ago,))
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
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


@router.get("/users")
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """List all users with optional filters (admin only)."""
    from rivaflow.db.database import get_connection, convert_query

    with get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT id, email, first_name, last_name, is_active, is_admin, created_at FROM users WHERE 1=1"
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
            count_query += " AND (email LIKE ? OR first_name LIKE ? OR last_name LIKE ?)"
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
        total_count = list(row.values())[0] if isinstance(row, dict) else (row[0] if row else 0)

        return {
            "users": [dict(row) for row in users],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }


@router.get("/users/{user_id}")
@limiter.limit("60/minute")
async def get_user_details(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Get detailed user information (admin only)."""
    from rivaflow.db.repositories.user_repo import UserRepository
    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.database import get_connection, convert_query

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
        cursor.execute(convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"), (user_id,))
        session_count = extract_count(cursor.fetchone())

        # Comment count
        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments WHERE user_id = ?"), (user_id,))
        comment_count = extract_count(cursor.fetchone())

        # Followers
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE following_user_id = ?
        """), (user_id,))
        followers_count = extract_count(cursor.fetchone())

        # Following
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE follower_user_id = ?
        """), (user_id,))
        following_count = extract_count(cursor.fetchone())

    return {
        **user,
        "stats": {
            "sessions": session_count,
            "comments": comment_count,
            "followers": followers_count,
            "following": following_count,
        }
    }


@router.put("/users/{user_id}")
@limiter.limit("30/minute")
async def update_user(
    http_request: Request,
    user_id: int = Path(..., gt=0),
    request: UserUpdateRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Update user (admin only)."""
    from rivaflow.db.repositories.user_repo import UserRepository
    from rivaflow.db.database import get_connection, convert_query

    user = UserRepository.get_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")

    changes = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(request.is_active)
            changes["is_active"] = request.is_active

        if request.is_admin is not None:
            updates.append("is_admin = ?")
            params.append(request.is_admin)
            changes["is_admin"] = request.is_admin

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
            ip_address=get_client_ip(http_request),
        )

    return {"success": True, "user": updated_user}


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete user (admin only). Cascades to all related data."""
    from rivaflow.db.repositories.user_repo import UserRepository
    from rivaflow.db.database import get_connection, convert_query

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
async def list_all_comments(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
):
    """List all comments for moderation (admin only)."""
    from rivaflow.db.database import get_connection, convert_query

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(convert_query("""
            SELECT
                c.id, c.user_id, c.activity_type, c.activity_id,
                c.comment_text, c.created_at,
                u.email, u.first_name, u.last_name
            FROM activity_comments c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """), (limit, offset))

        comments = [dict(row) for row in cursor.fetchall()]

        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
        row = cursor.fetchone()
        # Handle both PostgreSQL (dict) and SQLite (Row) results
        total = list(row.values())[0] if isinstance(row, dict) else (row[0] if row else 0)

        return {
            "comments": comments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.delete("/comments/{comment_id}")
@limiter.limit("10/minute")
async def delete_comment(
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
async def list_techniques(
    request: Request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    custom_only: bool = False,
    current_user: dict = Depends(require_admin),
):
    """List all techniques for admin management."""
    from rivaflow.db.database import get_connection, convert_query

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
async def delete_technique(
    request: Request,
    technique_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a technique (admin only)."""
    from rivaflow.db.database import get_connection, convert_query

    # Get technique name before deleting
    technique_name = None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_query("SELECT name FROM movements_glossary WHERE id = ?"), (technique_id,))
        row = cursor.fetchone()
        if row:
            technique_name = row["name"] if hasattr(row, "__getitem__") else row[0]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_query("DELETE FROM movements_glossary WHERE id = ?"), (technique_id,))
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
async def get_audit_logs(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    actor_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
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
