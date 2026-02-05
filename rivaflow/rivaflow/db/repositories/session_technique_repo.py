"""Repository for session techniques (detailed technique tracking) data access."""

import json
import sqlite3

from rivaflow.db.database import convert_query, execute_insert, get_connection


class SessionTechniqueRepository:
    """Data access layer for session techniques."""

    @staticmethod
    def create(
        session_id: int,
        user_id: int,
        movement_id: int,
        technique_number: int = 1,
        notes: str | None = None,
        media_urls: list[dict] | None = None,
    ) -> dict:
        """Create a new session technique record.

        Note: user_id parameter is kept for API compatibility but not used
        since session_techniques table doesn't have user_id column.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            technique_id = execute_insert(
                cursor,
                """
                INSERT INTO session_techniques
                (session_id, movement_id, technique_number, notes, media_urls)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    movement_id,
                    technique_number,
                    notes,
                    json.dumps(media_urls) if media_urls else None,
                ),
            )

            # Return the created technique
            cursor.execute(
                convert_query("SELECT * FROM session_techniques WHERE id = ?"),
                (technique_id,),
            )
            row = cursor.fetchone()
            return SessionTechniqueRepository._row_to_dict(row)

    @staticmethod
    def get_by_id(technique_id: int) -> dict | None:
        """Get a session technique by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM session_techniques WHERE id = ?"),
                (technique_id,),
            )
            row = cursor.fetchone()
            return SessionTechniqueRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_by_session_id(user_id: int, session_id: int) -> list[dict]:
        """Get all techniques for a specific session."""
        # Note: session_techniques doesn't have user_id column
        # Security is enforced by session_id since sessions belong to users
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM session_techniques WHERE session_id = ? ORDER BY technique_number ASC"
                ),
                (session_id,),
            )
            rows = cursor.fetchall()
            return [SessionTechniqueRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def list_by_movement(user_id: int, movement_id: int) -> list[dict]:
        """Get all technique records for a specific movement."""
        # Note: session_techniques doesn't have user_id, filter via sessions JOIN
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    """
                SELECT st.* FROM session_techniques st
                JOIN sessions s ON st.session_id = s.id
                WHERE st.movement_id = ? AND s.user_id = ?
                ORDER BY s.session_date DESC, st.technique_number ASC
                """
                ),
                (movement_id, user_id),
            )
            rows = cursor.fetchall()
            return [SessionTechniqueRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def update(
        technique_id: int,
        movement_id: int | None = None,
        technique_number: int | None = None,
        notes: str | None = None,
        media_urls: list[dict] | None = None,
    ) -> dict | None:
        """Update a session technique by ID. Returns updated technique or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if movement_id is not None:
                updates.append("movement_id = ?")
                params.append(movement_id)
            if technique_number is not None:
                updates.append("technique_number = ?")
                params.append(technique_number)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if media_urls is not None:
                updates.append("media_urls = ?")
                params.append(json.dumps(media_urls) if media_urls else None)

            if not updates:
                # No updates provided, just return current record
                return SessionTechniqueRepository.get_by_id(technique_id)

            params.append(technique_id)
            query = f"UPDATE session_techniques SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(convert_query(query), params)

            if cursor.rowcount == 0:
                return None

            return SessionTechniqueRepository.get_by_id(technique_id)

    @staticmethod
    def delete(technique_id: int) -> bool:
        """Delete a session technique by ID. Returns True if deleted, False if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM session_techniques WHERE id = ?"),
                (technique_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_by_session(session_id: int) -> int:
        """Delete all techniques for a session. Returns count of deleted techniques."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM session_techniques WHERE session_id = ?"),
                (session_id,),
            )
            return cursor.rowcount

    @staticmethod
    def batch_get_by_session_ids(session_ids: list[int]) -> dict:
        """
        Batch load techniques for multiple sessions with movement names.
        Returns dict mapping session_id to list of techniques.
        Avoids N+1 queries when loading multiple sessions.
        """
        if not session_ids:
            return {}

        with get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(session_ids))
            cursor.execute(
                convert_query(
                    f"""
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
                    WHERE st.session_id IN ({placeholders})
                    ORDER BY st.session_id, st.technique_number
                """
                ),
                session_ids,
            )

            # Group techniques by session_id
            techniques_by_session = {}
            for row in cursor.fetchall():
                technique = SessionTechniqueRepository._row_to_dict(row)
                session_id = technique["session_id"]
                if session_id not in techniques_by_session:
                    techniques_by_session[session_id] = []
                techniques_by_session[session_id].append(technique)

            return techniques_by_session

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}

        data = dict(row)

        # Convert integer fields
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "session_id" in data and data["session_id"] is not None:
            data["session_id"] = int(data["session_id"])
        if "movement_id" in data and data["movement_id"] is not None:
            data["movement_id"] = int(data["movement_id"])
        if "technique_number" in data and data["technique_number"] is not None:
            data["technique_number"] = int(data["technique_number"])

        # Parse JSON array for media_urls
        if data.get("media_urls"):
            try:
                data["media_urls"] = json.loads(data["media_urls"])
            except (json.JSONDecodeError, TypeError):
                data["media_urls"] = []
        else:
            data["media_urls"] = []

        return data
