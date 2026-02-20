"""Repository for session event data access."""

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class SessionEventRepository(BaseRepository):
    """Data access layer for session events (extracted technique events)."""

    @staticmethod
    def create(
        session_id: int,
        user_id: int,
        event_type: str,
        technique_name: str | None = None,
        glossary_id: int | None = None,
        position: str | None = None,
        outcome: str | None = None,
        partner_name: str | None = None,
        notes: str | None = None,
        event_order: int = 0,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """INSERT INTO session_events
                (session_id, user_id, event_type,
                 technique_name, glossary_id, position,
                 outcome, partner_name, notes, event_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    user_id,
                    event_type,
                    technique_name,
                    glossary_id,
                    position,
                    outcome,
                    partner_name,
                    notes,
                    event_order,
                ),
            )

    @staticmethod
    def bulk_create(events: list[dict]) -> list[int]:
        ids = []
        with get_connection() as conn:
            cursor = conn.cursor()
            for event in events:
                event_id = execute_insert(
                    cursor,
                    """INSERT INTO session_events
                    (session_id, user_id, event_type,
                     technique_name, glossary_id, position,
                     outcome, partner_name, notes,
                     event_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event["session_id"],
                        event["user_id"],
                        event["event_type"],
                        event.get("technique_name"),
                        event.get("glossary_id"),
                        event.get("position"),
                        event.get("outcome"),
                        event.get("partner_name"),
                        event.get("notes"),
                        event.get("event_order", 0),
                    ),
                )
                ids.append(event_id)
        return ids

    @staticmethod
    def list_by_session(session_id: int) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM session_events"
                    " WHERE session_id = ?"
                    " ORDER BY event_order"
                ),
                (session_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def list_by_user(user_id: int, limit: int = 50) -> list[dict]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT * FROM session_events"
                    " WHERE user_id = ?"
                    " ORDER BY created_at DESC LIMIT ?"
                ),
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete_by_session(session_id: int) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM session_events" " WHERE session_id = ?"),
                (session_id,),
            )
            return cursor.rowcount
