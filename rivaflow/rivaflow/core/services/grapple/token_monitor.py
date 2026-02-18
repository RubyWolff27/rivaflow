"""Token usage monitoring and cost tracking for Grapple AI Coach."""

import logging
from datetime import datetime, timedelta
from typing import Any

from rivaflow.core.time_utils import utcnow
from rivaflow.db.repositories.grapple_usage_repo import GrappleUsageRepository

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
        total_tokens = input_tokens + output_tokens

        try:
            log_id = GrappleUsageRepository.log_token_usage(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
            )

            logger.info(
                f"Logged usage for user {user_id}: {total_tokens} tokens, ${cost_usd:.6f} via {provider}"
            )
            return log_id

        except (ConnectionError, OSError) as e:
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
            start_date = utcnow() - timedelta(days=30)
        if not end_date:
            end_date = utcnow()

        try:
            rows = GrappleUsageRepository.get_user_usage_by_provider(
                user_id, start_date, end_date
            )

            # Aggregate by provider
            by_provider = {}
            totals = {
                "request_count": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
            }

            for r in rows:
                provider = r["provider"]
                by_provider[provider] = {
                    "request_count": r["request_count"],
                    "total_tokens": r["total_tokens"],
                    "total_input_tokens": r["total_input_tokens"],
                    "total_output_tokens": r["total_output_tokens"],
                    "total_cost_usd": round(float(r["total_cost_usd"] or 0), 6),
                    "avg_tokens_per_request": round(
                        float(r["avg_tokens_per_request"] or 0), 2
                    ),
                }

                # Add to totals
                totals["request_count"] += r["request_count"]
                totals["total_tokens"] += r["total_tokens"]
                totals["total_input_tokens"] += r["total_input_tokens"]
                totals["total_output_tokens"] += r["total_output_tokens"]
                totals["total_cost_usd"] += float(r["total_cost_usd"] or 0)

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

        except (ConnectionError, OSError) as e:
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
        now = utcnow()

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
        hourly_rate_today = (
            cost_today / hours_elapsed_today if hours_elapsed_today > 0 else 0
        )
        projected_today = cost_today + (hourly_rate_today * hours_remaining_today)

        # Project this week (use average daily cost)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        usage_this_week = self.get_user_usage(user_id, week_start, now)
        cost_this_week = usage_this_week["totals"]["total_cost_usd"]
        days_remaining_this_week = 7 - now.weekday()
        projected_this_week = cost_this_week + (
            avg_daily_cost * days_remaining_this_week
        )

        # Project this month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage_this_month = self.get_user_usage(user_id, month_start, now)
        cost_this_month = usage_this_month["totals"]["total_cost_usd"]

        # Calculate days in current month
        import calendar

        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_elapsed_this_month = now.day
        days_remaining_this_month = days_in_month - days_elapsed_this_month

        projected_this_month = cost_this_month + (
            avg_daily_cost * days_remaining_this_month
        )

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
        now = utcnow()
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
            start_date = utcnow() - timedelta(days=30)
        if not end_date:
            end_date = utcnow()

        try:
            rows = GrappleUsageRepository.get_global_usage_by_provider(
                start_date, end_date
            )

            by_provider = {}
            totals = {
                "unique_users": 0,
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }

            for r in rows:
                provider = r["provider"]
                by_provider[provider] = {
                    "unique_users": r["unique_users"],
                    "total_requests": r["total_requests"],
                    "total_tokens": r["total_tokens"],
                    "total_cost_usd": round(float(r["total_cost_usd"] or 0), 6),
                    "avg_tokens_per_request": round(
                        float(r["avg_tokens_per_request"] or 0), 2
                    ),
                }

                totals["total_requests"] += r["total_requests"]
                totals["total_tokens"] += r["total_tokens"]
                totals["total_cost_usd"] += float(r["total_cost_usd"] or 0)

            # Get unique users across all providers
            totals["unique_users"] = GrappleUsageRepository.get_global_unique_users(
                start_date, end_date
            )

            totals["total_cost_usd"] = round(totals["total_cost_usd"], 6)

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "totals": totals,
                "by_provider": by_provider,
            }

        except (ConnectionError, OSError) as e:
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
