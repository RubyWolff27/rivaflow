"""Repository for Grapple chat sessions data access."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from rivaflow.db.database import convert_query, get_connection


class ChatSessionRepository:
    """Repository for managing Grapple AI Coach chat sessions."""

    @staticmethod
    def create(user_id: int, title: str | None = None) -> dict[str, Any]:
        """
        Create a new chat session.

        Args:
            user_id: User ID
            title: Optional session title (defaults to "New Chat")

        Returns:
            Created session dict
        """
        session_id = str(uuid4())
        session_title = title or "New Chat"

        query = convert_query(
            """
            INSERT INTO chat_sessions (id, user_id, title, message_count, total_tokens, total_cost_usd)
            VALUES (?, ?, ?, 0, 0, 0.0)
            RETURNING id, user_id, title, message_count, total_tokens, total_cost_usd, created_at, updated_at
        """
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, user_id, session_title))
            row = cursor.fetchone()
            conn.commit()

            if row:
                # Handle both dict (PostgreSQL) and tuple (SQLite) results
                if hasattr(row, "keys"):
                    # PostgreSQL RealDictCursor
                    return dict(row)
                else:
                    # SQLite tuple
                    return {
                        "id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "message_count": row[3],
                        "total_tokens": row[4],
                        "total_cost_usd": float(row[5]) if row[5] else 0.0,
                        "created_at": row[6],
                        "updated_at": row[7],
                    }
            return {}

    @staticmethod
    def get_by_id(session_id: str, user_id: int) -> dict[str, Any] | None:
        """
        Get a session by ID.

        Args:
            session_id: Session UUID
            user_id: User ID (for ownership check)

        Returns:
            Session dict or None
        """
        query = """
            SELECT id, user_id, title, message_count, total_tokens, total_cost_usd, created_at, updated_at
            FROM chat_sessions
            WHERE id = ? AND user_id = ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, user_id))
            row = cursor.fetchone()

            if row:
                # Handle both dict (PostgreSQL) and tuple (SQLite) results
                if hasattr(row, "keys"):
                    # PostgreSQL RealDictCursor
                    return dict(row)
                else:
                    # SQLite tuple
                    return {
                        "id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "message_count": row[3],
                        "total_tokens": row[4],
                        "total_cost_usd": float(row[5]) if row[5] else 0.0,
                        "created_at": row[6],
                        "updated_at": row[7],
                    }
            return None

    @staticmethod
    def get_by_user(
        user_id: int, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        Get sessions for a user.

        Args:
            user_id: User ID
            limit: Max sessions to return
            offset: Offset for pagination

        Returns:
            List of session dicts
        """
        query = """
            SELECT id, user_id, title, message_count, total_tokens, total_cost_usd, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, limit, offset))
            rows = cursor.fetchall()

            # Handle both dict (PostgreSQL) and tuple (SQLite) results
            if rows and hasattr(rows[0], "keys"):
                # PostgreSQL RealDictCursor
                return [dict(row) for row in rows]
            else:
                # SQLite tuple
                return [
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "title": row[2],
                        "message_count": row[3],
                        "total_tokens": row[4],
                        "total_cost_usd": float(row[5]) if row[5] else 0.0,
                        "created_at": row[6],
                        "updated_at": row[7],
                    }
                    for row in rows
                ]

    @staticmethod
    def update_stats(
        session_id: str,
        message_count_delta: int = 0,
        tokens_delta: int = 0,
        cost_delta: float = 0.0,
    ) -> bool:
        """
        Update session statistics.

        Args:
            session_id: Session UUID
            message_count_delta: Messages to add
            tokens_delta: Tokens to add
            cost_delta: Cost to add

        Returns:
            True if updated
        """
        query = convert_query(
            """
            UPDATE chat_sessions
            SET message_count = message_count + ?,
                total_tokens = total_tokens + ?,
                total_cost_usd = total_cost_usd + ?,
                updated_at = ?
            WHERE id = ?
        """
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    message_count_delta,
                    tokens_delta,
                    cost_delta,
                    datetime.utcnow(),
                    session_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def update_title(session_id: str, user_id: int, title: str) -> bool:
        """Update session title."""
        query = convert_query(
            """
            UPDATE chat_sessions
            SET title = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, datetime.utcnow(), session_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete(session_id: str, user_id: int) -> bool:
        """
        Delete a session and all its messages (CASCADE).

        Args:
            session_id: Session UUID
            user_id: User ID (for ownership check)

        Returns:
            True if deleted
        """
        query = "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
