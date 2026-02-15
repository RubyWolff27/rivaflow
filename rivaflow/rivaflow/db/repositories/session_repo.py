"""Repository for session data access."""

import json
from datetime import date, datetime
from typing import Any

from rivaflow.core.settings import settings
from rivaflow.db.database import convert_query, execute_insert, get_connection


def _pg_bool(value: bool) -> Any:
    """Adapt a Python bool for PostgreSQL BOOLEAN or SQLite INTEGER columns.

    For PostgreSQL: returns Python bool → psycopg2 sends TRUE/FALSE.
    For SQLite: returns int (1/0) since SQLite has no boolean type.

    Note: production's needs_review column is converted from INTEGER to
    BOOLEAN at startup by migrate.py _ensure_critical_columns().
    """
    if settings.DB_TYPE == "postgresql":
        return bool(value)
    return int(value)


# Explicit column list for sessions table (avoids SELECT *)
_SESSION_COLS = (
    "id, user_id, session_date, class_time, class_type, gym_name, location, "
    "duration_mins, intensity, rolls, "
    "submissions_for, submissions_against, "
    "partners, techniques, notes, "
    "visibility_level, audience_scope, share_fields, published_at, "
    "instructor_id, instructor_name, "
    "whoop_strain, whoop_calories, whoop_avg_hr, whoop_max_hr, "
    "attacks_attempted, attacks_successful, "
    "defenses_attempted, defenses_successful, "
    "source, needs_review, "
    "session_score, score_breakdown, score_version, "
    "created_at, updated_at"
)


