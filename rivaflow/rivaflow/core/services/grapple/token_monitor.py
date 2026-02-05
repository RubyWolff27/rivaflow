"""Token usage monitoring and cost tracking for Grapple AI Coach."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from rivaflow.db.database import convert_query, get_connection

logger = logging.getLogger(__name__)


class GrappleTokenMonitor:
    """
    Monitors token usage and tracks costs for Grapple AI Coach.

    Features:
    - Log every LLM request with token counts and costs
    - Per-user cost tracking
    - Cost projections (daily, weekly, monthly)
    - Tier-based cost limit enforcement
    - Provider usage analytics
    """

    def __init__(self):
        """Initialize token monitor."""
        pass

    def log_usage(
        self,
        user_id: int,
        session_id: str | None,
        message_id: str | None,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> str:
        """
        Log a token usage event.

        Args:
            user_id: User ID
            session_id: Chat session ID (optional)
            message_id: Chat message ID (optional)
            provider: LLM provider ('groq', 'together', 'ollama')
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Cost in USD

        Returns:
            Log entry ID
        """
        log_id = str(uuid4())
        total_tokens = input_tokens + output_tokens

        query = convert_query("""
            INSERT INTO token_usage_logs (
                id, user_id, session_id, message_id, provider, model,
                input_tokens, output_tokens, total_tokens, cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        try:
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
                conn.commit()
                cursor.close()

                logger.info(
                    f"Logged usage for user {user_id}: {total_tokens} tokens, ${cost_usd:.6f} via {provider}"
                )
                return log_id

        except Exception as e:
            logger.error(f"Failed to log token usage for user {user_id}: {e}")
            raise

    def get_user_usage(
        self,
        user_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get token usage statistics for a user.

        Args:
            user_id: User ID
            start_date: Start of date range (default: 30 days ago)
            end_date: End of date range (default: now)

        Returns:
            Dict with usage statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = """
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
        """

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (user_id, start_date, end_date))
                rows = cursor.fetchall()
                cursor.close()

                # Aggregate by provider
                by_provider = {}
                totals = {
                    "request_count": 0,
                    "total_tokens": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost_usd": 0.0,
                }

                for row in rows:
                    provider = row[6]
                    by_provider[provider] = {
                        "request_count": row[0],
                        "total_tokens": row[1],
                        "total_input_tokens": row[2],
                        "total_output_tokens": row[3],
                        "total_cost_usd": round(row[4], 6),
                        "avg_tokens_per_request": round(row[5], 2),
                    }

                    # Add to totals
                    totals["request_count"] += row[0]
                    totals["total_tokens"] += row[1]
                    totals["total_input_tokens"] += row[2]
                    totals["total_output_tokens"] += row[3]
                    totals["total_cost_usd"] += row[4]

                totals["total_cost_usd"] = round(totals["total_cost_usd"], 6)
                totals["avg_tokens_per_request"] = (
                    round(totals["total_tokens"] / totals["request_count"], 2)
                    if totals["request_count"] > 0
                    else 0
                )

                return {
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "totals": totals,
                    "by_provider": by_provider,
                }

        except Exception as e:
            logger.error(f"Failed to get usage for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "totals": {
                    "request_count": 0,
                    "total_tokens": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost_usd": 0.0,
                },
                "by_provider": {},
            }

    def get_cost_projection(self, user_id: int) -> dict[str, Any]:
        """
        Project costs for the user based on recent usage.

        Calculates projected costs for:
        - Rest of today
        - This week
        - This month

        Args:
            user_id: User ID

        Returns:
            Dict with cost projections
        """
        now = datetime.utcnow()

        # Get usage for last 7 days to calculate average daily cost
        seven_days_ago = now - timedelta(days=7)
        usage_7d = self.get_user_usage(user_id, seven_days_ago, now)
        avg_daily_cost = usage_7d["totals"]["total_cost_usd"] / 7

        # Get usage for today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        usage_today = self.get_user_usage(user_id, today_start, now)
        cost_today = usage_today["totals"]["total_cost_usd"]

        # Calculate projections
        hours_elapsed_today = now.hour + (now.minute / 60)
        hours_remaining_today = 24 - hours_elapsed_today

        # Project rest of today based on today's hourly rate
        hourly_rate_today = cost_today / hours_elapsed_today if hours_elapsed_today > 0 else 0
        projected_today = cost_today + (hourly_rate_today * hours_remaining_today)

        # Project this week (use average daily cost)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        usage_this_week = self.get_user_usage(user_id, week_start, now)
        cost_this_week = usage_this_week["totals"]["total_cost_usd"]
        days_remaining_this_week = 7 - now.weekday()
        projected_this_week = cost_this_week + (avg_daily_cost * days_remaining_this_week)

        # Project this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_this_month = self.get_user_usage(user_id, month_start, now)
        cost_this_month = usage_this_month["totals"]["total_cost_usd"]

        # Calculate days in current month
        import calendar
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_elapsed_this_month = now.day
        days_remaining_this_month = days_in_month - days_elapsed_this_month

        projected_this_month = cost_this_month + (avg_daily_cost * days_remaining_this_month)

        return {
            "user_id": user_id,
            "avg_daily_cost": round(avg_daily_cost, 6),
            "today": {
                "cost_so_far": round(cost_today, 6),
                "projected_total": round(projected_today, 6),
            },
            "this_week": {
                "cost_so_far": round(cost_this_week, 6),
                "projected_total": round(projected_this_week, 6),
            },
            "this_month": {
                "cost_so_far": round(cost_this_month, 6),
                "projected_total": round(projected_this_month, 6),
            },
            "calculated_at": now.isoformat(),
        }

    def check_cost_limit(self, user_id: int, user_tier: str) -> dict[str, Any]:
        """
        Check if user is approaching or has exceeded their cost limit.

        Args:
            user_id: User ID
            user_tier: User's subscription tier

        Returns:
            Dict with cost limit status
        """
        from rivaflow.core.middleware.feature_access import FeatureAccess

        # Get tier cost limit
        cost_limit = FeatureAccess.get_cost_limit(user_tier)

        # Get current month usage
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_this_month = self.get_user_usage(user_id, month_start, now)
        cost_this_month = usage_this_month["totals"]["total_cost_usd"]

        # Calculate percentage used
        percentage_used = (cost_this_month / cost_limit * 100) if cost_limit > 0 else 0

        # Determine status
        if cost_this_month >= cost_limit:
            status = "exceeded"
        elif percentage_used >= 90:
            status = "warning"
        elif percentage_used >= 75:
            status = "approaching"
        else:
            status = "ok"

        return {
            "user_id": user_id,
            "tier": user_tier,
            "limit_usd": cost_limit,
            "used_usd": round(cost_this_month, 6),
            "remaining_usd": max(0, round(cost_limit - cost_this_month, 6)),
            "percentage_used": round(percentage_used, 2),
            "status": status,
            "can_continue": cost_this_month < cost_limit,
        }

    def get_global_usage_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get global usage statistics across all users (admin only).

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dict with global statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = """
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
        """

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (start_date, end_date))
                rows = cursor.fetchall()
                cursor.close()

                by_provider = {}
                totals = {
                    "unique_users": 0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                }

                for row in rows:
                    provider = row[5]
                    by_provider[provider] = {
                        "unique_users": row[0],
                        "total_requests": row[1],
                        "total_tokens": row[2],
                        "total_cost_usd": round(row[3], 6),
                        "avg_tokens_per_request": round(row[4], 2),
                    }

                    totals["total_requests"] += row[1]
                    totals["total_tokens"] += row[2]
                    totals["total_cost_usd"] += row[3]

                # Get unique users across all providers
                user_query = """
                    SELECT COUNT(DISTINCT user_id)
                    FROM token_usage_logs
                    WHERE created_at >= ? AND created_at <= ?
                """
                cursor = conn.cursor()
                cursor.execute(user_query, (start_date, end_date))
                totals["unique_users"] = cursor.fetchone()[0]
                cursor.close()

                totals["total_cost_usd"] = round(totals["total_cost_usd"], 6)

                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "totals": totals,
                    "by_provider": by_provider,
                }

        except Exception as e:
            logger.error(f"Failed to get global usage stats: {e}")
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "totals": {
                    "unique_users": 0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                },
                "by_provider": {},
            }
