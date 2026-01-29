"""Repository for session data access."""
import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from rivaflow.db.database import get_connection
from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository


class SessionRepository:
    """Data access layer for training sessions."""

    @staticmethod
    def create(
        user_id: int,
        session_date: date,
        class_type: str,
        gym_name: str,
        location: Optional[str] = None,
        class_time: Optional[str] = None,
        duration_mins: int = 60,
        intensity: int = 4,
        rolls: int = 0,
        submissions_for: int = 0,
        submissions_against: int = 0,
        partners: Optional[list[str]] = None,
        techniques: Optional[list[str]] = None,
        notes: Optional[str] = None,
        visibility_level: str = "private",
        instructor_id: Optional[int] = None,
        instructor_name: Optional[str] = None,
        whoop_strain: Optional[float] = None,
        whoop_calories: Optional[int] = None,
        whoop_avg_hr: Optional[int] = None,
        whoop_max_hr: Optional[int] = None,
    ) -> int:
        """Create a new session and return its ID."""
        with get_connection() as conn:
            from rivaflow.db.database import DB_TYPE
            cursor = conn.cursor()

            if DB_TYPE == "postgresql":
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        user_id, session_date, class_time, class_type, gym_name, location,
                        duration_mins, intensity, rolls,
                        submissions_for, submissions_against,
                        partners, techniques, notes, visibility_level,
                        instructor_id, instructor_name,
                        whoop_strain, whoop_calories, whoop_avg_hr, whoop_max_hr
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        session_date.isoformat(),
                        class_time,
                        class_type,
                        gym_name,
                        location,
                        duration_mins,
                        intensity,
                        rolls,
                        submissions_for,
                        submissions_against,
                        json.dumps(partners) if partners else None,
                        json.dumps(techniques) if techniques else None,
                        notes,
                        visibility_level,
                        instructor_id,
                        instructor_name,
                        whoop_strain,
                        whoop_calories,
                        whoop_avg_hr,
                        whoop_max_hr,
                    ),
                )
                result = cursor.fetchone()
                return result['id'] if hasattr(result, 'keys') else result[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO sessions (
                        user_id, session_date, class_time, class_type, gym_name, location,
                        duration_mins, intensity, rolls,
                        submissions_for, submissions_against,
                        partners, techniques, notes, visibility_level,
                        instructor_id, instructor_name,
                        whoop_strain, whoop_calories, whoop_avg_hr, whoop_max_hr
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        session_date.isoformat(),
                        class_time,
                        class_type,
                        gym_name,
                        location,
                        duration_mins,
                        intensity,
                        rolls,
                        submissions_for,
                        submissions_against,
                        json.dumps(partners) if partners else None,
                        json.dumps(techniques) if techniques else None,
                        notes,
                        visibility_level,
                        instructor_id,
                        instructor_name,
                        whoop_strain,
                        whoop_calories,
                        whoop_avg_hr,
                        whoop_max_hr,
                    ),
                )
                return cursor.lastrowid

    @staticmethod
    def get_by_id(user_id: int, session_id: int) -> Optional[dict]:
        """Get a session by ID with detailed techniques."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
            row = cursor.fetchone()
            if not row:
                return None

            session = SessionRepository._row_to_dict(row)

            # Fetch detailed technique records
            techniques = SessionTechniqueRepository.get_by_session_id(user_id, session_id)

            # Enrich with movement names from glossary
            for technique in techniques:
                cursor.execute(
                    "SELECT name FROM movements_glossary WHERE id = %s",
                    (technique["movement_id"],)
                )
                movement_row = cursor.fetchone()
                if movement_row:
                    technique["movement_name"] = movement_row["name"]

            session["session_techniques"] = techniques

            return session

    @staticmethod
    def get_by_id_any_user(session_id: int) -> Optional[dict]:
        """Get a session by ID without user scope (for validation/privacy checks)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return SessionRepository._row_to_dict(row)

    @staticmethod
    def update(
        user_id: int,
        session_id: int,
        session_date: Optional[date] = None,
        class_time: Optional[str] = None,
        class_type: Optional[str] = None,
        gym_name: Optional[str] = None,
        location: Optional[str] = None,
        duration_mins: Optional[int] = None,
        intensity: Optional[int] = None,
        rolls: Optional[int] = None,
        submissions_for: Optional[int] = None,
        submissions_against: Optional[int] = None,
        partners: Optional[list[str]] = None,
        techniques: Optional[list[str]] = None,
        notes: Optional[str] = None,
        visibility_level: Optional[str] = None,
        instructor_id: Optional[int] = None,
        instructor_name: Optional[str] = None,
        whoop_strain: Optional[float] = None,
        whoop_calories: Optional[int] = None,
        whoop_avg_hr: Optional[int] = None,
        whoop_max_hr: Optional[int] = None,
    ) -> Optional[dict]:
        """Update a session by ID. Returns updated session or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if session_date is not None:
                updates.append("session_date = %s")
                params.append(session_date.isoformat())
            if class_time is not None:
                updates.append("class_time = %s")
                params.append(class_time)
            if class_type is not None:
                updates.append("class_type = %s")
                params.append(class_type)
            if gym_name is not None:
                updates.append("gym_name = %s")
                params.append(gym_name)
            if location is not None:
                updates.append("location = %s")
                params.append(location)
            if duration_mins is not None:
                updates.append("duration_mins = %s")
                params.append(duration_mins)
            if intensity is not None:
                updates.append("intensity = %s")
                params.append(intensity)
            if rolls is not None:
                updates.append("rolls = %s")
                params.append(rolls)
            if submissions_for is not None:
                updates.append("submissions_for = %s")
                params.append(submissions_for)
            if submissions_against is not None:
                updates.append("submissions_against = %s")
                params.append(submissions_against)
            if partners is not None:
                updates.append("partners = %s")
                params.append(json.dumps(partners) if partners else None)
            if techniques is not None:
                updates.append("techniques = %s")
                params.append(json.dumps(techniques) if techniques else None)
            if notes is not None:
                updates.append("notes = %s")
                params.append(notes)
            if visibility_level is not None:
                updates.append("visibility_level = %s")
                params.append(visibility_level)
            if instructor_id is not None:
                updates.append("instructor_id = %s")
                params.append(instructor_id)
            if instructor_name is not None:
                updates.append("instructor_name = %s")
                params.append(instructor_name)
            if whoop_strain is not None:
                updates.append("whoop_strain = %s")
                params.append(whoop_strain)
            if whoop_calories is not None:
                updates.append("whoop_calories = %s")
                params.append(whoop_calories)
            if whoop_avg_hr is not None:
                updates.append("whoop_avg_hr = %s")
                params.append(whoop_avg_hr)
            if whoop_max_hr is not None:
                updates.append("whoop_max_hr = %s")
                params.append(whoop_max_hr)

            if not updates:
                # Nothing to update, return current session
                return SessionRepository.get_by_id(user_id, session_id)

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([session_id, user_id])
            query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = %s AND user_id = %s"
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return None

            # Return updated session
            return SessionRepository.get_by_id(user_id, session_id)

    @staticmethod
    def get_by_date_range(user_id: int, start_date: date, end_date: date) -> list[dict]:
        """Get all sessions within a date range (inclusive)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM sessions
                WHERE user_id = %s AND session_date BETWEEN %s AND %s
                ORDER BY session_date DESC
                """,
                (user_id, start_date.isoformat(), end_date.isoformat()),
            )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_recent(user_id: int, limit: int = 10) -> list[dict]:
        """Get most recent sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE user_id = %s ORDER BY session_date DESC LIMIT %s", (user_id, limit)
            )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_unique_gyms(user_id: int) -> list[str]:
        """Get list of unique gym names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT gym_name FROM sessions WHERE user_id = %s ORDER BY gym_name",
                (user_id,)
            )
            return [row["gym_name"] for row in cursor.fetchall()]

    @staticmethod
    def get_unique_locations(user_id: int) -> list[str]:
        """Get list of unique locations from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT location FROM sessions
                WHERE user_id = %s AND location IS NOT NULL
                ORDER BY location
                """,
                (user_id,)
            )
            return [row["location"] for row in cursor.fetchall()]

    @staticmethod
    def get_unique_partners(user_id: int) -> list[str]:
        """Get list of unique partner names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT partners FROM sessions WHERE user_id = %s AND partners IS NOT NULL",
                (user_id,)
            )
            partners_set = set()
            for row in cursor.fetchall():
                partners_list = json.loads(row["partners"])
                partners_set.update(partners_list)
            return sorted(partners_set)

    @staticmethod
    def get_last_n_sessions_by_type(user_id: int, n: int = 5) -> dict[str, list[str]]:
        """Get the class types of the last N sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT class_type FROM sessions
                WHERE user_id = %s
                ORDER BY session_date DESC, created_at DESC
                LIMIT %s
                """,
                (user_id, n),
            )
            return [row["class_type"] for row in cursor.fetchall()]

    @staticmethod
    def delete(user_id: int, session_id: int) -> bool:
        """Delete a session by ID. Returns True if deleted, False if not found."""
        from rivaflow.db.repositories.session_roll_repo import SessionRollRepository
        from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository

        with get_connection() as conn:
            cursor = conn.cursor()

            # Delete related session rolls
            SessionRollRepository.delete_by_session(session_id)

            # Delete related session techniques
            SessionTechniqueRepository.delete_by_session(session_id)

            # Delete the session itself
            cursor.execute(
                "DELETE FROM sessions WHERE id = %s AND user_id = %s",
                (session_id, user_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse JSON fields
        if data.get("partners"):
            data["partners"] = json.loads(data["partners"])
        if data.get("techniques"):
            data["techniques"] = json.loads(data["techniques"])
        # Parse dates
        if data.get("session_date"):
            data["session_date"] = date.fromisoformat(data["session_date"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return data
