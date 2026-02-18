"""Milestone detection and celebration."""

import random

from rivaflow.core.constants import MILESTONE_QUOTES
from rivaflow.db.repositories.milestone_repo import MilestoneRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.streak_repo import StreakRepository


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
