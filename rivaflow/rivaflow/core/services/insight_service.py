"""Daily insight generation."""

import random
from datetime import date, timedelta

from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.settings import settings
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.streak_repo import StreakRepository


class InsightService:
    """Business logic for generating contextual daily insights."""

    def __init__(self):
        self.streak_repo = StreakRepository()
        self.milestone_service = MilestoneService()

    def generate_insight(self, user_id: int) -> dict:
        """
        Generate a contextual insight based on user's data.

        Returns dict with:
        - type: 'stat', 'technique', 'partner', 'trend', 'encouragement', 'recovery'
        - title: short title
        - message: the insight text
        - action: optional action suggestion
        - icon: emoji icon
        """
        insights = []

        # Collect all possible insights
        insights.extend(self._get_stat_insights(user_id))
        insights.extend(self._get_streak_insights(user_id))
        insights.extend(self._get_milestone_insights(user_id))
        insights.extend(self._get_recovery_insights(user_id))
        insights.extend(self._get_trend_insights(user_id))

        # Select one insight (weighted by relevance)
        if insights:
            # Weight insights by type priority
            weighted_insights = []
            for insight in insights:
                weight = {
                    "milestone": 10,  # Highest priority
                    "streak": 8,
                    "recovery": 6,
                    "trend": 5,
                    "stat": 4,
                    "encouragement": 2,
                }.get(insight["type"], 1)
                weighted_insights.extend([insight] * weight)

            return random.choice(weighted_insights)

        return self._get_default_insight()

    def _get_stat_insights(self, user_id: int) -> list[dict]:
        """Generate insights comparing current week to average."""
        insights = []

        with get_connection() as conn:
            cursor = conn.cursor()

            # Get this week's hours
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

            cursor.execute(
                convert_query("""
                SELECT SUM(duration_mins) as total FROM sessions
                WHERE session_date >= ? AND user_id = ?
            """),
                (week_start.isoformat(), user_id),
            )
            result = cursor.fetchone()
            week_mins = result["total"] or 0
            week_hours = round(week_mins / 60, 1)

            # Get 4-week average
            four_weeks_ago = today - timedelta(days=28)

            # Database-specific week formatting
            if settings.DB_TYPE == "postgresql":
                week_format = "to_char(session_date::date, 'IYYY-IW')"
            else:
                week_format = "strftime('%Y-%W', session_date)"

            cursor.execute(
                convert_query(f"""
                SELECT AVG(weekly_mins) as avg FROM (
                    SELECT SUM(duration_mins) as weekly_mins
                    FROM sessions
                    WHERE session_date >= ? AND session_date < ? AND user_id = ?
                    GROUP BY {week_format}
                ) subq
            """),
                (four_weeks_ago.isoformat(), week_start.isoformat(), user_id),
            )
            result = cursor.fetchone()
            avg_mins = result["avg"] or 0
            avg_hours = round(avg_mins / 60, 1)

            if avg_hours > 0 and week_hours > 0:
                percent_diff = round(((week_hours - avg_hours) / avg_hours) * 100)

                if percent_diff > 15:
                    insights.append(
                        {
                            "type": "stat",
                            "title": "Training volume up",
                            "message": f"You've trained {week_hours} hours this week — {percent_diff}% more than your 4-week average.",
                            "action": None,
                            "icon": "📈",
                        }
                    )
                elif percent_diff < -15:
                    insights.append(
                        {
                            "type": "stat",
                            "title": "Recovery week",
                            "message": f"You've trained {week_hours} hours this week — {abs(percent_diff)}% less than average. Recovery matters.",
                            "action": None,
                            "icon": "📉",
                        }
                    )

        return insights

    def _get_streak_insights(self, user_id: int) -> list[dict]:
        """Generate insights about streaks."""
        insights = []

        checkin_streak = self.streak_repo.get_streak(user_id, "checkin")
        current = checkin_streak["current_streak"]

        # Milestone streak achievements
        if current >= 30:
            insights.append(
                {
                    "type": "streak",
                    "title": "Consistency wins",
                    "message": f"You've checked in {current} days in a row. This is who you are now.",
                    "action": None,
                    "icon": "🔥",
                }
            )
        elif current >= 14:
            insights.append(
                {
                    "type": "streak",
                    "title": "Habit forming",
                    "message": f"{current}-day check-in streak. Two weeks of consistency builds champions.",
                    "action": None,
                    "icon": "🔥",
                }
            )
        elif current >= 7:
            insights.append(
                {
                    "type": "streak",
                    "title": "One week down",
                    "message": f"{current}-day streak. Keep the momentum going.",
                    "action": None,
                    "icon": "🔥",
                }
            )

        return insights

    def _get_milestone_insights(self, user_id: int) -> list[dict]:
        """Generate insights about upcoming milestones."""
        insights = []

        closest = self.milestone_service.get_closest_milestone(user_id)
        if closest and closest["percentage"] >= 80:
            insights.append(
                {
                    "type": "milestone",
                    "title": "Almost there",
                    "message": f"{closest['remaining']} more {closest['type']} to hit {closest['next_label']}.",
                    "action": "You're so close!",
                    "icon": "🎯",
                }
            )

        return insights

    def _get_recovery_insights(self, user_id: int) -> list[dict]:
        """Generate insights about rest and recovery."""
        insights = []

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check consecutive training days
            six_days_ago = date.today() - timedelta(days=6)
            cursor.execute(
                convert_query("""
                SELECT COUNT(*) as count FROM sessions
                WHERE session_date >= ? AND user_id = ?
            """),
                (six_days_ago.isoformat(), user_id),
            )
            result = cursor.fetchone()
            recent_days = result["count"] or 0

            if recent_days >= 6:
                insights.append(
                    {
                        "type": "recovery",
                        "title": "Rest is training",
                        "message": f"You've trained {recent_days} of the last 7 days. Consider a recovery day.",
                        "action": "Your body needs time to adapt",
                        "icon": "😴",
                    }
                )

        return insights

    def _get_trend_insights(self, user_id: int) -> list[dict]:
        """Generate insights about performance trends."""
        insights = []

        # Calculate date boundaries in Python for database compatibility
        today = date.today()
        thirty_days_ago = (today - timedelta(days=30)).isoformat()
        sixty_days_ago = (today - timedelta(days=60)).isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check submission rate trend
            cursor.execute(
                convert_query("""
                SELECT
                    SUM(submissions_for) as subs,
                    COUNT(*) as sessions
                FROM sessions
                WHERE session_date >= ? AND user_id = ?
            """),
                (thirty_days_ago, user_id),
            )
            recent = cursor.fetchone()
            if recent:
                recent_dict = dict(recent)
                recent_rate = (
                    (recent_dict["subs"] / recent_dict["sessions"])
                    if recent_dict["sessions"] and recent_dict["sessions"] > 0
                    else 0
                )
            else:
                recent_rate = 0

            cursor.execute(
                convert_query("""
                SELECT
                    SUM(submissions_for) as subs,
                    COUNT(*) as sessions
                FROM sessions
                WHERE session_date >= ?
                  AND session_date < ?
                  AND user_id = ?
            """),
                (sixty_days_ago, thirty_days_ago, user_id),
            )
            previous = cursor.fetchone()
            if previous:
                previous_dict = dict(previous)
                previous_rate = (
                    (previous_dict["subs"] / previous_dict["sessions"])
                    if previous_dict["sessions"] and previous_dict["sessions"] > 0
                    else 0
                )
            else:
                previous_rate = 0

            if previous_rate > 0 and recent_rate > previous_rate * 1.15:
                percent_up = round(
                    ((recent_rate - previous_rate) / previous_rate) * 100
                )
                insights.append(
                    {
                        "type": "trend",
                        "title": "Submissions trending up",
                        "message": f"Your submission rate is up {percent_up}% this month. The work is paying off.",
                        "action": None,
                        "icon": "📊",
                    }
                )

        return insights

    def _get_default_insight(self) -> dict:
        """Fallback insight when no data-driven insight available."""
        default_insights = [
            {
                "type": "encouragement",
                "title": "Keep showing up",
                "message": "Consistency beats intensity. You're building something.",
                "action": None,
                "icon": "💪",
            },
            {
                "type": "encouragement",
                "title": "Trust the process",
                "message": "Every session is an investment in your future self.",
                "action": None,
                "icon": "🥋",
            },
            {
                "type": "encouragement",
                "title": "Small wins compound",
                "message": "You don't need to be great today. Just better than yesterday.",
                "action": None,
                "icon": "📈",
            },
        ]

        return random.choice(default_insights)
