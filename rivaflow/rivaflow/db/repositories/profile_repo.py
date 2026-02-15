"""Repository for user profile data access."""

import logging
from datetime import date, datetime

from rivaflow.db.database import convert_query, get_connection

logger = logging.getLogger(__name__)

# Explicit column list for profile table (avoids SELECT p.*)
_PROFILE_COLS = (
    "p.id, p.user_id, p.first_name, p.last_name, "
    "p.date_of_birth, p.sex, p.default_gym, p.default_location, "
    "p.current_grade, p.current_professor, p.current_instructor_id, "
    "p.primary_training_type, "
    "p.location, p.state, "
    "p.height_cm, p.target_weight_kg, p.target_weight_date, "
    "p.weekly_sessions_target, p.weekly_hours_target, p.weekly_rolls_target, "
    "p.weekly_bjj_sessions_target, p.weekly_sc_sessions_target, "
    "p.weekly_mobility_sessions_target, "
    "p.show_streak_on_dashboard, p.show_weekly_goals, "
    "p.timezone, "
    "p.created_at, p.updated_at"
)

# Profile columns joined with user table fields
_PROFILE_JOIN_COLS = (
    _PROFILE_COLS + ", u.avatar_url, u.email, u.primary_gym_id, u.activity_visibility"
)


