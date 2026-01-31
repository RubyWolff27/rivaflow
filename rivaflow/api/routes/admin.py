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


# Dashboard endpoints
@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(require_admin)):
    """Get platform statistics for admin dashboard."""
    from rivaflow.db.repositories.user_repo import UserRepository
    from rivaflow.db.repositories.session_repo import SessionRepository
    from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository
    from rivaflow.db.database import get_connection, convert_query
    from datetime import datetime, timedelta

    with get_connection() as conn:
        cursor = conn.cursor()

        # Total users
        cursor.execute(convert_query("SELECT COUNT(*) FROM users"))
        row = cursor.fetchone()
        total_users = row[0] if row else 0

        # Active users (logged session in last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute(convert_query("""
            SELECT COUNT(DISTINCT user_id) FROM sessions
            WHERE session_date >= ?
        """), (thirty_days_ago,))
        row = cursor.fetchone()
        active_users = row[0] if row else 0

        # Total sessions
        cursor.execute(convert_query("SELECT COUNT(*) FROM sessions"))
        row = cursor.fetchone()
        total_sessions = row[0] if row else 0

        # Total gyms
        total_gyms = len(GymRepository.list_all(verified_only=False))
        pending_gyms = len(GymRepository.get_pending_gyms())
        verified_gyms = total_gyms - pending_gyms

        # Total comments
        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
        row = cursor.fetchone()
        total_comments = row[0] if row else 0

        # New users this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM users
            WHERE created_at >= ?
        """), (week_ago,))
        row = cursor.fetchone()
        new_users_week = row[0] if row else 0

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
async def list_users(
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
        total_count = row[0] if row else 0

        return {
            "users": [dict(row) for row in users],
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }


@router.get("/users/{user_id}")
async def get_user_details(
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

        # Session count
        cursor.execute(convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"), (user_id,))
        row = cursor.fetchone()
        session_count = row[0] if row else 0

        # Comment count
        cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments WHERE user_id = ?"), (user_id,))
        row = cursor.fetchone()
        comment_count = row[0] if row else 0

        # Followers
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE following_user_id = ?
        """), (user_id,))
        row = cursor.fetchone()
        followers_count = row[0] if row else 0

        # Following
        cursor.execute(convert_query("""
            SELECT COUNT(*) FROM user_relationships WHERE follower_user_id = ?
        """), (user_id,))
        row = cursor.fetchone()
        following_count = row[0] if row else 0

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
async def update_user(
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

    with get_connection() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(request.is_active)

        if request.is_admin is not None:
            updates.append("is_admin = ?")
            params.append(request.is_admin)

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)
            cursor.execute(convert_query(query), params)
            conn.commit()

    updated_user = UserRepository.get_by_id(user_id)
    return {"success": True, "user": updated_user}


@router.delete("/users/{user_id}")
async def delete_user(
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

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_query("DELETE FROM users WHERE id = ?"), (user_id,))
        conn.commit()

    return {"success": True, "message": f"User {user['email']} deleted"}


# Content moderation endpoints
@router.get("/comments")
async def list_all_comments(
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
        total = row[0] if row else 0

        return {
            "comments": comments,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a comment (admin only)."""
    from rivaflow.db.repositories.activity_comment_repo import ActivityCommentRepository

    success = ActivityCommentRepository.delete_admin(comment_id)
    if not success:
        raise NotFoundError(f"Comment {comment_id} not found")

    return {"success": True, "message": "Comment deleted"}


# Technique management endpoints
@router.get("/techniques")
async def list_techniques(
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
async def delete_technique(
    technique_id: int = Path(..., gt=0),
    current_user: dict = Depends(require_admin),
):
    """Delete a technique (admin only)."""
    from rivaflow.db.database import get_connection, convert_query

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(convert_query("DELETE FROM movements_glossary WHERE id = ?"), (technique_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise NotFoundError(f"Technique {technique_id} not found")

    return {"success": True, "message": "Technique deleted"}
