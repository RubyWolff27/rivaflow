"""Repository for milestone tracking."""
import sqlite3
from typing import Optional

from rivaflow.db.database import get_connection, convert_query
from rivaflow.config import MILESTONES, MILESTONE_LABELS


class MilestoneRepository:
    """Data access layer for milestone achievements."""

    @staticmethod
    def check_and_create_milestone(user_id: int, milestone_type: str, current_value: int) -> Optional[dict]:
        """
        Check if current value crosses a milestone threshold. Create if new.
        Returns the newly created milestone dict, or None if no new milestone.
        """
        # Get thresholds for this milestone type
        thresholds = MILESTONES.get(milestone_type, [])

        # Find the highest threshold that's been crossed
        crossed_threshold = None
        for threshold in sorted(thresholds, reverse=True):
            if current_value >= threshold:
                crossed_threshold = threshold
                break

        if crossed_threshold is None:
            return None

        # Check if this milestone already exists
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id FROM milestones
                WHERE user_id = ? AND milestone_type = ? AND milestone_value = ?
                """),
                (user_id, milestone_type, crossed_threshold)
            )
            existing = cursor.fetchone()

            if existing:
                return None  # Already achieved

            # Create new milestone
            label = MILESTONE_LABELS.get(milestone_type, "{}").format(crossed_threshold)
            cursor.execute(
                convert_query("""
                INSERT INTO milestones (user_id, milestone_type, milestone_value, milestone_label, celebrated)
                VALUES (?, ?, ?, ?, 0)
                """),
                (user_id, milestone_type, crossed_threshold, label)
            )
            conn.commit()

            milestone_id = cursor.lastrowid

            # Fetch and return the created milestone
            cursor.execute(
                convert_query("""
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                WHERE id = ? AND user_id = ?
                """),
                (milestone_id, user_id)
            )
            row = cursor.fetchone()

            return dict(row)

    @staticmethod
    def get_uncelebrated_milestones(user_id: int) -> list[dict]:
        """Get milestones that haven't been shown to user yet."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                WHERE user_id = ? AND celebrated = FALSE
                ORDER BY achieved_at DESC
                """),
                (user_id,)
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def mark_celebrated(user_id: int, milestone_id: int) -> None:
        """Mark milestone as celebrated."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                UPDATE milestones
                SET celebrated = TRUE
                WHERE id = ? AND user_id = ?
                """),
                (milestone_id, user_id)
            )
            conn.commit()

    @staticmethod
    def get_next_milestone(milestone_type: str, current_value: int) -> Optional[dict]:
        """Get the next milestone target for a type."""
        thresholds = MILESTONES.get(milestone_type, [])

        # Find the next threshold above current value
        for threshold in sorted(thresholds):
            if threshold > current_value:
                label = MILESTONE_LABELS.get(milestone_type, "{}").format(threshold)
                return {
                    "milestone_type": milestone_type,
                    "milestone_value": threshold,
                    "milestone_label": label,
                    "remaining": threshold - current_value,
                    "percentage": round((current_value / threshold) * 100, 1),
                }

        return None  # No more milestones

    @staticmethod
    def get_all_achieved(user_id: int) -> list[dict]:
        """Get all achieved milestones."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                WHERE user_id = ?
                ORDER BY achieved_at DESC
                """),
                (user_id,)
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def get_highest_achieved(user_id: int, milestone_type: str) -> Optional[int]:
        """Get the highest achieved value for a milestone type."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT MAX(milestone_value) as max_value
                FROM milestones
                WHERE user_id = ? AND milestone_type = ?
                """),
                (user_id, milestone_type)
            )
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                max_value = row_dict.get('max_value')
                return max_value if max_value is not None else 0
            return 0