class ProfileRepository:
    """Data access layer for user profile (single row table)."""

    @staticmethod
    def get(user_id: int) -> dict | None:
        """Get the user profile."""
        ProfileRepository._ensure_timezone_column()
        with get_connection() as conn:
            cursor = conn.cursor()
            # Join with users table to get avatar_url
            cursor.execute(
                convert_query(
                    f"SELECT {_PROFILE_JOIN_COLS}"
                    " FROM profile p"
                    " LEFT JOIN users u ON p.user_id = u.id"
                    " WHERE p.user_id = ?"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return ProfileRepository._row_to_dict(row)
            return None

    _tz_col_checked = False

    @classmethod
    def _ensure_timezone_column(cls):
        """Add timezone column to profile table if missing (PG only). Once-per-process."""
        if cls._tz_col_checked:
            return
        from rivaflow.core.settings import settings

        if settings.DB_TYPE != "postgresql":
            cls._tz_col_checked = True
            return
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='profile' "
                    "AND column_name='timezone'"
                )
                if cur.fetchone() is None:
                    logger.warning("profile.timezone missing — adding inline")
                    cur.execute(
                        "ALTER TABLE profile " "ADD COLUMN timezone TEXT DEFAULT 'UTC'"
                    )
                    logger.info("Added profile.timezone column inline")
                cur.close()
            cls._tz_col_checked = True
        except Exception as exc:
            logger.error(f"_ensure_timezone_column failed: {exc}")

    @staticmethod
    def update(
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: str | None = None,
        sex: str | None = None,
        city: str | None = None,
        state: str | None = None,
        default_gym: str | None = None,
        default_location: str | None = None,
        current_grade: str | None = None,
        current_professor: str | None = None,
        current_instructor_id: int | None = None,
        primary_training_type: str | None = None,
        height_cm: int | None = None,
        target_weight_kg: float | None = None,
        weekly_sessions_target: int | None = None,
        weekly_hours_target: float | None = None,
        weekly_rolls_target: int | None = None,
        weekly_bjj_sessions_target: int | None = None,
        weekly_sc_sessions_target: int | None = None,
        weekly_mobility_sessions_target: int | None = None,
        target_weight_date: str | None = None,
        show_streak_on_dashboard: bool | None = None,
        show_weekly_goals: bool | None = None,
        timezone: str | None = None,
    ) -> dict:
        """Update the user profile. Creates profile if it doesn't exist. Returns updated profile."""
        ProfileRepository._ensure_timezone_column()
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if profile exists
            cursor.execute(
                convert_query("SELECT id FROM profile WHERE user_id = ?"), (user_id,)
            )
            exists = cursor.fetchone() is not None

            if not exists:
                # Create new profile
                cursor.execute(
                    convert_query("""
                    INSERT INTO profile (
                        user_id, first_name, last_name, date_of_birth, sex, location, state,
                        default_gym, default_location, current_grade, current_professor, current_instructor_id,
                        primary_training_type, height_cm, target_weight_kg,
                        weekly_sessions_target, weekly_hours_target, weekly_rolls_target,
                        weekly_bjj_sessions_target, weekly_sc_sessions_target, weekly_mobility_sessions_target,
                        show_streak_on_dashboard, show_weekly_goals, timezone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        default_location,
                        current_grade,
                        current_professor,
                        current_instructor_id,
                        primary_training_type,
                        height_cm,
                        target_weight_kg,
                        (
                            weekly_sessions_target
                            if weekly_sessions_target is not None
                            else 3
                        ),
                        weekly_hours_target if weekly_hours_target is not None else 4.5,
                        weekly_rolls_target if weekly_rolls_target is not None else 15,
                        (
                            weekly_bjj_sessions_target
                            if weekly_bjj_sessions_target is not None
                            else 3
                        ),
                        (
                            weekly_sc_sessions_target
                            if weekly_sc_sessions_target is not None
                            else 1
                        ),
                        (
                            weekly_mobility_sessions_target
                            if weekly_mobility_sessions_target is not None
                            else 0
                        ),
                        (
                            show_streak_on_dashboard
                            if show_streak_on_dashboard is not None
                            else True
                        ),
                        show_weekly_goals if show_weekly_goals is not None else True,
                        timezone if timezone is not None else "UTC",
                    ),
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
                    updates.append(
                        "location = ?"
                    )  # Column is named 'location' not 'city'
                    params.append(city)
                if state is not None:
                    updates.append("state = ?")
                    params.append(state)
                if default_gym is not None:
                    updates.append("default_gym = ?")
                    params.append(default_gym)
                if default_location is not None:
                    updates.append("default_location = ?")
                    params.append(default_location)
                if current_grade is not None:
                    updates.append("current_grade = ?")
                    params.append(current_grade)
                if current_professor is not None:
                    updates.append("current_professor = ?")
                    params.append(current_professor)
                if current_instructor_id is not None:
                    updates.append("current_instructor_id = ?")
                    params.append(current_instructor_id)
                if primary_training_type is not None:
                    updates.append("primary_training_type = ?")
                    params.append(primary_training_type)
                if height_cm is not None:
                    updates.append("height_cm = ?")
                    params.append(height_cm)
                if target_weight_kg is not None:
                    updates.append("target_weight_kg = ?")
                    params.append(target_weight_kg)
                if target_weight_date is not None:
                    updates.append("target_weight_date = ?")
                    params.append(target_weight_date)
                if weekly_sessions_target is not None:
                    updates.append("weekly_sessions_target = ?")
                    params.append(weekly_sessions_target)
                if weekly_hours_target is not None:
                    updates.append("weekly_hours_target = ?")
                    params.append(weekly_hours_target)
                if weekly_rolls_target is not None:
                    updates.append("weekly_rolls_target = ?")
                    params.append(weekly_rolls_target)
                if weekly_bjj_sessions_target is not None:
                    updates.append("weekly_bjj_sessions_target = ?")
                    params.append(weekly_bjj_sessions_target)
                if weekly_sc_sessions_target is not None:
                    updates.append("weekly_sc_sessions_target = ?")
                    params.append(weekly_sc_sessions_target)
                if weekly_mobility_sessions_target is not None:
                    updates.append("weekly_mobility_sessions_target = ?")
                    params.append(weekly_mobility_sessions_target)
                if show_streak_on_dashboard is not None:
                    updates.append("show_streak_on_dashboard = ?")
                    params.append(show_streak_on_dashboard)
                if show_weekly_goals is not None:
                    updates.append("show_weekly_goals = ?")
                    params.append(show_weekly_goals)
                if timezone is not None:
                    updates.append("timezone = ?")
                    params.append(timezone)

                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(user_id)
                    query = f"UPDATE profile SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(convert_query(query), params)

            # Return updated profile (join with users table to get avatar_url)
            cursor.execute(
                convert_query(
                    f"SELECT {_PROFILE_JOIN_COLS}"
                    " FROM profile p"
                    " LEFT JOIN users u ON p.user_id = u.id"
                    " WHERE p.user_id = ?"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return ProfileRepository._row_to_dict(row)
            else:
                raise Exception("Failed to create or update profile")

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)

        # Map 'location' column to 'city' for API compatibility
        if "location" in data:
            data["city"] = data.pop("location")

        # Parse dates (handle both string and datetime types)
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # Calculate age from date_of_birth
        if data.get("date_of_birth"):
            try:
                dob = datetime.fromisoformat(data["date_of_birth"]).date()
                today = date.today()
                age = (
                    today.year
                    - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
                data["age"] = age
            except (ValueError, AttributeError):
                data["age"] = None
        else:
            data["age"] = None

        return data
