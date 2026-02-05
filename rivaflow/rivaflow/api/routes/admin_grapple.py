"""Admin endpoints for Grapple AI Coach monitoring and management."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.middleware.feature_access import require_admin

router = APIRouter(prefix="/admin/grapple", tags=["admin", "grapple"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class FeedbackRequest(BaseModel):
    """User feedback on a Grapple response."""

    message_id: str
    rating: str  # 'positive' or 'negative'
    category: str | None = None  # 'helpful', 'accurate', 'unclear', etc.
    comment: str | None = None


class UsageStatsResponse(BaseModel):
    """Global usage statistics."""

    total_users: int
    active_users_7d: int
    total_sessions: int
    total_messages: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict[str, Any]
    by_tier: dict[str, Any]


# ============================================================================
# User Feedback Endpoints (Beta/Premium users)
# ============================================================================


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit feedback on a Grapple response.

    Available to all authenticated users (beta/premium/admin).
    """
    from uuid import uuid4

    from rivaflow.db.database import convert_query, get_connection

    user_id = current_user["id"]

    # Verify message exists and belongs to user's session
    verify_query = """
        SELECT cm.session_id
        FROM chat_messages cm
        JOIN chat_sessions cs ON cm.session_id = cs.id
        WHERE cm.id = ? AND cs.user_id = ? AND cm.role = 'assistant'
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(verify_query, (feedback.message_id, user_id))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or access denied",
            )

        session_id = result[0]

        # Insert feedback
        feedback_id = str(uuid4())
        insert_query = convert_query(
            """
            INSERT INTO grapple_feedback (id, user_id, session_id, message_id, rating, category, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        )

        cursor.execute(
            insert_query,
            (
                feedback_id,
                user_id,
                session_id,
                feedback.message_id,
                feedback.rating,
                feedback.category,
                feedback.comment,
            ),
        )
        conn.commit()

    logger.info(
        f"Feedback submitted by user {user_id}: {feedback.rating} for message {feedback.message_id}"
    )

    return {
        "success": True,
        "feedback_id": feedback_id,
        "message": "Thank you for your feedback!",
    }


# ============================================================================
# Admin Monitoring Endpoints
# ============================================================================


@router.get("/stats/global", response_model=UsageStatsResponse)
@require_admin
async def get_global_stats(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Get global Grapple usage statistics.

    Admin only. Shows usage across all users.
    """
    from rivaflow.core.services.grapple.token_monitor import GrappleTokenMonitor
    from rivaflow.db.database import get_connection

    logger.info(f"Admin {current_user['id']} fetching global Grapple stats")

    # Get token usage stats
    token_monitor = GrappleTokenMonitor()
    start_date = datetime.utcnow() - timedelta(days=days)
    global_stats = token_monitor.get_global_usage_stats(start_date=start_date)

    # Get session/message counts
    with get_connection() as conn:
        cursor = conn.cursor()

        # Total sessions and messages
        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT cs.id) as total_sessions,
                COUNT(cm.id) as total_messages
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            WHERE cs.created_at >= ?
        """,
            (start_date,),
        )
        session_stats = cursor.fetchone()

        # Active users in last 7 days
        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM chat_sessions
            WHERE updated_at >= ?
        """,
            (datetime.utcnow() - timedelta(days=7),),
        )
        active_users_7d = cursor.fetchone()[0]

        # Stats by tier
        cursor.execute(
            """
            SELECT
                u.subscription_tier,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(DISTINCT cs.id) as session_count,
                COUNT(cm.id) as message_count,
                COALESCE(SUM(tul.total_tokens), 0) as total_tokens,
                COALESCE(SUM(tul.cost_usd), 0) as total_cost
            FROM users u
            LEFT JOIN chat_sessions cs ON u.id = cs.user_id
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            LEFT JOIN token_usage_logs tul ON u.id = tul.user_id AND tul.created_at >= ?
            WHERE u.subscription_tier IN ('beta', 'premium', 'admin')
            GROUP BY u.subscription_tier
        """,
            (start_date,),
        )
        tier_stats = cursor.fetchall()

    # Format tier stats
    by_tier = {}
    for row in tier_stats:
        tier = row[0]
        by_tier[tier] = {
            "users": row[1],
            "sessions": row[2],
            "messages": row[3],
            "tokens": row[4],
            "cost_usd": float(row[5]) if row[5] else 0.0,
        }

    return UsageStatsResponse(
        total_users=global_stats["totals"]["unique_users"],
        active_users_7d=active_users_7d,
        total_sessions=session_stats[0] if session_stats else 0,
        total_messages=session_stats[1] if session_stats else 0,
        total_tokens=global_stats["totals"]["total_tokens"],
        total_cost_usd=global_stats["totals"]["total_cost_usd"],
        by_provider=global_stats["by_provider"],
        by_tier=by_tier,
    )


@router.get("/stats/projections")
@require_admin
async def get_cost_projections(
    current_user: dict = Depends(get_current_user),
):
    """
    Get cost projections for current month.

    Admin only. Projects total costs based on current usage.
    """
    import calendar
    from datetime import datetime

    from rivaflow.db.database import get_connection

    logger.info(f"Admin {current_user['id']} fetching cost projections")

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Cost so far this month
        cursor.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM token_usage_logs
            WHERE created_at >= ?
        """,
            (month_start,),
        )
        cost_this_month = cursor.fetchone()[0]

        # Average daily cost
        cursor.execute(
            """
            SELECT
                DATE(created_at) as date,
                SUM(cost_usd) as daily_cost
            FROM token_usage_logs
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """,
            (now - timedelta(days=7),),
        )
        daily_costs = cursor.fetchall()

    # Calculate average daily cost
    if daily_costs:
        avg_daily_cost = sum(row[1] for row in daily_costs) / len(daily_costs)
    else:
        avg_daily_cost = 0.0

    # Project for month
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day
    days_remaining = days_in_month - days_elapsed

    projected_month_cost = cost_this_month + (avg_daily_cost * days_remaining)

    return {
        "current_month": {
            "cost_so_far": round(cost_this_month, 6),
            "projected_total": round(projected_month_cost, 6),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
        },
        "daily_average": {
            "last_7_days": round(avg_daily_cost, 6),
            "daily_costs": [{"date": row[0], "cost_usd": round(row[1], 6)} for row in daily_costs],
        },
        "calculated_at": now.isoformat(),
    }


