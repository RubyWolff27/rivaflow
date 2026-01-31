"""Milestone detection and celebration."""
import random
from typing import Optional

from rivaflow.db.database import get_connection
from rivaflow.db.repositories.milestone_repo import MilestoneRepository
from rivaflow.db.repositories.streak_repo import StreakRepository
from rivaflow.config import MILESTONE_QUOTES


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
            milestone = self.milestone_repo.check_and_create_milestone(user_id, milestone_type, current_value)
            if milestone:
                new_milestones.append(milestone)

        return new_milestones

    def _get_current_totals(self, user_id: int) -> dict:
        """Calculate current totals for all milestone types."""
        from rivaflow.db.database import convert_query

        with get_connection() as conn:
            cursor = conn.cursor()

            # Hours: sum of duration_mins / 60 from sessions
            cursor.execute(convert_query("SELECT SUM(duration_mins) as total FROM sessions WHERE user_id = ?"), (user_id,))
            result = cursor.fetchone()
            total_mins = result['total'] or 0
            hours = int(total_mins / 60)

            # Sessions: count of sessions
            cursor.execute(convert_query("SELECT COUNT(*) as count FROM sessions WHERE user_id = ?"), (user_id,))
            result = cursor.fetchone()
            sessions = result['count'] or 0

            # Rolls: sum of rolls from sessions
            cursor.execute(convert_query("SELECT SUM(rolls) as total FROM sessions WHERE user_id = ?"), (user_id,))
            result = cursor.fetchone()
            rolls = result['total'] or 0

            # Partners: count of unique partners from sessions (JSON partners field)
            # Note: This is simplified - in reality we'd need to parse JSON
            # session_rolls doesn't have user_id, need to JOIN with sessions
            cursor.execute(convert_query("""
                SELECT COUNT(DISTINCT sr.partner_id) as count
                FROM session_rolls sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE sr.partner_id IS NOT NULL AND s.user_id = ?
            """), (user_id,))
            result = cursor.fetchone()
            partners = result['count'] or 0

            # Techniques: count from techniques table with times_trained > 0
            # Note: This assumes a techniques table - adjust based on actual schema
            # For now, use count of unique technique names from session_techniques
            # session_techniques doesn't have user_id, need to JOIN with sessions
            cursor.execute(convert_query("""
                SELECT COUNT(DISTINCT st.movement_id) as count
                FROM session_techniques st
                JOIN sessions s ON st.session_id = s.id
                WHERE s.user_id = ?
            """), (user_id,))
            result = cursor.fetchone()
            techniques = result['count'] or 0

            # Streak: current checkin streak
            checkin_streak = self.streak_repo.get_streak(user_id, "checkin")
            streak = checkin_streak["current_streak"]

        return {
            "hours": hours,
            "sessions": sessions,
            "rolls": rolls,
            "partners": partners,
            "techniques": techniques,
            "streak": streak,
        }

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
            next_milestone = self.milestone_repo.get_next_milestone(milestone_type, current_value)

            if next_milestone:
                progress_list.append({
                    "type": milestone_type,
                    "current": current_value,
                    "next_target": next_milestone["milestone_value"],
                    "next_label": next_milestone["milestone_label"],
                    "remaining": next_milestone["remaining"],
                    "percentage": next_milestone["percentage"],
                })

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

    def get_closest_milestone(self, user_id: int) -> Optional[dict]:
        """Get the closest upcoming milestone across all types."""
        progress_list = self.get_progress_to_next(user_id)

        if not progress_list:
            return None

        # Find the milestone with highest percentage completion
        closest = max(progress_list, key=lambda x: x["percentage"])
        return closest