class SessionRepository:
    """Data access layer for training sessions."""

    @staticmethod
    def create(
        user_id: int,
        session_date: date,
        class_type: str,
        gym_name: str,
        location: str | None = None,
        class_time: str | None = None,
        duration_mins: int = 60,
        intensity: int = 4,
        rolls: int = 0,
        submissions_for: int = 0,
        submissions_against: int = 0,
        partners: list[str] | None = None,
        techniques: list[str] | None = None,
        notes: str | None = None,
        visibility_level: str = "private",
        instructor_id: int | None = None,
        instructor_name: str | None = None,
        whoop_strain: float | None = None,
        whoop_calories: int | None = None,
        whoop_avg_hr: int | None = None,
        whoop_max_hr: int | None = None,
        attacks_attempted: int = 0,
        attacks_successful: int = 0,
        defenses_attempted: int = 0,
        defenses_successful: int = 0,
        source: str = "manual",
        needs_review: bool = False,
    ) -> int:
        """Create a new session and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO sessions (
                    user_id, session_date, class_time, class_type, gym_name, location,
                    duration_mins, intensity, rolls,
                    submissions_for, submissions_against,
                    partners, techniques, notes, visibility_level,
                    instructor_id, instructor_name,
                    whoop_strain, whoop_calories, whoop_avg_hr, whoop_max_hr,
                    attacks_attempted, attacks_successful,
                    defenses_attempted, defenses_successful,
                    source, needs_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    attacks_attempted,
                    attacks_successful,
                    defenses_attempted,
                    defenses_successful,
                    source,
                    _pg_bool(needs_review),
                ),
            )

    @staticmethod
    def get_by_id(user_id: int, session_id: int) -> dict | None:
        """Get a session by ID with detailed techniques."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT {_SESSION_COLS} FROM sessions"
                    " WHERE id = ? AND user_id = ?"
                ),
                (session_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None

            session = SessionRepository._row_to_dict(row)

            # Fetch detailed technique records with movement names in a single JOIN query
            cursor.execute(
                convert_query("""
                    SELECT
                        st.id,
                        st.session_id,
                        st.movement_id,
                        st.technique_number,
                        st.notes,
                        st.media_urls,
                        st.created_at,
                        mg.name as movement_name
                    FROM session_techniques st
                    LEFT JOIN movements_glossary mg ON st.movement_id = mg.id
                    WHERE st.session_id = ?
                    ORDER BY st.technique_number
                """),
                (session_id,),
            )
            techniques = [dict(row) for row in cursor.fetchall()]

            session["session_techniques"] = techniques

            return session

    @staticmethod
    def get_owned_ids(user_id: int, session_ids: list[int]) -> set[int]:
        """Return the subset of *session_ids* that belong to *user_id*."""
        if not session_ids:
            return set()
        placeholders = ",".join("?" for _ in session_ids)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT id FROM sessions WHERE user_id = ? AND id IN ({placeholders})"
                ),
                (user_id, *session_ids),
            )
            rows = cursor.fetchall()
        return {(r["id"] if hasattr(r, "keys") else r[0]) for r in rows}

    @staticmethod
    def get_by_id_any_user(session_id: int) -> dict | None:
        """Get a session by ID without user scope (for validation/privacy checks)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(f"SELECT {_SESSION_COLS} FROM sessions WHERE id = ?"),
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return SessionRepository._row_to_dict(row)

    @staticmethod
    def update(user_id: int, session_id: int, **kwargs) -> dict | None:
        """
        Update a session by ID with flexible field updates.

        Args:
            user_id: User ID (for authorization)
            session_id: Session ID to update
            **kwargs: Fields to update (session_date, class_type, gym_name, etc.)

        Returns:
            Updated session dict or None if not found

        Example:
            update(user_id=1, session_id=123, intensity=5, notes="Great session!")
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Define field handlers for special processing
            # Most fields pass through directly, but some need transformation
            field_processors = {
                "session_date": lambda v: v.isoformat() if v else None,
                "partners": lambda v: (
                    json.dumps(v) if v is not None else json.dumps([])
                ),
                "techniques": lambda v: (
                    json.dumps(v) if v is not None else json.dumps([])
                ),
                "needs_review": lambda v: _pg_bool(bool(v)),
                "score_breakdown": lambda v: (
                    json.dumps(v) if isinstance(v, dict) else v
                ),
            }

            # List fields that can be explicitly cleared with []
            clearable_list_fields = {"partners", "techniques"}

            # Build update query dynamically from provided kwargs
            updates = []
            params = []

            # Valid fields that can be updated
            valid_fields = {
                "session_date",
                "class_time",
                "class_type",
                "gym_name",
                "location",
                "duration_mins",
                "intensity",
                "rolls",
                "submissions_for",
                "submissions_against",
                "partners",
                "techniques",
                "notes",
                "visibility_level",
                "instructor_id",
                "instructor_name",
                "whoop_strain",
                "whoop_calories",
                "whoop_avg_hr",
                "whoop_max_hr",
                "attacks_attempted",
                "attacks_successful",
                "defenses_attempted",
                "defenses_successful",
                "source",
                "needs_review",
                "session_score",
                "score_breakdown",
                "score_version",
            }

            # Process each provided field — validate BEFORE building query
            for field, value in kwargs.items():
                if field not in valid_fields:
                    raise ValueError(f"Invalid field: {field}")

                # For list fields, allow empty list as explicit "clear"
                if field in clearable_list_fields:
                    if value is not None:
                        updates.append(f"{field} = ?")
                        params.append(field_processors[field](value))
                elif value is not None:
                    updates.append(f"{field} = ?")

                    # Apply processor if field has special handling
                    if field in field_processors:
                        params.append(field_processors[field](value))
                    else:
                        params.append(value)

            if not updates:
                # Nothing to update, return current session
                return SessionRepository.get_by_id(user_id, session_id)

            # Always update timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")

            # Build and execute query
            params.extend([session_id, user_id])
            query = (
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            )
            cursor.execute(convert_query(query), params)

            if cursor.rowcount == 0:
                return None

            # Return updated session
            return SessionRepository.get_by_id(user_id, session_id)

    @staticmethod
    def get_by_date_range(
        user_id: int, start_date: date, end_date: date, types: list[str] | None = None
    ) -> list[dict]:
        """Get all sessions within a date range (inclusive), optionally filtered by class types."""
        with get_connection() as conn:
            cursor = conn.cursor()

            if types:
                # Build parameterized query with IN clause
                placeholders = ", ".join("?" * len(types))
                query = f"""
                SELECT {_SESSION_COLS} FROM sessions
                WHERE user_id = ? AND session_date BETWEEN ? AND ?
                AND class_type IN ({placeholders})
                ORDER BY session_date DESC
                """
                params = (user_id, start_date.isoformat(), end_date.isoformat(), *types)
            else:
                query = f"""
                SELECT {_SESSION_COLS} FROM sessions
                WHERE user_id = ? AND session_date BETWEEN ? AND ?
                ORDER BY session_date DESC
                """
                params = (user_id, start_date.isoformat(), end_date.isoformat())

            cursor.execute(convert_query(query), params)
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_recent(user_id: int, limit: int = 10) -> list[dict]:
        """Get most recent sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT {_SESSION_COLS} FROM sessions"
                    " WHERE user_id = ? ORDER BY session_date DESC LIMIT ?"
                ),
                (user_id, limit),
            )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def list_by_user(user_id: int, limit: int = None) -> list[dict]:
        """Get all sessions for a user.

        Args:
            user_id: User ID
            limit: Optional limit on number of sessions to return
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute(
                    convert_query(
                        f"SELECT {_SESSION_COLS} FROM sessions"
                        " WHERE user_id = ? ORDER BY session_date DESC"
                        " LIMIT ?"
                    ),
                    (user_id, limit),
                )
            else:
                cursor.execute(
                    convert_query(
                        f"SELECT {_SESSION_COLS} FROM sessions"
                        " WHERE user_id = ? ORDER BY session_date DESC"
                    ),
                    (user_id,),
                )
            return [SessionRepository._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """Get aggregate stats for a user's sessions efficiently.

        Returns:
            Dict with total_sessions and total_hours
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        COUNT(*) as total_sessions,
                        COALESCE(SUM(duration_mins), 0) as total_minutes
                    FROM sessions
                    WHERE user_id = ?
                """),
                (user_id,),
            )
            row = cursor.fetchone()
            if hasattr(row, "keys"):  # PostgreSQL dict result
                return {
                    "total_sessions": row["total_sessions"],
                    "total_hours": round(row["total_minutes"] / 60, 1),
                }
            else:  # SQLite tuple result
                return {"total_sessions": row[0], "total_hours": round(row[1] / 60, 1)}

    @staticmethod
    def get_unique_gyms(user_id: int) -> list[str]:
        """Get list of unique gym names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT DISTINCT gym_name FROM sessions WHERE user_id = ? ORDER BY gym_name"
                ),
                (user_id,),
            )
            rows = cursor.fetchall()
            # Handle both dict (PostgreSQL) and tuple (SQLite) results
            if rows and hasattr(rows[0], "keys"):
                return [row["gym_name"] for row in rows]
            else:
                return [row[0] for row in rows]

    @staticmethod
    def get_unique_locations(user_id: int) -> list[str]:
        """Get list of unique locations from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT DISTINCT location FROM sessions
                WHERE user_id = ? AND location IS NOT NULL
                ORDER BY location
                """),
                (user_id,),
            )
            rows = cursor.fetchall()
            # Handle both dict (PostgreSQL) and tuple (SQLite) results
            if rows and hasattr(rows[0], "keys"):
                return [row["location"] for row in rows]
            else:
                return [row[0] for row in rows]

    @staticmethod
    def get_unique_partners(user_id: int) -> list[str]:
        """Get list of unique partner names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT partners FROM sessions WHERE user_id = ? AND partners IS NOT NULL"
                ),
                (user_id,),
            )
            partners_set = set()
            rows = cursor.fetchall()
            for row in rows:
                # Handle both dict (PostgreSQL) and tuple (SQLite) results
                if hasattr(row, "keys"):
                    partners_list = json.loads(row["partners"])
                else:
                    partners_list = json.loads(row[0])
                partners_set.update(partners_list)
            return sorted(partners_set)

    @staticmethod
    def get_last_n_sessions_by_type(user_id: int, n: int = 5) -> list[str]:
        """Get the class types of the last N sessions."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                SELECT class_type FROM sessions
                WHERE user_id = ?
                ORDER BY session_date DESC, created_at DESC
                LIMIT ?
                """),
                (user_id, n),
            )
            rows = cursor.fetchall()
            # Handle both dict (PostgreSQL) and tuple (SQLite) results
            if rows and hasattr(rows[0], "keys"):
                return [row["class_type"] for row in rows]
            else:
                return [row[0] for row in rows]

    @staticmethod
    def delete(user_id: int, session_id: int) -> bool:
        """Delete a session and all related records atomically."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Delete related child records in same transaction
            cursor.execute(
                convert_query("DELETE FROM session_rolls WHERE session_id = ?"),
                (session_id,),
            )
            cursor.execute(
                convert_query("DELETE FROM session_techniques WHERE session_id = ?"),
                (session_id,),
            )

            # Delete the session itself
            cursor.execute(
                convert_query("DELETE FROM sessions WHERE id = ? AND user_id = ?"),
                (session_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        data = dict(row)
        # Parse JSON fields - ensure arrays are never null
        if data.get("partners"):
            data["partners"] = json.loads(data["partners"])
        else:
            data["partners"] = []

        if data.get("techniques"):
            data["techniques"] = json.loads(data["techniques"])
        else:
            data["techniques"] = []
        # Parse dates (handle both string and datetime/date types)
        if data.get("session_date"):
            if isinstance(data["session_date"], str):
                data["session_date"] = date.fromisoformat(data["session_date"])
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        # Convert needs_review to bool (SQLite stores as INTEGER)
        data["needs_review"] = bool(data.get("needs_review", 0))
        # Parse score_breakdown JSON
        if data.get("score_breakdown"):
            data["score_breakdown"] = json.loads(data["score_breakdown"])
        return data
