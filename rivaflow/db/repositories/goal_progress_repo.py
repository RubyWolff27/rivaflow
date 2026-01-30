"""Repository for goal progress tracking."""
from typing import Optional
from datetime import date, datetime

from rivaflow.db.database import get_connection, convert_query, execute_insert


class GoalProgressRepository:
    """Data access layer for weekly goal progress."""

    def _row_to_dict(self, row) -> dict:
        """Convert database row to dictionary."""
        return dict(row)

    def get_by_week(self, user_id: int, week_start_date: date) -> Optional[dict]:
        """Get goal progress for a specific week."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, week_start_date, week_end_date, target_sessions, actual_sessions,
                       target_hours, actual_hours, target_rolls, actual_rolls,
                       completed_at, created_at, updated_at
                FROM goal_progress
                WHERE user_id = ? AND week_start_date = ?
                """),
                (user_id, week_start_date.isoformat()),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def get_current_week(self, user_id: int, week_start: date) -> Optional[dict]:
        """Get current week's goal progress."""
        return self.get_by_week(user_id, week_start)

    def get_recent_weeks(self, user_id: int, limit: int = 12) -> list[dict]:
        """Get recent weeks' goal progress (for trend display)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT id, week_start_date, week_end_date, target_sessions, actual_sessions,
                       target_hours, actual_hours, target_rolls, actual_rolls,
                       completed_at, created_at, updated_at
                FROM goal_progress
                WHERE user_id = ?
                ORDER BY week_start_date DESC
                LIMIT ?
                """),
                (user_id, limit),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def create(
        self,
        user_id: int,
        week_start_date: date,
        week_end_date: date,
        target_sessions: int,
        actual_sessions: int,
        target_hours: float,
        actual_hours: float,
        target_rolls: int,
        actual_rolls: int,
    ) -> int:
        """Create a new goal progress record."""
        with get_connection() as conn:
            cursor = conn.cursor()

            return execute_insert(
                cursor,
                """
                INSERT INTO goal_progress
                (user_id, week_start_date, week_end_date, target_sessions, actual_sessions,
                 target_hours, actual_hours, target_rolls, actual_rolls)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    week_start_date.isoformat(),
                    week_end_date.isoformat(),
                    target_sessions,
                    actual_sessions,
                    target_hours,
                    actual_hours,
                    target_rolls,
                    actual_rolls,
                ),
            )

    def update_progress(
        self,
        user_id: int,
        week_start_date: date,
        actual_sessions: int,
        actual_hours: float,
        actual_rolls: int,
    ) -> bool:
        """Update actual progress for a week."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if all goals are met
            cursor.execute(
                convert_query("""
                SELECT target_sessions, target_hours, target_rolls
                FROM goal_progress
                WHERE user_id = ? AND week_start_date = ?
                """),
                (user_id, week_start_date.isoformat()),
            )
            row = cursor.fetchone()

            if not row:
                return False

            row_dict = dict(row)
            target_sessions = row_dict['target_sessions']
            target_hours = row_dict['target_hours']
            target_rolls = row_dict['target_rolls']
            all_complete = (
                actual_sessions >= target_sessions
                and actual_hours >= target_hours
                and actual_rolls >= target_rolls
            )

            # Update with completion timestamp if newly completed
            # PostgreSQL requires explicit NULL::timestamp casting for type matching in CASE
            cursor.execute(
                convert_query("""
                UPDATE goal_progress
                SET actual_sessions = ?,
                    actual_hours = ?,
                    actual_rolls = ?,
                    completed_at = CASE
                        WHEN ? AND completed_at IS NULL THEN CURRENT_TIMESTAMP
                        WHEN NOT ? THEN NULL::timestamp
                        ELSE completed_at
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND week_start_date = ?
                """),
                (
                    actual_sessions,
                    actual_hours,
                    actual_rolls,
                    all_complete,
                    all_complete,
                    user_id,
                    week_start_date.isoformat(),
                ),
            )
            return True

    def get_completion_streak(self, user_id: int) -> dict:
        """Calculate current and longest weekly goal completion streaks."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT week_start_date, completed_at
                FROM goal_progress
                WHERE user_id = ?
                ORDER BY week_start_date DESC
                """),
                (user_id,)
            )
            rows = cursor.fetchall()

            if not rows:
                return {"current_streak": 0, "longest_streak": 0}

            # Calculate current streak (from most recent week backwards)
            current_streak = 0
            for week_start, completed_at in rows:
                if completed_at:
                    current_streak += 1
                else:
                    break

            # Calculate longest streak
            longest_streak = 0
            temp_streak = 0
            for week_start, completed_at in reversed(rows):
                if completed_at:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 0

            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
            }
