"""Events and competition prep service."""

import logging

from rivaflow.db.repositories.events_repo import EventRepository
from rivaflow.db.repositories.weight_log_repo import WeightLogRepository

logger = logging.getLogger(__name__)


class EventsService:
    """Wraps EventRepository and WeightLogRepository."""

    def __init__(self):
        self.event_repo = EventRepository()
        self.weight_repo = WeightLogRepository()

    # -- Events --

    def create_event(self, user_id: int, data: dict) -> int:
        logger.info("Creating event '%s' for user %d", data.get("name"), user_id)
        return self.event_repo.create(user_id=user_id, data=data)

    def get_event_by_id(self, user_id: int, event_id: int) -> dict | None:
        return self.event_repo.get_by_id(user_id=user_id, event_id=event_id)

    def list_events(self, user_id: int, status: str | None = None) -> list[dict]:
        return self.event_repo.list_by_user(user_id=user_id, status=status)

    def update_event(self, user_id: int, event_id: int, data: dict) -> bool:
        logger.info("Updating event %d for user %d", event_id, user_id)
        return self.event_repo.update(user_id=user_id, event_id=event_id, data=data)

    def delete_event(self, user_id: int, event_id: int) -> bool:
        logger.info("Deleting event %d for user %d", event_id, user_id)
        return self.event_repo.delete(user_id=user_id, event_id=event_id)

    def get_next_upcoming(self, user_id: int) -> dict | None:
        return self.event_repo.get_next_upcoming(user_id=user_id)

    # -- Weight logs --

    def create_weight_log(self, user_id: int, data: dict) -> int:
        logger.info("Logging weight for user %d", user_id)
        return self.weight_repo.create(user_id=user_id, data=data)

    def list_weight_logs(
        self,
        user_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        return self.weight_repo.list_by_user(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

    def get_latest_weight(self, user_id: int) -> dict | None:
        return self.weight_repo.get_latest(user_id=user_id)

    def get_weight_averages(self, user_id: int, period: str = "weekly") -> list[dict]:
        return self.weight_repo.get_averages(user_id=user_id, period=period)
