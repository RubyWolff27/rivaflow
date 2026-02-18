"""Waitlist service."""

import logging

from rivaflow.db.repositories.waitlist_repo import WaitlistRepository

logger = logging.getLogger(__name__)


class WaitlistService:
    """Wraps WaitlistRepository."""

    def __init__(self):
        self.repo = WaitlistRepository()

    def create(self, **kwargs) -> dict:
        logger.info("Adding %s to waitlist", kwargs.get("email"))
        return self.repo.create(**kwargs)

    def get_by_id(self, waitlist_id: int) -> dict | None:
        return self.repo.get_by_id(waitlist_id)

    def get_by_email(self, email: str) -> dict | None:
        return self.repo.get_by_email(email)

    def get_waiting_count(self) -> int:
        return self.repo.get_waiting_count()

    def get_count(self, status: str | None = None) -> int:
        return self.repo.get_count(status=status)

    def list_all(self, **kwargs) -> list[dict]:
        return self.repo.list_all(**kwargs)

    def invite(self, waitlist_id: int, assigned_tier: str = "free") -> str | None:
        logger.info(
            "Inviting waitlist entry %d with tier %s", waitlist_id, assigned_tier
        )
        return self.repo.invite(waitlist_id, assigned_tier=assigned_tier)

    def bulk_invite(
        self, waitlist_ids: list[int], assigned_tier: str = "free"
    ) -> list[tuple]:
        logger.info("Bulk inviting %d waitlist entries", len(waitlist_ids))
        return self.repo.bulk_invite(waitlist_ids, assigned_tier=assigned_tier)

    def decline(self, waitlist_id: int) -> bool:
        logger.info("Declining waitlist entry %d", waitlist_id)
        return self.repo.decline(waitlist_id)

    def update_notes(self, waitlist_id: int, notes: str) -> bool:
        return self.repo.update_notes(waitlist_id, notes)

    def mark_registered(self, email: str) -> bool:
        return self.repo.mark_registered(email)

    def is_invite_valid(self, token: str) -> bool:
        return self.repo.is_invite_valid(token)
