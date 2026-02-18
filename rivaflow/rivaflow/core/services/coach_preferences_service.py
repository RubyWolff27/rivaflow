"""Coach preferences service for Grapple AI personalization."""

import logging

from rivaflow.db.repositories.coach_preferences_repo import (
    CoachPreferencesRepository,
)

logger = logging.getLogger(__name__)


class CoachPreferencesService:
    """Wraps CoachPreferencesRepository."""

    def get(self, user_id: int) -> dict | None:
        return CoachPreferencesRepository.get(user_id)

    def upsert(self, user_id: int, **fields) -> dict | None:
        logger.info("Upserting coach preferences for user %d", user_id)
        return CoachPreferencesRepository.upsert(user_id, **fields)
