"""Repository for goal progress tracking."""
from typing import Optional
from datetime import date, datetime

from rivaflow.db.database import get_connection


class GoalProgressRepository:
    """Data access layer for weekly goal progress."""

    def _row_to_dict(self, row) -> dict:
        """Convert database row to dictionary."""
        return {
            "id": row[0],
            "week_start_date": row[1],
            "week_end_date": row[2],
            "target_sessions": row[3],
            "actual_sessions": row[4],
            "target_hours": row[5],
            "actual_hours": row[6],
            "target_rolls": row[7],
            "actual_rolls": row[8],
            "completed_at": row[9],
            "created_at": row[10],
            "updated_at": row[11],
        }

    def get_by_week(self, user_id: int, week_start_date: date) -> Optional[dict]:
        """Get goal progress for a specific week."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, week_start_date, week_end_date, target_sessions, actual_sessions,
                       target_hours, actual_hours, target_rolls, actual_rolls,
                       completed_at, created_at, updated_at
                FROM goal_progress
                WHERE user_id = %s AND week_start_date = %s
                """,
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
                """
                SELECT id, week_start_date, week_end_date, target_sessions, actual_sessions,
                       target_hours, actual_hours, target_rolls, actual_rolls,
                       completed_at, created_at, updated_at
                FROM goal_progress
                WHERE user_id = %s
                ORDER BY week_start_date DESC
                LIMIT %s
                """,
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
            from rivaflow.db.database import DB_TYPE
            cursor = conn.cursor()

            if DB_TYPE == "postgresql":
                cursor.execute(
                    """
                    INSERT INTO goal_progress
                    (user_id, week_start_date, week_end_date, target_sessions, actual_sessions,
                     target_hours, actual_hours, target_rolls, actual_rolls)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
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
                result = cursor.fetchone()
                return result['id'] if hasattr(result, 'keys') else result[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO goal_progress
                    (user_id, week_start_date, week_end_date, target_sessions, actual_sessions,
                     target_hours, actual_hours, target_rolls, actual_rolls)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                return cursor.lastrowid

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
                """
                SELECT target_sessions, target_hours, target_rolls
                FROM goal_progress
                WHERE user_id = %s AND week_start_date = %s
                """,
                (user_id, week_start_date.isoformat()),
            )
            row = cursor.fetchone()

            if not row:
                return False

            target_sessions, target_hours, target_rolls = row
            all_complete = (
                actual_sessions >= target_sessions
                and actual_hours >= target_hours
                and actual_rolls >= target_rolls
            )

            # Update with completion timestamp if newly completed
            cursor.execute(
                """
                UPDATE goal_progress
                SET actual_sessions = %s,
                    actual_hours = %s,
                    actual_rolls = %s,
                    completed_at = CASE
                        WHEN %s AND completed_at IS NULL THEN CURRENT_TIMESTAMP
                        WHEN NOT %s THEN NULL
                        ELSE completed_at
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND week_start_date = %s
                """,
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
                """
                SELECT week_start_date, completed_at
                FROM goal_progress
                WHERE user_id = %s
                ORDER BY week_start_date DESC
                """,
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