@router.get("/stats/providers")
@require_admin
async def get_provider_stats(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """
    Get LLM provider usage breakdown.

    Admin only. Shows which providers are being used and their reliability.
    """
    from rivaflow.db.database import get_connection

    logger.info(f"Admin {current_user['id']} fetching provider stats")

    start_date = datetime.utcnow() - timedelta(days=days)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Provider usage stats
        cursor.execute(
            """
            SELECT
                provider,
                model,
                COUNT(*) as request_count,
                SUM(total_tokens) as total_tokens,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens,
                SUM(cost_usd) as total_cost,
                AVG(total_tokens) as avg_tokens
            FROM token_usage_logs
            WHERE created_at >= ?
            GROUP BY provider, model
            ORDER BY request_count DESC
        """,
            (start_date,),
        )

        provider_stats = []
        for row in cursor.fetchall():
            provider_stats.append(
                {
                    "provider": row[0],
                    "model": row[1],
                    "request_count": row[2],
                    "total_tokens": row[3],
                    "input_tokens": row[4],
                    "output_tokens": row[5],
                    "total_cost_usd": round(row[6], 6) if row[6] else 0.0,
                    "avg_tokens_per_request": round(row[7], 2) if row[7] else 0.0,
                }
            )

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "providers": provider_stats,
    }


@router.get("/stats/users")
@require_admin
async def get_user_stats(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """
    Get top users by usage.

    Admin only. Shows which users are using Grapple most.
    """
    from rivaflow.db.database import get_connection

    logger.info(f"Admin {current_user['id']} fetching user stats")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Use the view we created in migration
        cursor.execute(
            """
            SELECT
                user_id,
                email,
                subscription_tier,
                total_sessions,
                total_messages,
                total_tokens,
                total_cost_usd,
                last_activity
            FROM grapple_user_usage
            ORDER BY total_messages DESC
            LIMIT ?
        """,
            (limit,),
        )

        users = []
        for row in cursor.fetchall():
            users.append(
                {
                    "user_id": row[0],
                    "email": row[1],
                    "subscription_tier": row[2],
                    "total_sessions": row[3] or 0,
                    "total_messages": row[4] or 0,
                    "total_tokens": row[5] or 0,
                    "total_cost_usd": round(row[6], 6) if row[6] else 0.0,
                    "last_activity": row[7],
                }
            )

    return {
        "users": users,
        "total_returned": len(users),
    }


@router.get("/feedback")
@require_admin
async def get_feedback(
    limit: int = 100,
    rating: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get user feedback on Grapple responses.

    Admin only. Shows feedback to improve the system.
    """
    from rivaflow.db.database import get_connection

    logger.info(f"Admin {current_user['id']} fetching feedback")

    query = """
        SELECT
            f.id,
            f.user_id,
            u.email,
            f.message_id,
            f.rating,
            f.category,
            f.comment,
            f.created_at
        FROM grapple_feedback f
        JOIN users u ON f.user_id = u.id
        WHERE 1=1
    """
    params = []

    if rating:
        query += " AND f.rating = ?"
        params.append(rating)

    query += " ORDER BY f.created_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)

        feedback_list = []
        for row in cursor.fetchall():
            feedback_list.append(
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_email": row[2],
                    "message_id": row[3],
                    "rating": row[4],
                    "category": row[5],
                    "comment": row[6],
                    "created_at": row[7],
                }
            )

    return {
        "feedback": feedback_list,
        "total_returned": len(feedback_list),
    }


@router.get("/health")
@require_admin
async def get_grapple_health(
    current_user: dict = Depends(get_current_user),
):
    """
    Get Grapple system health status.

    Admin only. Shows LLM provider availability and system status.
    """
    from rivaflow.core.services.grapple.llm_client import GrappleLLMClient

    logger.info(f"Admin {current_user['id']} checking Grapple health")

    # Check LLM client
    try:
        llm_client = GrappleLLMClient(environment="production")
        provider_status = llm_client.get_provider_status()
        llm_healthy = True
    except Exception as e:
        provider_status = {"error": str(e)}
        llm_healthy = False

    # Check database tables exist
    from rivaflow.db.database import get_connection

    tables_ok = True
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN ('chat_sessions', 'chat_messages', 'token_usage_logs', 'grapple_feedback')
            """
            )
            tables = [row[0] for row in cursor.fetchall()]
            tables_ok = len(tables) == 4
    except Exception:
        tables_ok = False

    return {
        "overall_status": "healthy" if (llm_healthy and tables_ok) else "degraded",
        "llm_client": {
            "status": "healthy" if llm_healthy else "error",
            "providers": provider_status,
        },
        "database": {
            "status": "healthy" if tables_ok else "error",
        },
        "checked_at": datetime.utcnow().isoformat(),
    }
