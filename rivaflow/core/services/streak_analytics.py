"""Training consistency and streak analytics service."""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict, Counter
import statistics

from rivaflow.db.repositories import (
    SessionRepository,
    GradingRepository,
)


class StreakAnalyticsService:
    """Business logic for training consistency, streaks, and milestones."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.grading_repo = GradingRepository()

    def get_consistency_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get training consistency analytics.

        Returns:
            - weekly_volume: Sessions/hours by week
            - class_type_distribution: Breakdown by class type
            - gym_breakdown: Training by location
            - streaks: Current and longest streaks
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        # Weekly volume
        weekly_stats = defaultdict(lambda: {"sessions": 0, "hours": 0, "rolls": 0})
        for session in sessions:
            week_key = session["session_date"].strftime("%Y-W%U")
            weekly_stats[week_key]["sessions"] += 1
            weekly_stats[week_key]["hours"] += session["duration_mins"] / 60
            weekly_stats[week_key]["rolls"] += session["rolls"]

        weekly_volume = [
            {"week": k, **v} for k, v in sorted(weekly_stats.items())
        ]

        # Class type distribution
        class_type_counts = Counter(s["class_type"] for s in sessions)
        class_type_distribution = [
            {"class_type": ct, "count": count}
            for ct, count in class_type_counts.items()
        ]

        # Gym breakdown
        gym_counts = Counter(s["gym_name"] for s in sessions)
        gym_breakdown = [
            {"gym": gym, "sessions": count}
            for gym, count in gym_counts.most_common()
        ]

        # Calculate streaks
        all_sessions = self.session_repo.get_recent(user_id, 1000)  # Get more for streak calc
        current_streak, longest_streak = self._calculate_streaks(all_sessions)

        return {
            "weekly_volume": weekly_volume,
            "class_type_distribution": class_type_distribution,
            "gym_breakdown": gym_breakdown,
            "streaks": {
                "current": current_streak,
                "longest": longest_streak,
            },
        }

    def _calculate_streaks(self, sessions: List[Dict]) -> tuple:
        """Calculate current and longest training streaks."""
        if not sessions:
            return 0, 0

        # Sort by date descending
        sorted_sessions = sorted(sessions, key=lambda s: s["session_date"], reverse=True)

        # Get unique dates
        session_dates = sorted(list(set(s["session_date"] for s in sorted_sessions)), reverse=True)

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        # Calculate current streak from today
        today = date.today()
        if session_dates and session_dates[0] >= today - timedelta(days=1):
            current_streak = 1
            for i in range(1, len(session_dates)):
                if session_dates[i] == session_dates[i-1] - timedelta(days=1):
                    current_streak += 1
                else:
                    break

        # Calculate longest streak
        for i in range(1, len(session_dates)):
            if session_dates[i] == session_dates[i-1] - timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)

        return current_streak, longest_streak

    def get_milestones(self, user_id: int) -> Dict[str, Any]:
        """
        Get progression and milestone data.

        Returns:
            - belt_progression: Timeline of belt promotions
            - personal_records: Best performances
            - rolling_totals: Lifetime and current belt stats
        """
        all_sessions = self.session_repo.get_recent(user_id, 10000)  # Get all
        gradings = self.grading_repo.list_all(user_id)

        # Belt progression timeline
        belt_progression = []
        sorted_gradings = sorted(gradings, key=lambda g: g["date_graded"])

        for i, grading in enumerate(sorted_gradings):
            start = grading["date_graded"]
            if isinstance(start, str):
                start = date.fromisoformat(start)

            if i + 1 < len(sorted_gradings):
                end = sorted_gradings[i + 1]["date_graded"]
                if isinstance(end, str):
                    end = date.fromisoformat(end)
            else:
                end = date.today()

            period_sessions = [
                s for s in all_sessions
                if start <= s["session_date"] < end
            ]

            belt_progression.append({
                "belt": grading["grade"],
                "date": start.isoformat(),
                "professor": grading.get("professor"),
                "sessions_at_belt": len(period_sessions),
                "hours_at_belt": sum(s["duration_mins"] for s in period_sessions) / 60,
            })

        # Personal records
        personal_records = {
            "most_rolls_session": max(all_sessions, key=lambda s: s["rolls"])["rolls"] if all_sessions else 0,
            "longest_session": max(all_sessions, key=lambda s: s["duration_mins"])["duration_mins"] if all_sessions else 0,
            "best_sub_ratio_day": 0,
            "most_partners_session": 0,
        }

        # Best submission ratio
        for session in all_sessions:
            if session["submissions_against"] > 0:
                ratio = session["submissions_for"] / session["submissions_against"]
                personal_records["best_sub_ratio_day"] = max(
                    personal_records["best_sub_ratio_day"], ratio
                )

        # Rolling totals
        total_sessions = len(all_sessions)
        total_hours = sum(s["duration_mins"] for s in all_sessions) / 60
        total_rolls = sum(s["rolls"] for s in all_sessions)
        total_subs = sum(s["submissions_for"] for s in all_sessions)

        # Current belt stats (if gradings exist)
        current_belt_sessions = 0
        current_belt_hours = 0
        if gradings:
            latest_grading = max(gradings, key=lambda g: g["date_graded"] if isinstance(g["date_graded"], date) else date.fromisoformat(g["date_graded"]))
            latest_date = latest_grading["date_graded"]
            if isinstance(latest_date, str):
                latest_date = date.fromisoformat(latest_date)

            current_belt_sessions_list = [
                s for s in all_sessions
                if s["session_date"] >= latest_date
            ]
            current_belt_sessions = len(current_belt_sessions_list)
            current_belt_hours = sum(s["duration_mins"] for s in current_belt_sessions_list) / 60

        # This year stats
        year_start = date(date.today().year, 1, 1)
        year_sessions = [s for s in all_sessions if s["session_date"] >= year_start]
        year_stats = {
            "sessions": len(year_sessions),
            "hours": sum(s["duration_mins"] for s in year_sessions) / 60,
            "rolls": sum(s["rolls"] for s in year_sessions),
        }

        return {
            "belt_progression": belt_progression,
            "personal_records": personal_records,
            "rolling_totals": {
                "lifetime": {
                    "sessions": total_sessions,
                    "hours": round(total_hours, 1),
                    "rolls": total_rolls,
                    "submissions": total_subs,
                },
                "current_belt": {
                    "sessions": current_belt_sessions,
                    "hours": round(current_belt_hours, 1),
                },
                "this_year": year_stats,
            },
        }
