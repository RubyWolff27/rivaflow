"""Service layer for Grapple admin monitoring and feedback."""

import calendar
import logging
from datetime import timedelta
from typing import Any

from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.time_utils import utcnow
from rivaflow.db.repositories.grapple_stats_repo import GrappleStatsRepository

logger = logging.getLogger(__name__)


class GrappleAdminService:
    """Business logic for Grapple admin stats, projections, and feedback."""

    @staticmethod
    def get_global_stats(
        days: int = 30,
    ) -> dict[str, Any]:
        """Get global Grapple usage statistics.

        Combines token monitor stats with session/message counts and tier
        breakdowns from the repository.

        Args:
            days: Look-back window in days.

        Returns:
            Dict with total_users, active_users_7d, total_sessions,
            total_messages, total_tokens, total_cost_usd, by_provider,
            by_tier.
        """
        from rivaflow.core.services.grapple.token_monitor import (
            GrappleTokenMonitor,
        )

        start_date = utcnow() - timedelta(days=days)

        # Token usage from the monitor service
        token_monitor = GrappleTokenMonitor()
        global_stats = token_monitor.get_global_usage_stats(start_date=start_date)

        # Session/message counts from repo
        session_stats = GrappleStatsRepository.get_global_stats(start_date)

        # Active users in last 7 days
        active_users_7d = GrappleStatsRepository.get_active_users_count(
            utcnow() - timedelta(days=7)
        )

        # Stats by subscription tier
        tier_rows = GrappleStatsRepository.get_usage_by_tier(start_date)
        by_tier: dict[str, Any] = {}
        for row in tier_rows:
            tier = row["subscription_tier"]
            by_tier[tier] = {
                "users": row["user_count"],
                "sessions": row["session_count"],
                "messages": row["message_count"],
                "tokens": row["total_tokens"],
                "cost_usd": (float(row["total_cost"]) if row["total_cost"] else 0.0),
            }

        return {
            "total_users": global_stats["totals"]["unique_users"],
            "active_users_7d": active_users_7d,
            "total_sessions": session_stats["total_sessions"] or 0,
            "total_messages": session_stats["total_messages"] or 0,
            "total_tokens": global_stats["totals"]["total_tokens"],
            "total_cost_usd": global_stats["totals"]["total_cost_usd"],
            "by_provider": global_stats["by_provider"],
            "by_tier": by_tier,
        }

    @staticmethod
    def get_projections() -> dict[str, Any]:
        """Calculate cost projections for the current month.

        Uses monthly cost-to-date and recent daily costs to project
        the full-month total.

        Returns:
            Dict with current_month, daily_average, and calculated_at.
        """
        now = utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        cost_this_month = GrappleStatsRepository.get_monthly_cost(month_start)
        daily_costs = GrappleStatsRepository.get_daily_costs(
            since=now - timedelta(days=7), limit=7
        )

        # Average daily cost
        if daily_costs:
            avg_daily_cost = sum(float(row["daily_cost"]) for row in daily_costs) / len(
                daily_costs
            )
        else:
            avg_daily_cost = 0.0

        # Project for the rest of the month
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_elapsed = now.day
        days_remaining = days_in_month - days_elapsed

        projected_month_cost = float(cost_this_month) + (
            float(avg_daily_cost) * days_remaining
        )

        return {
            "current_month": {
                "cost_so_far": round(float(cost_this_month), 6),
                "projected_total": round(projected_month_cost, 6),
                "days_elapsed": days_elapsed,
                "days_remaining": days_remaining,
            },
            "daily_average": {
                "last_7_days": round(float(avg_daily_cost), 6),
                "daily_costs": [
                    {
                        "date": row["dt"],
                        "cost_usd": round(float(row["daily_cost"]), 6),
                    }
                    for row in daily_costs
                ],
            },
            "calculated_at": now.isoformat(),
        }

    @staticmethod
    def get_provider_stats(days: int = 7) -> dict[str, Any]:
        """Get LLM provider usage breakdown.

        Args:
            days: Look-back window in days.

        Returns:
            Dict with period_days, start_date, and providers list.
        """
        start_date = utcnow() - timedelta(days=days)
        rows = GrappleStatsRepository.get_provider_stats(start_date)

        providers = []
        for row in rows:
            providers.append(
                {
                    "provider": row["provider"],
                    "model": row["model"],
                    "request_count": row["request_count"],
                    "total_tokens": row["total_tokens"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_cost_usd": (
                        round(float(row["total_cost"]), 6) if row["total_cost"] else 0.0
                    ),
                    "avg_tokens_per_request": (
                        round(float(row["avg_tokens"]), 2) if row["avg_tokens"] else 0.0
                    ),
                }
            )

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "providers": providers,
        }

    @staticmethod
    def get_top_users(limit: int = 50) -> dict[str, Any]:
        """Get top users by Grapple usage.

        Args:
            limit: Max users to return.

        Returns:
            Dict with users list and total_returned count.
        """
        rows = GrappleStatsRepository.get_top_users(limit=limit)

        users = []
        for row in rows:
            users.append(
                {
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "subscription_tier": row["subscription_tier"],
                    "total_sessions": row["total_sessions"] or 0,
                    "total_messages": row["total_messages"] or 0,
                    "total_tokens": row["total_tokens"] or 0,
                    "total_cost_usd": (
                        round(float(row["total_cost_usd"]), 6)
                        if row["total_cost_usd"]
                        else 0.0
                    ),
                    "last_activity": row["last_activity"],
                }
            )

        return {
            "users": users,
            "total_returned": len(users),
        }

    @staticmethod
    def get_feedback(limit: int = 100, rating: str | None = None) -> dict[str, Any]:
        """Get user feedback on Grapple responses.

        Args:
            limit: Max feedback entries to return.
            rating: Optional filter ('positive' or 'negative').

        Returns:
            Dict with feedback list and total_returned count.
        """
        rows = GrappleStatsRepository.get_feedback(limit=limit, rating=rating)

        feedback_list = []
        for row in rows:
            feedback_list.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "user_email": row["email"],
                    "message_id": row["message_id"],
                    "rating": row["rating"],
                    "category": row["category"],
                    "comment": row["comment"],
                    "created_at": row["created_at"],
                }
            )

        return {
            "feedback": feedback_list,
            "total_returned": len(feedback_list),
        }

    @staticmethod
    def check_health() -> dict[str, Any]:
        """Check Grapple system health (LLM + database).

        Returns:
            Dict with overall_status, llm_client info, database info,
            and checked_at timestamp.
        """
        from rivaflow.core.services.grapple.llm_client import (
            GrappleLLMClient,
        )

        # Check LLM client
        try:
            llm_client = GrappleLLMClient(environment="production")
            provider_status = llm_client.get_provider_status()
            llm_healthy = True
        except Exception as e:
            provider_status = {"error": str(e)}
            llm_healthy = False

        # Check database tables
        try:
            tables_ok = GrappleStatsRepository.check_tables_exist()
        except Exception:
            tables_ok = False

        return {
            "overall_status": (
                "healthy" if (llm_healthy and tables_ok) else "degraded"
            ),
            "llm_client": {
                "status": "healthy" if llm_healthy else "error",
                "providers": provider_status,
            },
            "database": {
                "status": "healthy" if tables_ok else "error",
            },
            "checked_at": utcnow().isoformat(),
        }

    @staticmethod
    def submit_feedback(
        user_id: int,
        message_id: str,
        rating: str,
        category: str | None = None,
        comment: str | None = None,
    ) -> dict[str, str]:
        """Submit feedback on a Grapple assistant message.

        Verifies message ownership before creating the feedback record.

        Args:
            user_id: The user submitting feedback.
            message_id: The assistant message being rated.
            rating: 'positive' or 'negative'.
            category: Optional feedback category.
            comment: Optional free-text comment.

        Returns:
            Dict with feedback_id and confirmation message.

        Raises:
            NotFoundError: If message not found or not owned by user.
        """
        session_id = GrappleStatsRepository.verify_message_ownership(
            message_id, user_id
        )

        if not session_id:
            raise NotFoundError("Message not found or access denied")

        feedback_id = GrappleStatsRepository.create_feedback(
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            category=category,
            comment=comment,
        )

        logger.info(
            "Feedback submitted by user %d: %s for message %s",
            user_id,
            rating,
            message_id,
        )

        return {
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!",
        }
