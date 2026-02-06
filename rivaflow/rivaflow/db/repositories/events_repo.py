"""Repository for events data access."""

import sqlite3

from rivaflow.db.database import convert_query, execute_insert, get_connection


class EventRepository:
    """Data access layer for events."""

    @staticmethod
    def create(user_id: int, data: dict) -> int:
        """Create a new event. Returns the event ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            event_id = execute_insert(
                cursor,
                """
                INSERT INTO events
                (user_id, name, event_type, event_date, location,
                 weight_class, target_weight, division, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data["name"],
                    data.get("event_type", "competition"),
                    data["event_date"],
                    data.get("location"),
                    data.get("weight_class"),
                    data.get("target_weight"),
                    data.get("division"),
                    data.get("notes"),
                    data.get("status", "upcoming"),
                ),
            )
            return event_id

    @staticmethod
    def get_by_id(user_id: int, event_id: int) -> dict | None:
        """Get an event by ID for a specific user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM events WHERE id = ? AND user_id = ?"),
                (event_id, user_id),
            )
            row = cursor.fetchone()
            return EventRepository._row_to_dict(row) if row else None

    @staticmethod
    def list_by_user(user_id: int, status: str | None = None) -> list[dict]:
        """List events for a user, optionally filtered by status."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    convert_query(
                        "SELECT * FROM events WHERE user_id = ? AND status = ? "
                        "ORDER BY event_date ASC"
                    ),
                    (user_id, status),
                )
            else:
                cursor.execute(
                    convert_query(
                        "SELECT * FROM events WHERE user_id = ? "
                        "ORDER BY event_date ASC"
                    ),
                    (user_id,),
                )
            rows = cursor.fetchall()
            return [EventRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def update(user_id: int, event_id: int, data: dict) -> bool:
        """Update an event. Returns True if updated."""
        with get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            allowed_fields = [
                "name",
                "event_type",
                "event_date",
                "location",
                "weight_class",
                "target_weight",
                "division",
                "notes",
                "status",
            ]

            for field in allowed_fields:
                if field in data:
                    updates.append(f"{field} = ?")
                    params.append(data[field])

            if not updates:
                return False

            params.extend([event_id, user_id])
            query = (
                f"UPDATE events SET {', '.join(updates)} "
                "WHERE id = ? AND user_id = ?"
            )
            cursor.execute(convert_query(query), params)
            return cursor.rowcount > 0

    @staticmethod
    def delete(user_id: int, event_id: int) -> bool:
        """Delete an event. Returns True if deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM events WHERE id = ? AND user_id = ?"),
                (event_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_next_upcoming(user_id: int) -> dict | None:
        """Get the next upcoming event for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM events "
                    "WHERE user_id = ? AND status = 'upcoming' "
                    "AND event_date >= date('now') "
                    "ORDER BY event_date ASC LIMIT 1"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            return EventRepository._row_to_dict(row) if row else None

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a database row to a dictionary."""
        if not row:
            return {}
        data = dict(row)
        if "id" in data and data["id"] is not None:
            data["id"] = int(data["id"])
        if "user_id" in data and data["user_id"] is not None:
            data["user_id"] = int(data["user_id"])
        if "target_weight" in data and data["target_weight"] is not None:
            data["target_weight"] = float(data["target_weight"])
        return data
