"""Daily insight generation."""

import random
from datetime import date, timedelta

from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.settings import settings
from rivaflow.db.repositories.session_repo import SessionRepository
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

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Get this week's hours
        week_mins = SessionRepository.get_week_duration_sum(
            user_id, week_start.isoformat()
        )
        week_hours = round(week_mins / 60, 1)

        # Get 4-week average
        four_weeks_ago = today - timedelta(days=28)

        # Database-specific week formatting
        if settings.DB_TYPE == "postgresql":
            week_format = "to_char(session_date::date, 'IYYY-IW')"
        else:
            week_format = "strftime('%Y-%W', session_date)"

        avg_mins = SessionRepository.get_avg_weekly_duration(
            user_id,
            four_weeks_ago.isoformat(),
            week_start.isoformat(),
            week_format,
        )
        avg_hours = round(avg_mins / 60, 1)

        if avg_hours > 0 and week_hours > 0:
            percent_diff = round(((week_hours - avg_hours) / avg_hours) * 100)

            if percent_diff > 15:
                insights.append(
                    {
                        "type": "stat",
                        "title": "Training volume up",
                        "message": f"You've trained {week_hours} hours this week \u2014 {percent_diff}% more than your 4-week average.",
                        "action": None,
                        "icon": "\U0001f4c8",
                    }
                )
            elif percent_diff < -15:
                insights.append(
                    {
                        "type": "stat",
                        "title": "Recovery week",
                        "message": f"You've trained {week_hours} hours this week \u2014 {abs(percent_diff)}% less than average. Recovery matters.",
                        "action": None,
                        "icon": "\U0001f4c9",
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
                    "icon": "\U0001f525",
                }
            )
        elif current >= 14:
            insights.append(
                {
                    "type": "streak",
                    "title": "Habit forming",
                    "message": f"{current}-day check-in streak. Two weeks of consistency builds champions.",
                    "action": None,
                    "icon": "\U0001f525",
                }
            )
        elif current >= 7:
            insights.append(
                {
                    "type": "streak",
                    "title": "One week down",
                    "message": f"{current}-day streak. Keep the momentum going.",
                    "action": None,
                    "icon": "\U0001f525",
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
                    "icon": "\U0001f3af",
                }
            )

        return insights

    def _get_recovery_insights(self, user_id: int) -> list[dict]:
        """Generate insights about rest and recovery."""
        insights = []

        # Check consecutive training days
        six_days_ago = date.today() - timedelta(days=6)
        recent_days = SessionRepository.count_sessions_since(
            user_id, six_days_ago.isoformat()
        )

        if recent_days >= 6:
            insights.append(
                {
                    "type": "recovery",
                    "title": "Rest is training",
                    "message": f"You've trained {recent_days} of the last 7 days. Consider a recovery day.",
                    "action": "Your body needs time to adapt",
                    "icon": "\U0001f634",
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

        # Check submission rate trend
        recent = SessionRepository.get_submission_stats(user_id, thirty_days_ago)
        if recent and recent["sessions"] and recent["sessions"] > 0:
            recent_rate = (recent["subs"] or 0) / recent["sessions"]
        else:
            recent_rate = 0

        previous = SessionRepository.get_submission_stats(
            user_id, sixty_days_ago, thirty_days_ago
        )
        if previous and previous["sessions"] and previous["sessions"] > 0:
            previous_rate = (previous["subs"] or 0) / previous["sessions"]
        else:
            previous_rate = 0

        if previous_rate > 0 and recent_rate > previous_rate * 1.15:
            percent_up = round(((recent_rate - previous_rate) / previous_rate) * 100)
            insights.append(
                {
                    "type": "trend",
                    "title": "Submissions trending up",
                    "message": f"Your submission rate is up {percent_up}% this month. The work is paying off.",
                    "action": None,
                    "icon": "\U0001f4ca",
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
                "icon": "\U0001f4aa",
            },
            {
                "type": "encouragement",
                "title": "Trust the process",
                "message": "Every session is an investment in your future self.",
                "action": None,
                "icon": "\U0001f94b",
            },
            {
                "type": "encouragement",
                "title": "Small wins compound",
                "message": "You don't need to be great today. Just better than yesterday.",
                "action": None,
                "icon": "\U0001f4c8",
            },
        ]

        return random.choice(default_insights)
