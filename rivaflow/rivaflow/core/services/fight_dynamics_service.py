"""Service for fight dynamics analytics (Attack vs Defence Heatmap)."""

import logging
from datetime import date, timedelta
from typing import Any

from rivaflow.db.database import convert_query, get_connection

logger = logging.getLogger(__name__)


class FightDynamicsService:
    """Business logic for fight dynamics heatmap and insights."""

    def get_heatmap_data(
        self,
        user_id: int,
        view: str = "weekly",
        weeks: int = 8,
        months: int = 6,
    ) -> list[dict[str, Any]]:
        """
        Get aggregated attack/defence data for heatmap display.

        Args:
            user_id: User ID
            view: "weekly" or "monthly"
            weeks: Number of weeks to return (for weekly view)
            months: Number of months to return (for monthly view)

        Returns:
            List of period objects with aggregated fight dynamics data.
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            if view == "monthly":
                return self._get_monthly_data(cursor, user_id, months)
            else:
                return self._get_weekly_data(cursor, user_id, weeks)

    def _get_weekly_data(
        self,
        cursor: Any,
        user_id: int,
        weeks: int,
    ) -> list[dict[str, Any]]:
        """Get weekly aggregated fight dynamics data."""
        today = date.today()
        start_date = today - timedelta(weeks=weeks)

        cursor.execute(
            convert_query("""
                SELECT
                    session_date,
                    attacks_attempted,
                    attacks_successful,
                    defenses_attempted,
                    defenses_successful
                FROM sessions
                WHERE user_id = ?
                    AND session_date >= ?
                    AND (
                        attacks_attempted > 0
                        OR defenses_attempted > 0
                    )
                ORDER BY session_date ASC
                """),
            (user_id, start_date.isoformat()),
        )
        rows = cursor.fetchall()

        # Build weekly buckets
        weekly_buckets: dict[str, dict[str, Any]] = {}
        for i in range(weeks):
            week_start = today - timedelta(weeks=weeks - 1 - i)
            # Align to Monday
            week_start = week_start - timedelta(days=week_start.weekday())
            week_end = week_start + timedelta(days=6)
            week_key = week_start.isoformat()
            week_label = (
                f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}"
            )
            weekly_buckets[week_key] = {
                "period_start": week_start.isoformat(),
                "period_end": week_end.isoformat(),
                "period_label": week_label,
                "attacks_attempted": 0,
                "attacks_successful": 0,
                "defenses_attempted": 0,
                "defenses_successful": 0,
                "session_count": 0,
            }

        # Fill buckets with data
        for row in rows:
            row_dict = dict(row)
            session_date = row_dict["session_date"]
            if isinstance(session_date, str):
                session_date = date.fromisoformat(session_date)

            # Find which weekly bucket this session belongs to
            week_start = session_date - timedelta(days=session_date.weekday())
            week_key = week_start.isoformat()

            if week_key in weekly_buckets:
                bucket = weekly_buckets[week_key]
                bucket["attacks_attempted"] += row_dict["attacks_attempted"] or 0
                bucket["attacks_successful"] += row_dict["attacks_successful"] or 0
                bucket["defenses_attempted"] += row_dict["defenses_attempted"] or 0
                bucket["defenses_successful"] += row_dict["defenses_successful"] or 0
                bucket["session_count"] += 1

        return list(weekly_buckets.values())

    def _get_monthly_data(
        self,
        cursor: Any,
        user_id: int,
        months: int,
    ) -> list[dict[str, Any]]:
        """Get monthly aggregated fight dynamics data."""
        today = date.today()

        # Build monthly buckets
        monthly_buckets: dict[str, dict[str, Any]] = {}
        for i in range(months):
            offset = months - 1 - i
            year = today.year
            month = today.month - offset
            while month <= 0:
                month += 12
                year -= 1
            month_start = date(year, month, 1)
            # Calculate month end
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)

            month_key = month_start.strftime("%Y-%m")
            month_label = month_start.strftime("%b %Y")
            monthly_buckets[month_key] = {
                "period_start": month_start.isoformat(),
                "period_end": month_end.isoformat(),
                "period_label": month_label,
                "attacks_attempted": 0,
                "attacks_successful": 0,
                "defenses_attempted": 0,
                "defenses_successful": 0,
                "session_count": 0,
            }

        # Get the start date (first day of the earliest month)
        earliest_key = min(monthly_buckets.keys())
        start_date = date.fromisoformat(monthly_buckets[earliest_key]["period_start"])

        cursor.execute(
            convert_query("""
                SELECT
                    session_date,
                    attacks_attempted,
                    attacks_successful,
                    defenses_attempted,
                    defenses_successful
                FROM sessions
                WHERE user_id = ?
                    AND session_date >= ?
                    AND (
                        attacks_attempted > 0
                        OR defenses_attempted > 0
                    )
                ORDER BY session_date ASC
                """),
            (user_id, start_date.isoformat()),
        )
        rows = cursor.fetchall()

        for row in rows:
            row_dict = dict(row)
            session_date = row_dict["session_date"]
            if isinstance(session_date, str):
                session_date = date.fromisoformat(session_date)

            month_key = session_date.strftime("%Y-%m")
            if month_key in monthly_buckets:
                bucket = monthly_buckets[month_key]
                bucket["attacks_attempted"] += row_dict["attacks_attempted"] or 0
                bucket["attacks_successful"] += row_dict["attacks_successful"] or 0
                bucket["defenses_attempted"] += row_dict["defenses_attempted"] or 0
                bucket["defenses_successful"] += row_dict["defenses_successful"] or 0
                bucket["session_count"] += 1

        return list(monthly_buckets.values())

    def get_insights(self, user_id: int) -> dict[str, Any]:
        """
        Generate auto-generated insights by comparing recent vs previous periods.

        Compares last 4 weeks to the previous 4 weeks.
        Only generates insights when 3+ sessions have fight dynamics data.

        Returns:
            Dict with offensive_trend, defensive_trend, attack_success_rate,
            defense_success_rate, imbalance_detection, suggested_focus.
        """
        today = date.today()
        recent_start = today - timedelta(weeks=4)
        previous_start = today - timedelta(weeks=8)

        with get_connection() as conn:
            cursor = conn.cursor()

            # Get recent period data (last 4 weeks)
            recent = self._get_period_totals(cursor, user_id, recent_start, today)

            # Get previous period data (4-8 weeks ago)
            previous = self._get_period_totals(
                cursor, user_id, previous_start, recent_start
            )

        # Check minimum data threshold
        total_sessions = recent["session_count"] + previous["session_count"]
        if total_sessions < 3:
            return {
                "has_sufficient_data": False,
                "message": (
                    "Need at least 3 sessions with fight dynamics data "
                    "to generate insights."
                ),
                "sessions_with_data": total_sessions,
                "sessions_needed": 3,
            }

        # Calculate success rates
        attack_success_rate = self._calc_rate(
            recent["attacks_successful"], recent["attacks_attempted"]
        )
        defense_success_rate = self._calc_rate(
            recent["defenses_successful"], recent["defenses_attempted"]
        )

        prev_attack_rate = self._calc_rate(
            previous["attacks_successful"], previous["attacks_attempted"]
        )
        prev_defense_rate = self._calc_rate(
            previous["defenses_successful"], previous["defenses_attempted"]
        )

        # Determine trends
        offensive_trend = self._determine_trend(
            recent["attacks_attempted"],
            previous["attacks_attempted"],
            attack_success_rate,
            prev_attack_rate,
        )

        defensive_trend = self._determine_trend(
            recent["defenses_attempted"],
            previous["defenses_attempted"],
            defense_success_rate,
            prev_defense_rate,
        )

        # Detect imbalance
        imbalance = self._detect_imbalance(
            recent["attacks_attempted"],
            recent["defenses_attempted"],
            attack_success_rate,
            defense_success_rate,
        )

        # Generate suggested focus
        suggested_focus = self._suggest_focus(
            attack_success_rate,
            defense_success_rate,
            recent["attacks_attempted"],
            recent["defenses_attempted"],
            offensive_trend,
            defensive_trend,
        )

        return {
            "has_sufficient_data": True,
            "sessions_with_data": total_sessions,
            "recent_period": {
                "start": recent_start.isoformat(),
                "end": today.isoformat(),
                "session_count": recent["session_count"],
                "attacks_attempted": recent["attacks_attempted"],
                "attacks_successful": recent["attacks_successful"],
                "defenses_attempted": recent["defenses_attempted"],
                "defenses_successful": recent["defenses_successful"],
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": recent_start.isoformat(),
                "session_count": previous["session_count"],
                "attacks_attempted": previous["attacks_attempted"],
                "attacks_successful": previous["attacks_successful"],
                "defenses_attempted": previous["defenses_attempted"],
                "defenses_successful": previous["defenses_successful"],
            },
            "offensive_trend": offensive_trend,
            "defensive_trend": defensive_trend,
            "attack_success_rate": attack_success_rate,
            "defense_success_rate": defense_success_rate,
            "imbalance_detection": imbalance,
            "suggested_focus": suggested_focus,
        }

    def _get_period_totals(
        self,
        cursor: Any,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> dict[str, int]:
        """Get aggregated fight dynamics totals for a date range."""
        cursor.execute(
            convert_query("""
                SELECT
                    COUNT(*) as session_count,
                    COALESCE(SUM(attacks_attempted), 0) as attacks_attempted,
                    COALESCE(SUM(attacks_successful), 0) as attacks_successful,
                    COALESCE(SUM(defenses_attempted), 0) as defenses_attempted,
                    COALESCE(SUM(defenses_successful), 0) as defenses_successful
                FROM sessions
                WHERE user_id = ?
                    AND session_date >= ?
                    AND session_date < ?
                    AND (
                        attacks_attempted > 0
                        OR defenses_attempted > 0
                    )
                """),
            (user_id, start_date.isoformat(), end_date.isoformat()),
        )
        row = cursor.fetchone()
        if row is None:
            return {
                "session_count": 0,
                "attacks_attempted": 0,
                "attacks_successful": 0,
                "defenses_attempted": 0,
                "defenses_successful": 0,
            }
        row_dict = dict(row)
        return {
            "session_count": row_dict["session_count"] or 0,
            "attacks_attempted": row_dict["attacks_attempted"] or 0,
            "attacks_successful": row_dict["attacks_successful"] or 0,
            "defenses_attempted": row_dict["defenses_attempted"] or 0,
            "defenses_successful": row_dict["defenses_successful"] or 0,
        }

    @staticmethod
    def _calc_rate(successful: int, attempted: int) -> float:
        """Calculate a success rate as a percentage."""
        if attempted == 0:
            return 0.0
        return round((successful / attempted) * 100, 1)

    @staticmethod
    def _determine_trend(
        recent_attempted: int,
        previous_attempted: int,
        recent_rate: float,
        previous_rate: float,
    ) -> dict[str, Any]:
        """Determine the trend direction and magnitude."""
        # Volume trend
        if previous_attempted == 0:
            if recent_attempted > 0:
                volume_change = "increasing"
                volume_pct = 100.0
            else:
                volume_change = "stable"
                volume_pct = 0.0
        else:
            volume_pct = round(
                ((recent_attempted - previous_attempted) / previous_attempted) * 100,
                1,
            )
            if volume_pct > 10:
                volume_change = "increasing"
            elif volume_pct < -10:
                volume_change = "decreasing"
            else:
                volume_change = "stable"

        # Rate trend
        rate_change = round(recent_rate - previous_rate, 1)
        if rate_change > 5:
            rate_direction = "improving"
        elif rate_change < -5:
            rate_direction = "declining"
        else:
            rate_direction = "stable"

        return {
            "volume_change": volume_change,
            "volume_change_pct": volume_pct,
            "rate_direction": rate_direction,
            "rate_change_pct": rate_change,
        }

    @staticmethod
    def _detect_imbalance(
        attacks_attempted: int,
        defenses_attempted: int,
        attack_rate: float,
        defense_rate: float,
    ) -> dict[str, Any]:
        """Detect attack/defence imbalance."""
        total = attacks_attempted + defenses_attempted
        if total == 0:
            return {
                "detected": False,
                "type": "none",
                "description": "No data available to assess balance.",
            }

        attack_ratio = attacks_attempted / total
        defense_ratio = defenses_attempted / total

        if attack_ratio > 0.7:
            return {
                "detected": True,
                "type": "attack_heavy",
                "attack_ratio": round(attack_ratio * 100, 1),
                "defense_ratio": round(defense_ratio * 100, 1),
                "description": (
                    "Training is heavily attack-focused. "
                    "Consider dedicating more time to defensive drills."
                ),
            }
        elif defense_ratio > 0.7:
            return {
                "detected": True,
                "type": "defense_heavy",
                "attack_ratio": round(attack_ratio * 100, 1),
                "defense_ratio": round(defense_ratio * 100, 1),
                "description": (
                    "Training is heavily defence-focused. "
                    "Consider working more on offensive techniques."
                ),
            }

        # Check success rate imbalance
        rate_diff = abs(attack_rate - defense_rate)
        if rate_diff > 25:
            weaker = "attack" if attack_rate < defense_rate else "defence"
            return {
                "detected": True,
                "type": f"rate_imbalance_{weaker}",
                "attack_ratio": round(attack_ratio * 100, 1),
                "defense_ratio": round(defense_ratio * 100, 1),
                "description": (
                    f"Your {weaker} success rate is significantly lower. "
                    f"Focus on improving {weaker} effectiveness."
                ),
            }

        return {
            "detected": False,
            "type": "balanced",
            "attack_ratio": round(attack_ratio * 100, 1),
            "defense_ratio": round(defense_ratio * 100, 1),
            "description": ("Good balance between attack and defence training."),
        }

    @staticmethod
    def _suggest_focus(
        attack_rate: float,
        defense_rate: float,
        attacks_attempted: int,
        defenses_attempted: int,
        offensive_trend: dict[str, Any],
        defensive_trend: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a suggested training focus based on current metrics."""
        suggestions = []

        # Low attack success rate
        if attack_rate < 40 and attacks_attempted > 0:
            suggestions.append(
                {
                    "area": "attack_accuracy",
                    "priority": "high",
                    "message": (
                        "Attack success rate is below 40%. "
                        "Focus on setting up attacks with better positioning."
                    ),
                }
            )

        # Low defense success rate
        if defense_rate < 40 and defenses_attempted > 0:
            suggestions.append(
                {
                    "area": "defense_accuracy",
                    "priority": "high",
                    "message": (
                        "Defence success rate is below 40%. "
                        "Work on defensive reactions and escape drills."
                    ),
                }
            )

        # Declining offensive trend
        if offensive_trend["rate_direction"] == "declining":
            suggestions.append(
                {
                    "area": "offensive_momentum",
                    "priority": "medium",
                    "message": (
                        "Offensive effectiveness is declining. "
                        "Review recent attack strategies and adapt."
                    ),
                }
            )

        # Declining defensive trend
        if defensive_trend["rate_direction"] == "declining":
            suggestions.append(
                {
                    "area": "defensive_momentum",
                    "priority": "medium",
                    "message": (
                        "Defensive effectiveness is declining. "
                        "Dedicate more drilling time to defence."
                    ),
                }
            )

        # Low volume areas
        total = attacks_attempted + defenses_attempted
        if total > 0:
            if attacks_attempted / total < 0.3:
                suggestions.append(
                    {
                        "area": "attack_volume",
                        "priority": "medium",
                        "message": (
                            "Very few attacks being attempted. "
                            "Try to initiate more offensive exchanges."
                        ),
                    }
                )
            if defenses_attempted / total < 0.3:
                suggestions.append(
                    {
                        "area": "defense_volume",
                        "priority": "medium",
                        "message": (
                            "Very few defences being recorded. "
                            "Practice working from disadvantaged positions."
                        ),
                    }
                )

        if not suggestions:
            suggestions.append(
                {
                    "area": "maintain",
                    "priority": "low",
                    "message": (
                        "Good balance and effectiveness. "
                        "Continue current training approach."
                    ),
                }
            )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 2))

        return {
            "primary_focus": suggestions[0] if suggestions else None,
            "all_suggestions": suggestions,
        }
