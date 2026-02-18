"""Repository for Grapple AI Coach rate limiting and token usage tracking."""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from rivaflow.db.database import convert_query, get_connection

logger = logging.getLogger(__name__)


class GrappleUsageRepository:
    """Data access layer for grapple_rate_limits and token_usage_logs tables."""

    # ---- Rate limiting ----

    @staticmethod
    def record_message(
        user_id: int,
        window_start: str,
        window_end: str,
    ) -> None:
        """Insert or increment message count for a user/window."""
        query = convert_query("""
            INSERT INTO grapple_rate_limits
                (id, user_id, window_start, window_end, message_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (user_id, window_start) DO UPDATE SET
                message_count = grapple_rate_limits.message_count + 1
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (str(uuid4()), user_id, window_start, window_end),
            )
            cursor.close()

    @staticmethod
    def get_user_message_count(user_id: int, window_start: str) -> tuple | None:
        """Get message_count and window_end for a user/window.

        Returns (message_count, window_end) or None if no record.
        """
        query = convert_query("""
            SELECT message_count, window_end
            FROM grapple_rate_limits
            WHERE user_id = ? AND window_start = ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, window_start))
            row = cursor.fetchone()
            cursor.close()

            if row:
                return row["message_count"], row["window_end"]
            return None

    @staticmethod
    def get_global_message_count(window_start: str) -> int:
        """Get total message count across all users for a window."""
        query = convert_query("""
            SELECT COALESCE(SUM(message_count), 0) as total
            FROM grapple_rate_limits
            WHERE window_start = ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (window_start,))
            row = cursor.fetchone()
            cursor.close()
            if row:
                return row["total"] or 0
            return 0

    @staticmethod
    def get_user_usage_stats(user_id: int, start_date: str) -> dict[str, Any] | None:
        """Get aggregate usage stats for a user since start_date.

        Returns dict with window_count, total_messages,
        peak_hourly_usage, avg_hourly_usage or None if no data.
        """
        query = convert_query("""
            SELECT
                COUNT(*) as window_count,
                SUM(message_count) as total_messages,
                MAX(message_count) as peak_hourly_usage,
                AVG(message_count) as avg_hourly_usage
            FROM grapple_rate_limits
            WHERE user_id = ? AND window_start >= ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, start_date))
            row = cursor.fetchone()
            cursor.close()

            if row:
                r = dict(row)
                if r["window_count"] and r["window_count"] > 0:
                    return r
            return None

    @staticmethod
    def cleanup_old_records(cutoff_date: str) -> int:
        """Delete rate limit records older than cutoff. Returns count."""
        query = convert_query("DELETE FROM grapple_rate_limits WHERE window_start < ?")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (cutoff_date,))
            deleted_count = cursor.rowcount
            cursor.close()
            return deleted_count

    # ---- Token usage logging ----

    @staticmethod
    def log_token_usage(
        user_id: int,
        session_id: str | None,
        message_id: str | None,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_usd: float,
    ) -> str:
        """Insert a token usage log entry. Returns the log ID."""
        log_id = str(uuid4())

        query = convert_query("""
            INSERT INTO token_usage_logs (
                id, user_id, session_id, message_id, provider, model,
                input_tokens, output_tokens, total_tokens, cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    log_id,
                    user_id,
                    session_id,
                    message_id,
                    provider,
                    model,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cost_usd,
                ),
            )
            cursor.close()

        return log_id

    @staticmethod
    def get_user_usage_by_provider(
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get token usage grouped by provider for a user in a date range."""
        query = convert_query("""
            SELECT
                COUNT(*) as request_count,
                SUM(total_tokens) as total_tokens,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(total_tokens) as avg_tokens_per_request,
                provider
            FROM token_usage_logs
            WHERE user_id = ? AND created_at >= ? AND created_at <= ?
            GROUP BY provider
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(dict(row))
            return results

    @staticmethod
    def get_global_usage_by_provider(
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Get global token usage grouped by provider."""
        query = convert_query("""
            SELECT
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(total_tokens) as avg_tokens_per_request,
                provider
            FROM token_usage_logs
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY provider
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append(dict(row))
            return results

    @staticmethod
    def get_global_unique_users(
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct users across all providers in date range."""
        user_query = convert_query("""
            SELECT COUNT(DISTINCT user_id)
            FROM token_usage_logs
            WHERE created_at >= ? AND created_at <= ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(user_query, (start_date, end_date))
            urow = cursor.fetchone()
            cursor.close()
            if hasattr(urow, "keys"):
                return list(urow.values())[0] or 0
            return urow[0] or 0
