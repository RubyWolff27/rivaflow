"""Repository for Grapple chat messages data access."""
from typing import List, Dict, Any, Optional
from uuid import uuid4

from rivaflow.db.database import get_connection, convert_query


class ChatMessageRepository:
    """Repository for managing Grapple AI Coach chat messages."""

    @staticmethod
    def create(
        session_id: str,
        role: str,
        content: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
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
                (message_id, session_id, role, content, input_tokens, output_tokens, cost_usd),
            )
            row = cursor.fetchone()
            conn.commit()

            if row:
                return {
                    "id": row[0],
                    "session_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "input_tokens": row[4],
                    "output_tokens": row[5],
                    "cost_usd": float(row[6]) if row[6] else 0.0,
                    "created_at": row[7],
                }
            return {}

    @staticmethod
    def get_by_session(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get messages for a session.

        Args:
            session_id: Session UUID
            limit: Max messages to return

        Returns:
            List of message dicts ordered by created_at ASC
        """
        query = """
            SELECT id, session_id, role, content, input_tokens, output_tokens, cost_usd, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, limit))
            rows = cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "input_tokens": row[4],
                    "output_tokens": row[5],
                    "cost_usd": float(row[6]) if row[6] else 0.0,
                    "created_at": row[7],
                }
                for row in rows
            ]

    @staticmethod
    def get_recent_context(session_id: str, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get recent messages for context (formatted for LLM).

        Args:
            session_id: Session UUID
            max_messages: Maximum messages to include

        Returns:
            List of dicts with 'role' and 'content' keys
        """
        query = """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id, max_messages))
            rows = cursor.fetchall()

            # Reverse to get chronological order
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    @staticmethod
    def count_by_session(session_id: str) -> int:
        """Get message count for a session."""
        query = "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
