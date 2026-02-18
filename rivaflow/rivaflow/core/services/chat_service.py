"""Chat service for Grapple AI sessions and messages."""

import logging
from typing import Any

from rivaflow.db.repositories.chat_message_repo import ChatMessageRepository
from rivaflow.db.repositories.chat_session_repo import ChatSessionRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Wraps ChatSessionRepository and ChatMessageRepository."""

    def __init__(self):
        self.session_repo = ChatSessionRepository()
        self.message_repo = ChatMessageRepository()

    # -- Session methods --

    def create_session(self, user_id: int, title: str | None = None) -> dict[str, Any]:
        logger.info("Creating chat session for user %d", user_id)
        return self.session_repo.create(user_id, title=title)

    def get_session_by_id(self, session_id: str, user_id: int) -> dict[str, Any] | None:
        return self.session_repo.get_by_id(session_id, user_id)

    def get_sessions_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        return self.session_repo.get_by_user(user_id, limit=limit, offset=offset)

    def update_session_stats(
        self,
        session_id: str,
        message_count_delta: int = 0,
        tokens_delta: int = 0,
        cost_delta: float = 0.0,
    ) -> bool:
        return self.session_repo.update_stats(
            session_id=session_id,
            message_count_delta=message_count_delta,
            tokens_delta=tokens_delta,
            cost_delta=cost_delta,
        )

    def update_session_title(self, session_id: str, user_id: int, title: str) -> bool:
        logger.info("Updating title for session %s", session_id)
        return self.session_repo.update_title(session_id, user_id, title)

    def delete_session(self, session_id: str, user_id: int) -> bool:
        logger.info("Deleting session %s for user %d", session_id, user_id)
        return self.session_repo.delete(session_id, user_id)

    # -- Message methods --

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> dict[str, Any]:
        return self.message_repo.create(
            session_id=session_id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )

    def get_messages_by_session(
        self, session_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        return self.message_repo.get_by_session(session_id, limit=limit)

    def get_recent_context(
        self, session_id: str, max_messages: int = 10
    ) -> list[dict[str, str]]:
        return self.message_repo.get_recent_context(
            session_id, max_messages=max_messages
        )

    def count_messages_by_session(self, session_id: str) -> int:
        return self.message_repo.count_by_session(session_id)
