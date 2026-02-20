"""Repository for Grapple admin statistics and feedback data access."""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GrappleStatsRepository(BaseRepository):
    """Data access layer for Grapple admin stats, feedback, and health checks."""

    # ---- Session / message counts ----

    @staticmethod
    def get_global_stats(start_date: datetime) -> dict[str, Any]:
        """Get total session and message counts since start_date.

        Returns:
            Dict with total_sessions and total_messages.
        """
        query = convert_query("""
            SELECT
                COUNT(DISTINCT cs.id) as total_sessions,
                COUNT(cm.id) as total_messages
            FROM chat_sessions cs
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            WHERE cs.created_at >= ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date,))
            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    "total_sessions": row["total_sessions"],
                    "total_messages": row["total_messages"],
                }
            return {"total_sessions": 0, "total_messages": 0}

    # ---- Active users ----

    @staticmethod
    def get_active_users_count(since: datetime) -> int:
        """Get count of distinct users with chat activity since a date.

        Args:
            since: Datetime threshold for activity.

        Returns:
            Number of distinct active users.
        """
        query = convert_query("""
            SELECT COUNT(DISTINCT user_id) as cnt
            FROM chat_sessions
            WHERE updated_at >= ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (since,))
            row = cursor.fetchone()
            cursor.close()
            return row["cnt"] if row else 0

    # ---- Usage by tier ----

    @staticmethod
    def get_usage_by_tier(start_date: datetime) -> list[dict[str, Any]]:
        """Get usage stats grouped by subscription tier.

        Args:
            start_date: Only count token usage logs from this date onward.

        Returns:
            List of dicts with subscription_tier, user_count, session_count,
            message_count, total_tokens, total_cost.
        """
        query = convert_query("""
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
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    # ---- Monthly cost ----

    @staticmethod
    def get_monthly_cost(month_start: datetime) -> float:
        """Get total cost in USD since month_start.

        Args:
            month_start: Start of the billing month.

        Returns:
            Total cost as float.
        """
        query = convert_query("""
            SELECT COALESCE(SUM(cost_usd), 0) as cost
            FROM token_usage_logs
            WHERE created_at >= ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (month_start,))
            row = cursor.fetchone()
            cursor.close()
            return float(row["cost"]) if row else 0.0

    # ---- Daily costs ----

    @staticmethod
    def get_daily_costs(since: datetime, limit: int = 7) -> list[dict[str, Any]]:
        """Get daily cost breakdown, most recent first.

        Args:
            since: Only include days from this date onward.
            limit: Max number of days to return.

        Returns:
            List of dicts with dt and daily_cost.
        """
        query = convert_query("""
            SELECT
                DATE(created_at) as dt,
                SUM(cost_usd) as daily_cost
            FROM token_usage_logs
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY dt DESC
            LIMIT ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (since, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    # ---- Provider stats ----

    @staticmethod
    def get_provider_stats(start_date: datetime) -> list[dict[str, Any]]:
        """Get provider/model usage breakdown since start_date.

        Args:
            start_date: Only include logs from this date onward.

        Returns:
            List of dicts with provider, model, request_count, total_tokens,
            input_tokens, output_tokens, total_cost, avg_tokens.
        """
        query = convert_query("""
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
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date,))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    # ---- Top users ----

    @staticmethod
    def get_top_users(limit: int = 20, since_days: int = 90) -> list[dict[str, Any]]:
        """Get top users by message count.

        Args:
            limit: Max users to return.
            since_days: Only include activity from the last N days
                        (default 90). Prevents scanning entire history.

        Returns:
            List of dicts with user_id, email, subscription_tier,
            total_sessions, total_messages, total_tokens,
            total_cost_usd, last_activity.
        """
        query = convert_query("""
            SELECT
                u.id as user_id,
                u.email,
                u.subscription_tier,
                COUNT(DISTINCT cs.id) as total_sessions,
                COUNT(cm.id) as total_messages,
                COALESCE(SUM(tul.total_tokens), 0) as total_tokens,
                COALESCE(SUM(tul.cost_usd), 0) as total_cost_usd,
                MAX(cs.updated_at) as last_activity
            FROM users u
            LEFT JOIN chat_sessions cs
                ON u.id = cs.user_id
                AND cs.created_at >= date('now', '-' || ? || ' days')
            LEFT JOIN chat_messages cm ON cs.id = cm.session_id
            LEFT JOIN token_usage_logs tul
                ON u.id = tul.user_id
                AND tul.created_at >= date('now', '-' || ? || ' days')
            WHERE u.subscription_tier IN ('beta', 'premium', 'admin')
            GROUP BY u.id, u.email, u.subscription_tier
            HAVING COUNT(cs.id) > 0
            ORDER BY COUNT(cm.id) DESC
            LIMIT ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (since_days, since_days, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    # ---- Health check ----

    @staticmethod
    def check_tables_exist() -> bool:
        """Check that all required Grapple tables exist.

        Returns:
            True if all required tables are present.
        """
        from rivaflow.core.settings import settings

        required_tables = {
            "chat_sessions",
            "chat_messages",
            "token_usage_logs",
            "grapple_feedback",
        }

        with get_connection() as conn:
            cursor = conn.cursor()
            if settings.DB_TYPE == "postgresql":
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name IN (
                        'chat_sessions', 'chat_messages',
                        'token_usage_logs', 'grapple_feedback'
                    )
                """)
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name IN (
                        'chat_sessions', 'chat_messages',
                        'token_usage_logs', 'grapple_feedback'
                    )
                """)

            found = {
                row["table_name" if settings.DB_TYPE == "postgresql" else "name"]
                for row in cursor.fetchall()
            }
            cursor.close()
            return required_tables <= found

    # ---- Message ownership verification ----

    @staticmethod
    def verify_message_ownership(message_id: str, user_id: int) -> str | None:
        """Verify an assistant message belongs to a user's session.

        Args:
            message_id: The chat message ID.
            user_id: The user ID to verify ownership.

        Returns:
            The session_id if valid, or None.
        """
        query = convert_query("""
            SELECT cm.session_id
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cm.id = ? AND cs.user_id = ? AND cm.role = 'assistant'
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (message_id, user_id))
            row = cursor.fetchone()
            cursor.close()

            if row:
                return row["session_id"]
            return None

    # ---- Feedback ----

    @staticmethod
    def create_feedback(
        user_id: int,
        session_id: str,
        message_id: str,
        rating: str,
        category: str | None = None,
        comment: str | None = None,
    ) -> str:
        """Insert a grapple feedback record.

        Args:
            user_id: User who submitted feedback.
            session_id: Chat session the message belongs to.
            message_id: The assistant message being rated.
            rating: 'positive' or 'negative'.
            category: Optional feedback category.
            comment: Optional free-text comment.

        Returns:
            The generated feedback ID.
        """
        feedback_id = str(uuid4())
        query = convert_query("""
            INSERT INTO grapple_feedback
                (id, user_id, session_id, message_id, rating, category, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    feedback_id,
                    user_id,
                    session_id,
                    message_id,
                    rating,
                    category,
                    comment,
                ),
            )
            cursor.close()

        return feedback_id

    # ---- Feedback listing (admin) ----

    @staticmethod
    def get_feedback(
        limit: int = 100,
        rating: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get grapple feedback records, newest first.

        Args:
            limit: Max records to return.
            rating: Optional filter by rating value.

        Returns:
            List of feedback dicts.
        """
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
        params: list = []

        if rating:
            query += " AND f.rating = ?"
            params.append(rating)

        query += " ORDER BY f.created_at DESC LIMIT ?"
        params.append(limit)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(query), params)
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]
