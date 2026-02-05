"""Service layer for weekly goals and streak tracking."""

from datetime import date

from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.report_service import ReportService
from rivaflow.db.repositories import ProfileRepository, SessionRepository
from rivaflow.db.repositories.goal_progress_repo import GoalProgressRepository


class GoalsService:
    """Business logic for goal setting and progress tracking."""

    def __init__(self):
        self.profile_repo = ProfileRepository()
        self.session_repo = SessionRepository()
        self.goal_progress_repo = GoalProgressRepository()
        self.report_service = ReportService()
        self.analytics_service = AnalyticsService()

    def get_current_week_progress(self, user_id: int) -> dict:
        """Get current week's goal progress vs targets.

        Returns:
            {
                "week_start": "2025-01-20",
                "week_end": "2025-01-26",
                "targets": {
                    "sessions": 3,
                    "hours": 4.5,
                    "rolls": 15
                },
                "actual": {
                    "sessions": 2,
                    "hours": 3.0,
                    "rolls": 10
                },
                "progress": {
                    "sessions_pct": 66.7,
                    "hours_pct": 66.7,
                    "rolls_pct": 66.7,
                    "overall_pct": 66.7
                },
                "completed": False,
                "days_remaining": 3
            }
        """
        import logging

        logger = logging.getLogger(__name__)

        # Get current week date range (Monday-Sunday)
        week_start, week_end = self.report_service.get_week_dates()
        logger.info(f"[DEBUG] Week range: {week_start} to {week_end}")

        # Get profile targets
        profile = self.profile_repo.get(user_id)
        targets = {
            "sessions": profile.get("weekly_sessions_target", 3),
            "hours": profile.get("weekly_hours_target", 4.5),
            "rolls": profile.get("weekly_rolls_target", 15),
            "bjj_sessions": profile.get("weekly_bjj_sessions_target", 3),
            "sc_sessions": profile.get("weekly_sc_sessions_target", 1),
            "mobility_sessions": profile.get("weekly_mobility_sessions_target", 0),
        }

        # Get actual progress from sessions this week
        sessions = self.session_repo.get_by_date_range(user_id, week_start, week_end)
        logger.info(f"[DEBUG] Retrieved {len(sessions)} sessions for week")
        for s in sessions:
            logger.info(
                f"[DEBUG] Session: date={s.get('session_date')}, type={s.get('class_type')}, duration={s.get('duration_mins')}"
            )

        actual_sessions = len(sessions)
        actual_hours = round(sum(s["duration_mins"] for s in sessions) / 60, 1)
        actual_rolls = sum(s["rolls"] for s in sessions)

        # Calculate activity type breakdown
        bjj_sessions = sum(
            1 for s in sessions if s.get("class_type") in ["gi", "no-gi", "open-mat", "competition"]
        )
        sc_sessions = sum(
            1 for s in sessions if s.get("class_type") in ["s&c", "cardio"]
        )  # Include cardio as S&C
        mobility_sessions = sum(
            1 for s in sessions if s.get("class_type") in ["mobility", "recovery", "physio"]
        )  # Include physio

        logger.info(
            f"[DEBUG] Activity breakdown: BJJ={bjj_sessions}, S&C={sc_sessions}, Mobility={mobility_sessions}"
        )

        actual = {
            "sessions": actual_sessions,
            "hours": actual_hours,
            "rolls": actual_rolls,
            "bjj_sessions": bjj_sessions,
            "sc_sessions": sc_sessions,
            "mobility_sessions": mobility_sessions,
        }

        # Calculate progress percentages
        progress = {
            "sessions_pct": (
                round((actual_sessions / targets["sessions"] * 100), 1)
                if targets["sessions"] > 0
                else 0
            ),
            "hours_pct": (
                round((actual_hours / targets["hours"] * 100), 1) if targets["hours"] > 0 else 0
            ),
            "rolls_pct": (
                round((actual_rolls / targets["rolls"] * 100), 1) if targets["rolls"] > 0 else 0
            ),
            "bjj_sessions_pct": (
                round((bjj_sessions / targets["bjj_sessions"] * 100), 1)
                if targets["bjj_sessions"] > 0
                else 0
            ),
            "sc_sessions_pct": (
                round((sc_sessions / targets["sc_sessions"] * 100), 1)
                if targets["sc_sessions"] > 0
                else 0
            ),
            "mobility_sessions_pct": (
                round((mobility_sessions / targets["mobility_sessions"] * 100), 1)
                if targets["mobility_sessions"] > 0
                else 0
            ),
        }
        progress["overall_pct"] = round(
            (progress["sessions_pct"] + progress["hours_pct"] + progress["rolls_pct"]) / 3,
            1,
        )

        # Calculate days remaining in week
        today = date.today()
        days_remaining = (week_end - today).days
        if days_remaining < 0:
            days_remaining = 0

        # Check if all goals met
        completed = (
            actual_sessions >= targets["sessions"]
            and actual_hours >= targets["hours"]
            and actual_rolls >= targets["rolls"]
        )

        # Update goal_progress table
        self._update_or_create_progress(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            targets=targets,
            actual=actual,
        )

        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "targets": targets,
            "actual": actual,
            "progress": progress,
            "completed": completed,
            "days_remaining": days_remaining,
        }

    def _update_or_create_progress(
        self,
        user_id: int,
        week_start: date,
        week_end: date,
        targets: dict,
        actual: dict,
    ):
        """Update or create goal_progress record for the week."""
        existing = self.goal_progress_repo.get_by_week(user_id, week_start)

        if existing:
            # Update existing record
            self.goal_progress_repo.update_progress(
                user_id=user_id,
                week_start_date=week_start,
                actual_sessions=actual["sessions"],
                actual_hours=actual["hours"],
                actual_rolls=actual["rolls"],
            )
        else:
            # Create new record
            self.goal_progress_repo.create(
                user_id=user_id,
                week_start_date=week_start,
                week_end_date=week_end,
                target_sessions=targets["sessions"],
                target_hours=targets["hours"],
                target_rolls=targets["rolls"],
                actual_sessions=actual["sessions"],
                actual_hours=actual["hours"],
                actual_rolls=actual["rolls"],
            )

    def get_recent_weeks_trend(self, user_id: int, weeks: int = 12) -> list[dict]:
        """Get goal completion trend for recent weeks."""
        progress_records = self.goal_progress_repo.get_recent_weeks(user_id, limit=weeks)

        trend = []
        for record in progress_records:
            completion_pct = self._calculate_completion_pct(record)
            trend.append(
                {
                    "week_start": record["week_start_date"],
                    "week_end": record["week_end_date"],
                    "completion_pct": completion_pct,
                    "completed": record["completed_at"] is not None,
                    "targets": {
                        "sessions": record["target_sessions"],
                        "hours": record["target_hours"],
                        "rolls": record["target_rolls"],
                    },
                    "actual": {
                        "sessions": record["actual_sessions"],
                        "hours": record["actual_hours"],
                        "rolls": record["actual_rolls"],
                    },
                }
            )

        return trend

    def _calculate_completion_pct(self, record: dict) -> float:
        """Calculate overall completion percentage for a goal record."""
        sessions_pct = (
            (record["actual_sessions"] / record["target_sessions"] * 100)
            if record["target_sessions"] > 0
            else 0
        )
        hours_pct = (
            (record["actual_hours"] / record["target_hours"] * 100)
            if record["target_hours"] > 0
            else 0
        )
        rolls_pct = (
            (record["actual_rolls"] / record["target_rolls"] * 100)
            if record["target_rolls"] > 0
            else 0
        )

        return round((sessions_pct + hours_pct + rolls_pct) / 3, 1)

    def get_goal_completion_streak(self, user_id: int) -> dict:
        """Get current and longest weekly goal completion streaks."""
        return self.goal_progress_repo.get_completion_streak(user_id)

    def get_training_streaks(self, user_id: int) -> dict:
        """Get training session streaks (consecutive days trained).

        Uses existing AnalyticsService streak calculation.
        """
        # Get consistency analytics which includes streak data
        consistency = self.analytics_service.get_consistency_analytics(user_id)

        return {
            "current_streak": consistency["streaks"]["current"],
            "longest_streak": consistency["streaks"]["longest"],
            "last_updated": date.today().isoformat(),
        }

    def update_profile_goals(
        self,
        user_id: int,
        weekly_sessions_target: int | None = None,
        weekly_hours_target: float | None = None,
        weekly_rolls_target: int | None = None,
        weekly_bjj_sessions_target: int | None = None,
        weekly_sc_sessions_target: int | None = None,
        weekly_mobility_sessions_target: int | None = None,
    ) -> dict:
        """Update weekly goal targets in profile.

        Returns updated profile.
        """
        profile = self.profile_repo.get(user_id)

        # Build update dict
        updates = {}
        if weekly_sessions_target is not None:
            updates["weekly_sessions_target"] = weekly_sessions_target
        if weekly_hours_target is not None:
            updates["weekly_hours_target"] = weekly_hours_target
        if weekly_rolls_target is not None:
            updates["weekly_rolls_target"] = weekly_rolls_target
        if weekly_bjj_sessions_target is not None:
            updates["weekly_bjj_sessions_target"] = weekly_bjj_sessions_target
        if weekly_sc_sessions_target is not None:
            updates["weekly_sc_sessions_target"] = weekly_sc_sessions_target
        if weekly_mobility_sessions_target is not None:
            updates["weekly_mobility_sessions_target"] = weekly_mobility_sessions_target

        if not updates:
            return profile

        # Update profile
        from rivaflow.db.database import convert_query, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [user_id]

            cursor.execute(
                convert_query(
                    f"UPDATE profile SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
                ),
                values,
            )

        return self.profile_repo.get(user_id)

    def get_goals_summary(self, user_id: int) -> dict:
        """Get comprehensive goals and streaks overview.

        Returns:
            {
                "current_week": {...},  # Current week progress
                "training_streaks": {...},  # Consecutive training days
                "goal_streaks": {...},  # Consecutive weeks hitting all goals
                "recent_trend": [...],  # Last 12 weeks goal completion
            }
        """
        return {
            "current_week": self.get_current_week_progress(user_id),
            "training_streaks": self.get_training_streaks(user_id),
            "goal_streaks": self.get_goal_completion_streak(user_id),
            "recent_trend": self.get_recent_weeks_trend(user_id, weeks=12),
        }
