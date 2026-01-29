"""Repository for user profile data access."""
import sqlite3
from datetime import datetime, date
from typing import Optional

from rivaflow.db.database import get_connection, convert_query


class ProfileRepository:
    """Data access layer for user profile (single row table)."""

    @staticmethod
    def get(user_id: int) -> Optional[dict]:
        """Get the user profile."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM profile WHERE user_id = ?"), (user_id,))
            row = cursor.fetchone()
            if row:
                return ProfileRepository._row_to_dict(row)
            return None

    @staticmethod
    def update(
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        sex: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        default_gym: Optional[str] = None,
        current_grade: Optional[str] = None,
        current_professor: Optional[str] = None,
        current_instructor_id: Optional[int] = None,
        height_cm: Optional[int] = None,
        target_weight_kg: Optional[float] = None,
        weekly_sessions_target: Optional[int] = None,
        weekly_hours_target: Optional[float] = None,
        weekly_rolls_target: Optional[int] = None,
        show_streak_on_dashboard: Optional[bool] = None,
        show_weekly_goals: Optional[bool] = None,
    ) -> dict:
        """Update the user profile. Creates profile if it doesn't exist. Returns updated profile."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if profile exists
            cursor.execute(convert_query("SELECT id FROM profile WHERE user_id = ?"), (user_id,))
            exists = cursor.fetchone() is not None

            if not exists:
                # Create new profile
                cursor.execute(
                convert_query("""
                    INSERT INTO profile (
                        user_id, first_name, last_name, date_of_birth, sex, location, state,
                        default_gym, current_grade, current_professor, current_instructor_id,
                        height_cm, target_weight_kg,
                        weekly_sessions_target, weekly_hours_target, weekly_rolls_target,
                        show_streak_on_dashboard, show_weekly_goals
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """),
                    (
                        user_id,
                        first_name,
                        last_name,
                        date_of_birth,
                        sex,
                        city,  # Maps to 'location' column in database
                        state,
                        default_gym,
                        current_grade,
                        current_professor,
                        current_instructor_id,
                        height_cm,
                        target_weight_kg,
                        weekly_sessions_target if weekly_sessions_target is not None else 3,
                        weekly_hours_target if weekly_hours_target is not None else 4.5,
                        weekly_rolls_target if weekly_rolls_target is not None else 15,
                        show_streak_on_dashboard if show_streak_on_dashboard is not None else 1,
                        show_weekly_goals if show_weekly_goals is not None else 1,
                    )
                )
            else:
                # Build dynamic update query
                updates = []
                params = []

                if first_name is not None:
                    updates.append("first_name = ?")
                    params.append(first_name)
                if last_name is not None:
                    updates.append("last_name = ?")
                    params.append(last_name)
                if date_of_birth is not None:
                    updates.append("date_of_birth = ?")
                    params.append(date_of_birth)
                if sex is not None:
                    updates.append("sex = ?")
                    params.append(sex)
                if city is not None:
                    updates.append("location = ?")  # Column is named 'location' not 'city'
                    params.append(city)
                if state is not None:
                    updates.append("state = ?")
                    params.append(state)
                if default_gym is not None:
                    updates.append("default_gym = ?")
                    params.append(default_gym)
                if current_grade is not None:
                    updates.append("current_grade = ?")
                    params.append(current_grade)
                if current_professor is not None:
                    updates.append("current_professor = ?")
                    params.append(current_professor)
                if current_instructor_id is not None:
                    updates.append("current_instructor_id = ?")
                    params.append(current_instructor_id)
                if height_cm is not None:
                    updates.append("height_cm = ?")
                    params.append(height_cm)
                if target_weight_kg is not None:
                    updates.append("target_weight_kg = ?")
                    params.append(target_weight_kg)
                if weekly_sessions_target is not None:
                    updates.append("weekly_sessions_target = ?")
                    params.append(weekly_sessions_target)
                if weekly_hours_target is not None:
                    updates.append("weekly_hours_target = ?")
                    params.append(weekly_hours_target)
                if weekly_rolls_target is not None:
                    updates.append("weekly_rolls_target = ?")
                    params.append(weekly_rolls_target)
                if show_streak_on_dashboard is not None:
                    updates.append("show_streak_on_dashboard = ?")
                    params.append(show_streak_on_dashboard)
                if show_weekly_goals is not None:
                    updates.append("show_weekly_goals = ?")
                    params.append(show_weekly_goals)

                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(user_id)
                    query = f"UPDATE profile SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(query, params)

            # Return updated profile
            cursor.execute(convert_query("SELECT * FROM profile WHERE user_id = ?"), (user_id,))
            row = cursor.fetchone()
            if row:
                return ProfileRepository._row_to_dict(row)
            else:
                raise Exception("Failed to create or update profile")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)

        # Map 'location' column to 'city' for API compatibility
        if "location" in data:
            data["city"] = data.pop("location")

        # Parse dates
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Calculate age from date_of_birth
        if data.get("date_of_birth"):
            try:
                dob = datetime.fromisoformat(data["date_of_birth"]).date()
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                data["age"] = age
            except (ValueError, AttributeError):
                data["age"] = None
        else:
            data["age"] = None

        return data
