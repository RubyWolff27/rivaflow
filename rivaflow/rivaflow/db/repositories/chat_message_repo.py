"""Repository for Grapple chat messages data access."""

from typing import Any
from uuid import uuid4

from rivaflow.db.database import convert_query, get_connection


class ChatMessageRepository:
    """Repository for managing Grapple AI Coach chat messages."""

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert database row to dictionary."""
        result = dict(row)
        if result.get("cost_usd") is not None:
            result["cost_usd"] = float(result["cost_usd"])
        return result

    @staticmethod
    def create(
        session_id: str,
        role: str,
        content: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> dict[str, Any]:
        """
        Create a new chat message.

        Args:
            session_id: Session UUID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            cost_usd: Cost in USD

        Returns:
            Created message dict
        """
        message_id = str(uuid4())

        query = convert_query("""
            INSERT INTO chat_messages (id, session_id, role, content, input_tokens, output_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id, session_id, role, content, input_tokens, output_tokens, cost_usd, created_at
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    input_tokens,
                    output_tokens,
                    cost_usd,
                ),
            )
            row = cursor.fetchone()

            if row:
                return ChatMessageRepository._row_to_dict(row)
            return {}

    @staticmethod
    def get_by_session(session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get messages for a session.

        Args:
            session_id: Session UUID
            limit: Max messages to return

        Returns:
            List of message dicts ordered by created_at ASC
        """
        query = convert_query("""
            SELECT id, session_id, role, content, input_tokens, output_tokens, cost_usd, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, limit))
            rows = cursor.fetchall()

            return [ChatMessageRepository._row_to_dict(row) for row in rows]

    @staticmethod
    def get_recent_context(
        session_id: str, max_messages: int = 10
    ) -> list[dict[str, str]]:
        """
        Get recent messages for context (formatted for LLM).

        Args:
            session_id: Session UUID
            max_messages: Maximum messages to include

        Returns:
            List of dicts with 'role' and 'content' keys
        """
        query = convert_query("""
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, max_messages))
            rows = cursor.fetchall()

            # Reverse to get chronological order
            messages = []
            for row in reversed(rows):
                messages.append({"role": row["role"], "content": row["content"]})
            return messages

    @staticmethod
    def count_by_session(session_id: str) -> int:
        """Get message count for a session."""
        query = convert_query(
            "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?"
        )

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            if result:
                return result["count"]
            return 0
