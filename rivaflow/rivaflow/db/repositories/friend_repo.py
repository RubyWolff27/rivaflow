"""Repository for friends (training partners and instructors) data access."""
import sqlite3
from typing import List, Optional

from rivaflow.db.database import get_connection, convert_query, execute_insert
from rivaflow.core.constants import FRIEND_SORT_OPTIONS


class FriendRepository:
    """Data access layer for friends."""

    @staticmethod
    def create(
        user_id: int,
        name: str,
        friend_type: str = "training-partner",
        belt_rank: Optional[str] = None,
        gym: Optional[str] = None,
        notes: Optional[str] = None,
        # Legacy parameters - ignored but kept for API compatibility
        belt_stripes: int = 0,
        instructor_certification: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """Create a new friend."""
        with get_connection() as conn:
            cursor = conn.cursor()
            friend_id = execute_insert(
                cursor,
                """
                INSERT INTO friends
                (user_id, name, friend_type, belt_rank, gym, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, friend_type, belt_rank, gym, notes),
            )

            # Return the created friend
            cursor.execute(convert_query("SELECT * FROM friends WHERE id = ? AND user_id = ?"), (friend_id, user_id))
            row = cursor.fetchone()
            return FriendRepository._row_to_dict(row)

    @staticmethod
    def get_by_id(user_id: int, friend_id: int) -> Optional[dict]:
        """Get a friend by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM friends WHERE id = ? AND user_id = ?"), (friend_id, user_id))
            row = cursor.fetchone()
            return FriendRepository._row_to_dict(row) if row else None

    @staticmethod
    def get_by_name(user_id: int, name: str) -> Optional[dict]:
        """Get a friend by exact name match."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("SELECT * FROM friends WHERE user_id = ? AND name = ?"), (user_id, name))
            row = cursor.fetchone()
            return FriendRepository._row_to_dict(row) if row else None

    @staticmethod
    def list_all(user_id: int, order_by: str = "name ASC") -> List[dict]:
        """Get all friends, ordered by name alphabetically by default."""
        # Whitelist allowed ORDER BY values to prevent SQL injection
        if order_by not in FRIEND_SORT_OPTIONS:
            order_by = "name ASC"  # Safe default

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query(f"SELECT * FROM friends WHERE user_id = ? ORDER BY {order_by}"), (user_id,))
            rows = cursor.fetchall()
            return [FriendRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def list_by_type(user_id: int, friend_type: str, order_by: str = "name ASC") -> List[dict]:
        """Get friends filtered by type."""
        # Whitelist allowed ORDER BY values to prevent SQL injection
        if order_by not in FRIEND_SORT_OPTIONS:
            order_by = "name ASC"  # Safe default

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(f"SELECT * FROM friends WHERE user_id = ? AND friend_type = ? ORDER BY {order_by}"),
                (user_id, friend_type),
            )
            rows = cursor.fetchall()
            return [FriendRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def search(user_id: int, query: str) -> List[dict]:
        """Search friends by name (case-insensitive partial match)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM friends WHERE user_id = ? AND name LIKE ? ORDER BY name ASC"),
                (user_id, f"%{query}%"),
            )
            rows = cursor.fetchall()
            return [FriendRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def update(
        user_id: int,
        friend_id: int,
        name: Optional[str] = None,
        friend_type: Optional[str] = None,
        belt_rank: Optional[str] = None,
        gym: Optional[str] = None,
        notes: Optional[str] = None,
        # Legacy parameters - ignored but kept for API compatibility
        belt_stripes: Optional[int] = None,
        instructor_certification: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[dict]:
        """Update a friend by ID. Returns updated friend or None if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if friend_type is not None:
                updates.append("friend_type = ?")
                params.append(friend_type)
            if belt_rank is not None:
                updates.append("belt_rank = ?")
                params.append(belt_rank)
            if gym is not None:
                updates.append("gym = ?")
                params.append(gym)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            # Legacy parameters ignored (belt_stripes, instructor_certification, phone, email)

            if not updates:
                # No updates provided, just return current record
                return FriendRepository.get_by_id(user_id, friend_id)

            # Add updated_at timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([friend_id, user_id])

            query = f"UPDATE friends SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            cursor.execute(convert_query(query), params)

            if cursor.rowcount == 0:
                return None

            return FriendRepository.get_by_id(user_id, friend_id)

    @staticmethod
    def delete(user_id: int, friend_id: int) -> bool:
        """Delete a friend by ID. Returns True if deleted, False if not found."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("DELETE FROM friends WHERE id = ? AND user_id = ?"), (friend_id, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}

        data = dict(row)

        # Convert integer to actual int (SQLite returns all as int already)
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "belt_stripes" in data and data["belt_stripes"] is not None:
            data["belt_stripes"] = int(data["belt_stripes"])

        return data
