"""Repository for session rolls (detailed roll tracking) data access."""
import sqlite3
import json
from typing import List, Optional

from rivaflow.db.database import get_connection


class SessionRollRepository:
    """Data access layer for session rolls."""

    @staticmethod
    def create(
        session_id: int,
        user_id: int,
        roll_number: int = 1,
        partner_id: Optional[int] = None,
        partner_name: Optional[str] = None,
        duration_mins: Optional[int] = None,
        submissions_for: Optional[List[int]] = None,
        submissions_against: Optional[List[int]] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """Create a new session roll record."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO session_rolls
                (session_id, user_id, roll_number, partner_id, partner_name, duration_mins, submissions_for, submissions_against, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    roll_number,
                    partner_id,
                    partner_name,
                    duration_mins,
                    json.dumps(submissions_for) if submissions_for else None,
                    json.dumps(submissions_against) if submissions_against else None,
                    notes,
                ),
            )
            roll_id = cursor.lastrowid

            # Return the created roll
            cursor.execute("SELECT * FROM session_rolls WHERE id = ?", (roll_id,))
            row = cursor.fetchone()
            return SessionRollRepository._row_to_dict(row)

    @staticmethod
    def get_by_id(roll_id: int) -> Optional[dict]:
        """Get a session roll by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_rolls WHERE id = ?", (roll_id,))
            row = cursor.fetchone()
            return SessionRollRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_by_session_id(user_id: int, session_id: int) -> List[dict]:
        """Get all rolls for a specific session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM session_rolls WHERE session_id = ? AND user_id = ? ORDER BY roll_number ASC",
                (session_id, user_id),
            )
            rows = cursor.fetchall()
            return [SessionRollRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def list_by_partner(user_id: int, partner_id: int) -> List[dict]:
        """Get all rolls with a specific partner."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sr.* FROM session_rolls sr
                JOIN sessions s ON sr.session_id = s.id
                WHERE sr.partner_id = ? AND sr.user_id = ?
                ORDER BY s.session_date DESC, sr.roll_number ASC
                """,
                (partner_id, user_id),
            )
            rows = cursor.fetchall()
            return [SessionRollRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_by_partner_id(user_id: int, partner_id: int) -> List[dict]:
        """Alias for list_by_partner. Get all rolls with a specific partner."""
        return SessionRollRepository.list_by_partner(user_id, partner_id)

    @staticmethod
    def get_partner_stats(user_id: int, partner_id: int) -> dict:
        """Get analytics for a specific partner."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get total rolls count
            cursor.execute(
                "SELECT COUNT(*) as total_rolls FROM session_rolls WHERE partner_id = ? AND user_id = ?",
                (partner_id, user_id),
            )
            total_rolls = cursor.fetchone()[0]

            # Get all rolls to calculate submission stats
            rolls = SessionRollRepository.list_by_partner(user_id, partner_id)

            total_subs_for = 0
            total_subs_against = 0

            for roll in rolls:
                if roll.get("submissions_for"):
                    total_subs_for += len(roll["submissions_for"])
                if roll.get("submissions_against"):
                    total_subs_against += len(roll["submissions_against"])

            return {
                "partner_id": partner_id,
                "total_rolls": total_rolls,
                "total_submissions_for": total_subs_for,
                "total_submissions_against": total_subs_against,
                "subs_per_roll": round(total_subs_for / total_rolls, 2) if total_rolls > 0 else 0,
                "taps_per_roll": round(total_subs_against / total_rolls, 2) if total_rolls > 0 else 0,
                "sub_ratio": round(total_subs_for / total_subs_against, 2) if total_subs_against > 0 else float('inf') if total_subs_for > 0 else 0,
            }

    @staticmethod
    def update(
        roll_id: int,
        roll_number: Optional[int] = None,
        partner_id: Optional[int] = None,
        partner_name: Optional[str] = None,
        duration_mins: Optional[int] = None,
        submissions_for: Optional[List[int]] = None,
        submissions_against: Optional[List[int]] = None,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Update a session roll by ID. Returns updated roll or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if roll_number is not None:
                updates.append("roll_number = ?")
                params.append(roll_number)
            if partner_id is not None:
                updates.append("partner_id = ?")
                params.append(partner_id)
            if partner_name is not None:
                updates.append("partner_name = ?")
                params.append(partner_name)
            if duration_mins is not None:
                updates.append("duration_mins = ?")
                params.append(duration_mins)
            if submissions_for is not None:
                updates.append("submissions_for = ?")
                params.append(json.dumps(submissions_for) if submissions_for else None)
            if submissions_against is not None:
                updates.append("submissions_against = ?")
                params.append(json.dumps(submissions_against) if submissions_against else None)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)

            if not updates:
                # No updates provided, just return current record
                return SessionRollRepository.get_by_id(roll_id)

            params.append(roll_id)
            query = f"UPDATE session_rolls SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return None

            return SessionRollRepository.get_by_id(roll_id)

    @staticmethod
    def delete(roll_id: int) -> bool:
        """Delete a session roll by ID. Returns True if deleted, False if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_rolls WHERE id = ?", (roll_id,))
            return cursor.rowcount > 0

    @staticmethod
    def delete_by_session(session_id: int) -> int:
        """Delete all rolls for a session. Returns count of deleted rolls."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_rolls WHERE session_id = ?", (session_id,))
            return cursor.rowcount

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
        if "partner_id" in data and data["partner_id"] is not None:
            data["partner_id"] = int(data["partner_id"])
        if "roll_number" in data and data["roll_number"] is not None:
            data["roll_number"] = int(data["roll_number"])
        if "duration_mins" in data and data["duration_mins"] is not None:
            data["duration_mins"] = int(data["duration_mins"])

        # Parse JSON arrays for submissions
        if data.get("submissions_for"):
            try:
                data["submissions_for"] = json.loads(data["submissions_for"])
            except (json.JSONDecodeError, TypeError):
                data["submissions_for"] = []
        else:
            data["submissions_for"] = []

        if data.get("submissions_against"):
            try:
                data["submissions_against"] = json.loads(data["submissions_against"])
            except (json.JSONDecodeError, TypeError):
                data["submissions_against"] = []
        else:
            data["submissions_against"] = []

        return data
