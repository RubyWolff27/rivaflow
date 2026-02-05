"""Repository for streak tracking."""

from datetime import date

from rivaflow.config import STREAK_GRACE_DAYS
from rivaflow.db.database import convert_query, execute_insert, get_connection


class StreakRepository:
    """Data access layer for streak tracking."""

    @staticmethod
    def get_streak(user_id: int, streak_type: str) -> dict:
        """Get current streak info for type."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    """
                SELECT id, streak_type, current_streak, longest_streak,
                       last_checkin_date, streak_started_date, grace_days_used, updated_at
                FROM streaks
                WHERE user_id = ? AND streak_type = ?
                """
                ),
                (user_id, streak_type),
            )
            row = cursor.fetchone()
            if row is None:
                # Initialize if not exists
                streak_id = execute_insert(
                    cursor,
                    """
                    INSERT INTO streaks (user_id, streak_type, current_streak, longest_streak)
                    VALUES (?, ?, 0, 0)
                    """,
                    (user_id, streak_type),
                )
                conn.commit()
                return {
                    "id": streak_id,
                    "streak_type": streak_type,
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_checkin_date": None,
                    "streak_started_date": None,
                    "grace_days_used": 0,
                    "updated_at": None,
                }

            # Convert row to dict (works for both SQLite Row and PostgreSQL RealDictRow)
            row_dict = dict(row)
            return {
                "id": row_dict["id"],
                "streak_type": row_dict["streak_type"],
                "current_streak": row_dict["current_streak"],
                "longest_streak": row_dict["longest_streak"],
                "last_checkin_date": row_dict.get("last_checkin_date"),
                "streak_started_date": row_dict.get("streak_started_date"),
                "grace_days_used": row_dict["grace_days_used"],
                "updated_at": row_dict.get("updated_at"),
            }

    @staticmethod
    def update_streak(user_id: int, streak_type: str, checkin_date: date) -> dict:
        """
        Update streak after check-in. Returns updated streak info.

        Logic:
        - If checkin_date == last_checkin_date: no change (duplicate)
        - If checkin_date == last_checkin_date + 1 day: increment streak
        - If checkin_date == last_checkin_date + 2 days AND grace_days_used < GRACE_DAYS: use grace day
        - Otherwise: reset streak to 1
        """
        streak = StreakRepository.get_streak(user_id, streak_type)

        last_checkin = streak["last_checkin_date"]

        # First ever check-in
        if last_checkin is None:
            new_streak = 1
            new_longest = max(1, streak["longest_streak"])
            grace_days_used = 0
            streak_started = checkin_date
        else:
            last_date = date.fromisoformat(last_checkin)
            days_since_last = (checkin_date - last_date).days

            # Same day - no change
            if days_since_last == 0:
                return streak

            # Consecutive day - extend streak
            elif days_since_last == 1:
                new_streak = streak["current_streak"] + 1
                new_longest = max(new_streak, streak["longest_streak"])
                grace_days_used = 0  # Reset grace days on consecutive check-in
                streak_started = streak["streak_started_date"] or checkin_date.isoformat()

            # Missed 1 day - use grace day if available
            elif days_since_last == 2 and streak["grace_days_used"] < STREAK_GRACE_DAYS:
                new_streak = streak["current_streak"] + 1
                new_longest = max(new_streak, streak["longest_streak"])
                grace_days_used = streak["grace_days_used"] + 1
                streak_started = streak["streak_started_date"] or checkin_date.isoformat()

            # Streak broken - reset
            else:
                new_streak = 1
                new_longest = streak["longest_streak"]  # Keep previous best
                grace_days_used = 0
                streak_started = checkin_date

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    """
                UPDATE streaks
                SET current_streak = ?,
                    longest_streak = ?,
                    last_checkin_date = ?,
                    streak_started_date = ?,
                    grace_days_used = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND streak_type = ?
                """
                ),
                (
                    new_streak,
                    new_longest,
                    checkin_date.isoformat(),
                    (
                        streak_started.isoformat()
                        if isinstance(streak_started, date)
                        else streak_started
                    ),
                    grace_days_used,
                    user_id,
                    streak_type,
                ),
            )
            conn.commit()

        return StreakRepository.get_streak(user_id, streak_type)

    @staticmethod
    def get_all_streaks(user_id: int) -> list[dict]:
        """Get all streak types with current values."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    """
                SELECT id, streak_type, current_streak, longest_streak,
                       last_checkin_date, streak_started_date, grace_days_used, updated_at
                FROM streaks
                WHERE user_id = ?
                ORDER BY streak_type
                """
                ),
                (user_id,),
            )
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def is_streak_at_risk(user_id: int, streak_type: str) -> bool:
        """Check if user will lose streak if they don't check in today."""
        streak = StreakRepository.get_streak(user_id, streak_type)

        if streak["last_checkin_date"] is None or streak["current_streak"] == 0:
            return False

        last_date = date.fromisoformat(streak["last_checkin_date"])
        today = date.today()
        days_since_last = (today - last_date).days

        # At risk if:
        # - Last check-in was yesterday and today is ending (would be 2 days tomorrow)
        # - Last check-in was 2 days ago and no grace days left
        if days_since_last == 1:
            return True  # Must check in today to keep streak
        elif days_since_last == 2 and streak["grace_days_used"] >= STREAK_GRACE_DAYS:
            return True  # Already used grace day, streak breaks tomorrow

        return False
