"""Feedback service."""

import logging

from rivaflow.db.repositories.feedback_repo import FeedbackRepository

logger = logging.getLogger(__name__)


class FeedbackService:
    """Wraps FeedbackRepository."""

    def __init__(self):
        self.repo = FeedbackRepository()

    def create(self, **kwargs) -> int:
        logger.info(
            "Creating %s feedback from user %d",
            kwargs.get("category"),
            kwargs["user_id"],
        )
        return self.repo.create(**kwargs)

    def get_by_id(self, feedback_id: int) -> dict | None:
        return self.repo.get_by_id(feedback_id)

    def list_by_user(self, user_id: int, limit: int = 50) -> list[dict]:
        return self.repo.list_by_user(user_id, limit=limit)

    def list_all(
        self,
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        return self.repo.list_all(
            status=status, category=category, limit=limit, offset=offset
        )

    def get_stats(self) -> dict:
        return self.repo.get_stats()

    def update_status(
        self,
        feedback_id: int,
        status: str,
        admin_notes: str | None = None,
    ) -> bool:
        return self.repo.update_status(
            feedback_id=feedback_id, status=status, admin_notes=admin_notes
        )
