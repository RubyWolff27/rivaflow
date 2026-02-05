"""Rest day logging."""

import json
from datetime import date, timedelta

from rivaflow.core.services.insight_service import InsightService
from rivaflow.core.services.milestone_service import MilestoneService
from rivaflow.core.services.streak_service import StreakService
from rivaflow.db.repositories.checkin_repo import CheckinRepository


class RestService:
    """Business logic for rest day logging."""

    def __init__(self):
        self.checkin_repo = CheckinRepository()
        self.streak_service = StreakService()
        self.milestone_service = MilestoneService()
        self.insight_service = InsightService()

    def log_rest_day(
        self,
        user_id: int,
        rest_type: str = "recovery",
        note: str | None = None,
        tomorrow_intention: str | None = None,
        rest_date: date | None = None,
    ) -> dict:
        """
        Log a rest day.

        Args:
            user_id: User ID
            rest_type: Type of rest ('recovery', 'life', 'injury', 'travel')
            note: Optional note about the rest day
            tomorrow_intention: Optional intention for tomorrow
            rest_date: Date of rest day (defaults to today)

        Returns dict with:
        - checkin_id: the daily checkin record ID
        - check_date: date of check-in
        - rest_type: type of rest
        - streak_info: updated streak information
        - insight: generated insight
        - milestones: any new milestones achieved
        - tomorrow_intention: tomorrow's intention (if set)
        """
        if rest_date is None:
            rest_date = date.today()

        # Generate insight first
        insight = self.insight_service.generate_insight(user_id)
        insight_json = json.dumps(insight)

        # Create/update check-in record
        checkin_id = self.checkin_repo.upsert_checkin(
            user_id=user_id,
            check_date=rest_date,
            checkin_type="rest",
            rest_type=rest_type,
            rest_note=note,
            tomorrow_intention=tomorrow_intention,
            insight_shown=insight_json,
        )

        # Update streaks (check-in only, not training)
        streak_info = self.streak_service.record_checkin(user_id, "rest", rest_date)

        # Check for new milestones
        new_milestones = self.milestone_service.check_all_milestones(user_id)

        return {
            "checkin_id": checkin_id,
            "check_date": rest_date.isoformat(),
            "rest_type": rest_type,
            "rest_note": note,
            "streak_info": streak_info,
            "insight": insight,
            "milestones": new_milestones,
            "tomorrow_intention": tomorrow_intention,
        }

    def get_recent_rest_days(self, user_id: int, days: int = 30) -> list[dict]:
        """Get rest days from the last N days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        checkins = self.checkin_repo.get_checkins_range(user_id, start_date, end_date)

        return [c for c in checkins if c["checkin_type"] == "rest"]

    def get_rest_day_count(self, user_id: int, days: int = 7) -> int:
        """Count rest days in the last N days."""
        rest_days = self.get_recent_rest_days(user_id, days)
        return len(rest_days)
