"""Milestone detection and celebration."""

import random
from typing import Any

from rivaflow.core.constants import MILESTONE_QUOTES
from rivaflow.db.repositories.milestone_repo import MilestoneRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.streak_repo import StreakRepository

SESSION_MILESTONES = [50, 100, 250, 500, 1000, 2500, 5000]
ROLL_MILESTONES = [100, 500, 1000, 5000, 10000]


class MilestoneService:
    """Business logic for milestone detection and celebration."""

    def __init__(self):
        self.milestone_repo = MilestoneRepository()
        self.streak_repo = StreakRepository()

    def check_all_milestones(self, user_id: int) -> list[dict]:
        """
        Check all milestone types against current totals.
        Returns list of newly achieved milestones.
        """
        new_milestones = []

        # Calculate current totals
        totals = self._get_current_totals(user_id)

        # Check each milestone type
        for milestone_type, current_value in totals.items():
            milestone = self.milestone_repo.check_and_create_milestone(
                user_id, milestone_type, current_value
            )
            if milestone:
                new_milestones.append(milestone)

        return new_milestones

    def _get_current_totals(self, user_id: int) -> dict:
        """Calculate current totals for all milestone types."""
        totals = SessionRepository.get_milestone_totals(user_id)

        # Streak: current checkin streak
        checkin_streak = self.streak_repo.get_streak(user_id, "checkin")
        totals["streak"] = checkin_streak["current_streak"]

        return totals

    def get_celebration_display(self, milestone: dict) -> dict:
        """
        Get celebration display data for a milestone.

        Returns dict with:
        - label: formatted label
        - value: milestone value
        - quote: random motivational quote
        - author: quote author
        - achieved_at: timestamp
        """
        quote, author = random.choice(MILESTONE_QUOTES)

        return {
            "label": milestone["milestone_label"],
            "value": milestone["milestone_value"],
            "type": milestone["milestone_type"],
            "quote": quote,
            "author": author,
            "achieved_at": milestone["achieved_at"],
        }

    def get_progress_to_next(self, user_id: int) -> list[dict]:
        """
        Get progress toward next milestone for each type.

        Returns list of dicts with:
        - type: milestone type
        - current: current value
        - next_target: next milestone value
        - next_label: formatted label
        - remaining: how many until milestone
        - percentage: progress percentage
        """
        totals = self._get_current_totals(user_id)
        progress_list = []

        for milestone_type, current_value in totals.items():
            next_milestone = self.milestone_repo.get_next_milestone(
                milestone_type, current_value
            )

            if next_milestone:
                progress_list.append(
                    {
                        "type": milestone_type,
                        "current": current_value,
                        "next_target": next_milestone["milestone_value"],
                        "next_label": next_milestone["milestone_label"],
                        "remaining": next_milestone["remaining"],
                        "percentage": next_milestone["percentage"],
                    }
                )

        return progress_list

    def get_uncelebrated_milestones(self, user_id: int) -> list[dict]:
        """Get all milestones that haven't been celebrated yet."""
        return self.milestone_repo.get_uncelebrated_milestones(user_id)

    def mark_celebrated(self, user_id: int, milestone_id: int) -> None:
        """Mark a milestone as celebrated."""
        self.milestone_repo.mark_celebrated(user_id, milestone_id)

    def get_all_achieved(self, user_id: int) -> list[dict]:
        """Get all achieved milestones."""
        return self.milestone_repo.get_all_achieved(user_id)

    def get_current_totals(self, user_id: int) -> dict:
        """Public method to get current totals."""
        return self._get_current_totals(user_id)

    def get_closest_milestone(self, user_id: int) -> dict | None:
        """Get the closest upcoming milestone across all types."""
        progress_list = self.get_progress_to_next(user_id)

        if not progress_list:
            return None

        # Find the milestone with highest percentage completion
        closest = max(progress_list, key=lambda x: x["percentage"])
        return closest

    @staticmethod
    def check_session_milestones(user_id: int) -> list[dict[str, Any]]:
        """Check if user just hit a session count milestone."""
        from rivaflow.core.services.notification_service import NotificationService

        total = SessionRepository.get_total_count_for_user(user_id)
        achieved: list[dict[str, Any]] = []
        for milestone in SESSION_MILESTONES:
            if total == milestone:
                label = f"{milestone} sessions logged!"
                try:
                    NotificationService.create_milestone_notification(user_id, label)
                except Exception:
                    pass
                achieved.append(
                    {"type": "session_count", "value": milestone, "label": label}
                )
        return achieved

    @staticmethod
    def check_roll_milestones(user_id: int) -> list[dict[str, Any]]:
        """Check if user just hit a total rolls milestone."""
        from rivaflow.core.services.notification_service import NotificationService

        total = SessionRepository.get_total_rolls_for_user(user_id)
        achieved: list[dict[str, Any]] = []
        for milestone in ROLL_MILESTONES:
            if total == milestone:
                label = f"{milestone} total rolls!"
                try:
                    NotificationService.create_milestone_notification(user_id, label)
                except Exception:
                    pass
                achieved.append(
                    {"type": "roll_count", "value": milestone, "label": label}
                )
        return achieved
