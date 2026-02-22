"""Repository for session data access."""

import json
from datetime import date, datetime

from rivaflow.core.settings import settings
from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

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


class SessionRepository(BaseRepository):
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
                    bool(needs_review),
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
        return {r["id"] for r in rows}

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
                "needs_review": lambda v: bool(v),
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
    def list_by_user(user_id: int, limit: int = 200) -> list[dict]:
        """Get sessions for a user.

        Args:
            user_id: User ID
            limit: Maximum sessions to return (default 200)
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    f"SELECT {_SESSION_COLS} FROM sessions"
                    " WHERE user_id = ? ORDER BY session_date DESC"
                    " LIMIT ?"
                ),
                (user_id, limit),
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
            return {
                "total_sessions": row["total_sessions"],
                "total_hours": round(row["total_minutes"] / 60, 1),
            }

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
            return [row["gym_name"] for row in rows]

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
            return [row["location"] for row in rows]

    @staticmethod
    def get_unique_partners(user_id: int) -> list[str]:
        """Get list of unique partner names from history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if settings.DB_TYPE == "postgresql":
                cursor.execute(
                    "SELECT DISTINCT value FROM sessions, "
                    "json_array_elements_text(partners::json) "
                    "WHERE user_id = %s AND partners IS NOT NULL "
                    "ORDER BY value",
                    (user_id,),
                )
                return [row["value"] for row in cursor.fetchall()]
            cursor.execute(
                convert_query(
                    "SELECT DISTINCT partners FROM sessions "
                    "WHERE user_id = ? AND partners IS NOT NULL"
                ),
                (user_id,),
            )
            partners_set: set[str] = set()
            for row in cursor.fetchall():
                partners_set.update(json.loads(row["partners"]))
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
            return [row["class_type"] for row in rows]

    @staticmethod
    def delete(user_id: int, session_id: int) -> bool:
        """Delete a session and all related records atomically.

        Verifies ownership BEFORE deleting child records to prevent
        orphan deletion of another user's data.
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership first
            cursor.execute(
                convert_query("SELECT id FROM sessions WHERE id = ? AND user_id = ?"),
                (session_id, user_id),
            )
            if not cursor.fetchone():
                return False

            # Now safe to delete child records
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
    def get_active_user_count(since_date: str) -> int:
        """Count distinct users with sessions since a given date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT COUNT(DISTINCT user_id) FROM sessions"
                    " WHERE session_date >= ?"
                ),
                (since_date,),
            )
            row = cursor.fetchone()
            if not row:
                return 0
            if isinstance(row, dict):
                return list(row.values())[0] or 0
            try:
                return row[0]
            except (KeyError, IndexError, TypeError):
                return 0

    @staticmethod
    def get_total_count() -> int:
        """Get total session count across all users."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT COUNT(*) FROM sessions"))
            row = cursor.fetchone()
            if not row:
                return 0
            if isinstance(row, dict):
                return list(row.values())[0] or 0
            try:
                return row[0]
            except (KeyError, IndexError, TypeError):
                return 0

    @staticmethod
    def get_total_comment_count() -> int:
        """Get total activity_comments count across all users."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT COUNT(*) FROM activity_comments"))
            row = cursor.fetchone()
            if not row:
                return 0
            if isinstance(row, dict):
                return list(row.values())[0] or 0
            try:
                return row[0]
            except (KeyError, IndexError, TypeError):
                return 0

    @staticmethod
    def get_adjacent_ids(user_id: int, session_id: int) -> dict:
        """Get previous and next session IDs for navigation.

        Uses two simple queries instead of a window function over the
        entire user session history, which is cheaper for large tables.
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get current session's date for ordering context
            cursor.execute(
                convert_query(
                    "SELECT session_date FROM sessions" " WHERE id = ? AND user_id = ?"
                ),
                (session_id, user_id),
            )
            current = cursor.fetchone()
            if not current:
                return {
                    "previous_session_id": None,
                    "next_session_id": None,
                }

            cur_date = current["session_date"]

            # Previous (older) session
            cursor.execute(
                convert_query(
                    "SELECT id FROM sessions"
                    " WHERE user_id = ?"
                    "   AND (session_date < ? OR (session_date = ? AND id < ?))"
                    " ORDER BY session_date DESC, id DESC"
                    " LIMIT 1"
                ),
                (user_id, cur_date, cur_date, session_id),
            )
            prev_row = cursor.fetchone()

            # Next (newer) session
            cursor.execute(
                convert_query(
                    "SELECT id FROM sessions"
                    " WHERE user_id = ?"
                    "   AND (session_date > ? OR (session_date = ? AND id > ?))"
                    " ORDER BY session_date ASC, id ASC"
                    " LIMIT 1"
                ),
                (user_id, cur_date, cur_date, session_id),
            )
            next_row = cursor.fetchone()

        return {
            "previous_session_id": prev_row["id"] if prev_row else None,
            "next_session_id": next_row["id"] if next_row else None,
        }

    @staticmethod
    def get_new_techniques_for_session(user_id: int, session_id: int) -> list[dict]:
        """Get techniques in a session that the user has never trained before."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT DISTINCT st.movement_id, mg.name
                    FROM session_techniques st
                    JOIN sessions s ON st.session_id = s.id
                    JOIN movements_glossary mg ON st.movement_id = mg.id
                    WHERE st.session_id = ? AND s.user_id = ?
                    AND st.movement_id NOT IN (
                        SELECT st2.movement_id FROM session_techniques st2
                        JOIN sessions s2 ON st2.session_id = s2.id
                        WHERE s2.user_id = ? AND s2.id != ?
                    )
                """),
                (session_id, user_id, user_id, session_id),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append({"name": row["name"]})
            return results

    @staticmethod
    def get_session_techniques_with_names(user_id: int, session_id: int) -> list[dict]:
        """Get techniques for a session with movement_id, name, and total count.

        Uses a single query with a correlated subquery instead of N+1.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        st.movement_id,
                        mg.name,
                        (
                            SELECT COUNT(DISTINCT st2.session_id)
                            FROM session_techniques st2
                            JOIN sessions s2 ON st2.session_id = s2.id
                            WHERE st2.movement_id = st.movement_id
                              AND s2.user_id = ?
                        ) AS session_count
                    FROM session_techniques st
                    JOIN sessions s ON st.session_id = s.id
                    JOIN movements_glossary mg ON st.movement_id = mg.id
                    WHERE st.session_id = ? AND s.user_id = ?
                    GROUP BY st.movement_id, mg.name
                """),
                (user_id, session_id, user_id),
            )
            return [
                {
                    "movement_id": row["movement_id"],
                    "name": row["name"],
                    "session_count": row["session_count"] or 0,
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def count_rolls_with_partner(
        user_id: int,
        partner_id: int | None,
        partner_name: str,
    ) -> int:
        """Count total rolls with a specific partner."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if partner_id:
                cursor.execute(
                    convert_query("""
                        SELECT COUNT(*) as cnt FROM session_rolls sr
                        JOIN sessions s ON sr.session_id = s.id
                        WHERE s.user_id = ? AND sr.partner_id = ?
                    """),
                    (user_id, partner_id),
                )
            else:
                cursor.execute(
                    convert_query("""
                        SELECT COUNT(*) as cnt FROM session_rolls sr
                        JOIN sessions s ON sr.session_id = s.id
                        WHERE s.user_id = ? AND sr.partner_name = ?
                    """),
                    (user_id, partner_name),
                )
            row = cursor.fetchone()
            return row["cnt"]

    @staticmethod
    def count_partner_sessions(user_id: int, partner_name: str) -> int:
        """Count sessions where partner appears in the partners JSON list.

        Uses SQL LIKE filter to push matching to the database instead of
        fetching all rows and parsing JSON in Python.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            # JSON list stores names as quoted strings; LIKE is safe here
            # because partner_name comes from our own data, not user input.
            cursor.execute(
                convert_query("""
                    SELECT COUNT(*) as cnt FROM sessions
                    WHERE user_id = ? AND partners IS NOT NULL
                      AND partners LIKE ?
                """),
                (user_id, f"%{partner_name}%"),
            )
            result = cursor.fetchone()
            return result["cnt"] or 0

    @staticmethod
    def get_max_rolls_excluding(user_id: int, exclude_id: int) -> int:
        """Get maximum rolls count excluding a specific session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT MAX(rolls) as max_rolls FROM sessions
                    WHERE user_id = ? AND id != ?
                """),
                (user_id, exclude_id),
            )
            row = cursor.fetchone()
            return row["max_rolls"] or 0

    @staticmethod
    def get_max_duration_excluding(user_id: int, exclude_id: int) -> int:
        """Get maximum duration_mins excluding a specific session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT MAX(duration_mins) as max_dur FROM sessions
                    WHERE user_id = ? AND id != ?
                """),
                (user_id, exclude_id),
            )
            row = cursor.fetchone()
            return row["max_dur"] or 0

    @staticmethod
    def count_sessions_on_date(user_id: int, date_str: str) -> int:
        """Count sessions for a user on a specific date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT COUNT(*) as cnt FROM sessions
                    WHERE user_id = ? AND session_date = ?
                """),
                (user_id, date_str),
            )
            row = cursor.fetchone()
            return row["cnt"]

    @staticmethod
    def get_week_duration_sum(user_id: int, week_start: str) -> int:
        """Get sum of duration_mins for sessions in the current week."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT SUM(duration_mins) as total FROM sessions
                    WHERE session_date >= ? AND user_id = ?
                """),
                (week_start, user_id),
            )
            result = cursor.fetchone()
            return int(result["total"]) if result["total"] is not None else 0

    # Whitelist of allowed GROUP BY expressions for week_format to prevent
    # SQL injection — callers must pass one of these exact strings.
    _VALID_WEEK_FORMATS = frozenset(
        {
            "strftime('%Y-%W', session_date)",
            "strftime('%W', session_date)",
            "to_char(session_date::date, 'IYYY-IW')",
            "to_char(session_date::date, 'IW')",
        }
    )

    @staticmethod
    def get_avg_weekly_duration(
        user_id: int,
        start_date: str,
        end_date: str,
        week_format: str,
    ) -> float:
        """Get average weekly duration_mins across a date range."""
        if week_format not in SessionRepository._VALID_WEEK_FORMATS:
            raise ValueError(
                f"Invalid week_format: {week_format!r}. "
                f"Must be one of {sorted(SessionRepository._VALID_WEEK_FORMATS)}"
            )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(f"""
                    SELECT AVG(weekly_mins) as avg FROM (
                        SELECT SUM(duration_mins) as weekly_mins
                        FROM sessions
                        WHERE session_date >= ? AND session_date < ?
                          AND user_id = ?
                        GROUP BY {week_format}
                    ) subq
                """),
                (start_date, end_date, user_id),
            )
            result = cursor.fetchone()
            return float(result["avg"]) if result["avg"] is not None else 0.0

    @staticmethod
    def count_sessions_since(user_id: int, since_date: str) -> int:
        """Count sessions since a given date (for recovery insights)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT COUNT(*) as count FROM sessions
                    WHERE session_date >= ? AND user_id = ?
                """),
                (since_date, user_id),
            )
            result = cursor.fetchone()
            return result["count"] or 0

    @staticmethod
    def get_submission_stats(
        user_id: int, start_date: str, end_date: str | None = None
    ) -> dict:
        """Get submission totals and session count for a date range."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if end_date:
                cursor.execute(
                    convert_query("""
                        SELECT
                            SUM(submissions_for) as subs,
                            COUNT(*) as sessions
                        FROM sessions
                        WHERE session_date >= ?
                          AND session_date < ?
                          AND user_id = ?
                    """),
                    (start_date, end_date, user_id),
                )
            else:
                cursor.execute(
                    convert_query("""
                        SELECT
                            SUM(submissions_for) as subs,
                            COUNT(*) as sessions
                        FROM sessions
                        WHERE session_date >= ? AND user_id = ?
                    """),
                    (start_date, user_id),
                )
            row = cursor.fetchone()
            if row:
                d = dict(row)
                return {
                    "subs": d["subs"],
                    "sessions": d["sessions"],
                }
            return {"subs": 0, "sessions": 0}

    @staticmethod
    def get_fight_dynamics_sessions(user_id: int, start_date: str) -> list[dict]:
        """Get sessions with fight dynamics data since a date."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        session_date,
                        attacks_attempted,
                        attacks_successful,
                        defenses_attempted,
                        defenses_successful
                    FROM sessions
                    WHERE user_id = ?
                        AND session_date >= ?
                        AND (
                            attacks_attempted > 0
                            OR defenses_attempted > 0
                        )
                    ORDER BY session_date ASC
                """),
                (user_id, start_date),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_fight_dynamics_totals(
        user_id: int, start_date: str, end_date: str
    ) -> dict[str, int]:
        """Get aggregated fight dynamics totals for a date range."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        COUNT(*) as session_count,
                        COALESCE(SUM(attacks_attempted), 0)
                            as attacks_attempted,
                        COALESCE(SUM(attacks_successful), 0)
                            as attacks_successful,
                        COALESCE(SUM(defenses_attempted), 0)
                            as defenses_attempted,
                        COALESCE(SUM(defenses_successful), 0)
                            as defenses_successful
                    FROM sessions
                    WHERE user_id = ?
                        AND session_date >= ?
                        AND session_date < ?
                        AND (
                            attacks_attempted > 0
                            OR defenses_attempted > 0
                        )
                """),
                (user_id, start_date, end_date),
            )
            row = cursor.fetchone()
            if row is None:
                return {
                    "session_count": 0,
                    "attacks_attempted": 0,
                    "attacks_successful": 0,
                    "defenses_attempted": 0,
                    "defenses_successful": 0,
                }
            row_dict = dict(row)
            return {
                "session_count": row_dict["session_count"] or 0,
                "attacks_attempted": row_dict["attacks_attempted"] or 0,
                "attacks_successful": row_dict["attacks_successful"] or 0,
                "defenses_attempted": row_dict["defenses_attempted"] or 0,
                "defenses_successful": row_dict["defenses_successful"] or 0,
            }

    @staticmethod
    def get_user_averages(user_id: int) -> dict:
        """Get last-30-session averages for scoring normalisation."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        AVG(duration_mins) as avg_duration,
                        AVG(intensity) as avg_intensity,
                        AVG(rolls) as avg_rolls
                    FROM (
                        SELECT duration_mins, intensity, rolls
                        FROM sessions
                        WHERE user_id = ?
                        ORDER BY session_date DESC
                        LIMIT 30
                    ) recent
                """),
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "avg_duration": 60,
                    "avg_intensity": 3,
                    "avg_rolls": 5,
                }
            return {
                "avg_duration": float(row["avg_duration"] or 60),
                "avg_intensity": float(row["avg_intensity"] or 3),
                "avg_rolls": float(row["avg_rolls"] or 5),
            }

    @staticmethod
    def clear_whoop_fields(user_id: int) -> None:
        """Clear WHOOP fields from all sessions for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE sessions
                    SET whoop_strain = NULL,
                        whoop_calories = NULL,
                        whoop_avg_hr = NULL,
                        whoop_max_hr = NULL
                    WHERE user_id = ?
                      AND (whoop_strain IS NOT NULL
                           OR whoop_calories IS NOT NULL
                           OR whoop_avg_hr IS NOT NULL
                           OR whoop_max_hr IS NOT NULL)
                """),
                (user_id,),
            )

    @staticmethod
    def get_milestone_totals(user_id: int) -> dict:
        """Get hours, sessions, rolls, partners, techniques totals.

        Consolidated from 5 queries into 2 for better performance.
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Query 1: session-level aggregates (hours, count, rolls)
            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) as cnt,"
                    " COALESCE(SUM(duration_mins), 0) as total_mins,"
                    " COALESCE(SUM(rolls), 0) as total_rolls"
                    " FROM sessions WHERE user_id = ?"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            total_mins = row["total_mins"] or 0
            sessions = row["cnt"] or 0
            rolls = row["total_rolls"] or 0

            # Query 2: distinct partners + distinct techniques via UNION
            cursor.execute(
                convert_query("""
                    SELECT
                        (SELECT COUNT(DISTINCT sr.partner_id)
                         FROM session_rolls sr
                         JOIN sessions s ON sr.session_id = s.id
                         WHERE sr.partner_id IS NOT NULL AND s.user_id = ?
                        ) AS partners,
                        (SELECT COUNT(DISTINCT st.movement_id)
                         FROM session_techniques st
                         JOIN sessions s ON st.session_id = s.id
                         WHERE s.user_id = ?
                        ) AS techniques
                """),
                (user_id, user_id),
            )
            row2 = cursor.fetchone()
            partners = row2["partners"] or 0
            techniques = row2["techniques"] or 0

        return {
            "hours": int(total_mins / 60),
            "sessions": sessions,
            "rolls": rolls,
            "partners": partners,
            "techniques": techniques,
        }

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
