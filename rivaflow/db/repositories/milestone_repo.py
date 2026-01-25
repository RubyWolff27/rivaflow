"""Repository for milestone tracking."""
import sqlite3
from typing import Optional

from rivaflow.db.database import get_connection
from rivaflow.config import MILESTONES, MILESTONE_LABELS


class MilestoneRepository:
    """Data access layer for milestone achievements."""

    @staticmethod
    def check_and_create_milestone(milestone_type: str, current_value: int) -> Optional[dict]:
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
                """
                SELECT id FROM milestones
                WHERE milestone_type = ? AND milestone_value = ?
                """,
                (milestone_type, crossed_threshold)
            )
            existing = cursor.fetchone()

            if existing:
                return None  # Already achieved

            # Create new milestone
            label = MILESTONE_LABELS.get(milestone_type, "{}").format(crossed_threshold)
            cursor.execute(
                """
                INSERT INTO milestones (milestone_type, milestone_value, milestone_label, celebrated)
                VALUES (?, ?, ?, 0)
                """,
                (milestone_type, crossed_threshold, label)
            )
            conn.commit()

            milestone_id = cursor.lastrowid

            # Fetch and return the created milestone
            cursor.execute(
                """
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                WHERE id = ?
                """,
                (milestone_id,)
            )
            row = cursor.fetchone()

            return {
                "id": row[0],
                "milestone_type": row[1],
                "milestone_value": row[2],
                "milestone_label": row[3],
                "achieved_at": row[4],
                "celebrated": row[5],
            }

    @staticmethod
    def get_uncelebrated_milestones() -> list[dict]:
        """Get milestones that haven't been shown to user yet."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                WHERE celebrated = 0
                ORDER BY achieved_at DESC
                """
            )
            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "milestone_type": row[1],
                    "milestone_value": row[2],
                    "milestone_label": row[3],
                    "achieved_at": row[4],
                    "celebrated": row[5],
                }
                for row in rows
            ]

    @staticmethod
    def mark_celebrated(milestone_id: int) -> None:
        """Mark milestone as celebrated."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE milestones
                SET celebrated = 1
                WHERE id = ?
                """,
                (milestone_id,)
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
    def get_all_achieved() -> list[dict]:
        """Get all achieved milestones."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, milestone_type, milestone_value, milestone_label, achieved_at, celebrated
                FROM milestones
                ORDER BY achieved_at DESC
                """
            )
            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "milestone_type": row[1],
                    "milestone_value": row[2],
                    "milestone_label": row[3],
                    "achieved_at": row[4],
                    "celebrated": row[5],
                }
                for row in rows
            ]

    @staticmethod
    def get_highest_achieved(milestone_type: str) -> Optional[int]:
        """Get the highest achieved value for a milestone type."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MAX(milestone_value)
                FROM milestones
                WHERE milestone_type = ?
                """,
                (milestone_type,)
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0
