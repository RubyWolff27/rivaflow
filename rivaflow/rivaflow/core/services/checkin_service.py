"""Daily check-in service."""

import logging
from datetime import date

from rivaflow.core.time_utils import user_today
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.profile_repo import ProfileRepository

logger = logging.getLogger(__name__)


class CheckinService:
    """Wraps CheckinRepository with timezone-aware helpers."""

    def __init__(self):
        self.repo = CheckinRepository()

    def get_user_timezone(self, user_id: int) -> str | None:
        """Get user's timezone from profile."""
        profile = ProfileRepository.get(user_id)
        return profile.get("timezone") if profile else None

    def get_today(self, user_id: int) -> date:
        """Get today's date in the user's timezone."""
        tz = self.get_user_timezone(user_id)
        return user_today(tz)

    def get_day_checkins(self, user_id: int, check_date: date) -> dict:
        return self.repo.get_day_checkins(user_id=user_id, check_date=check_date)

    def get_checkins_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        return self.repo.get_checkins_range(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

    def get_checkin(
        self, user_id: int, check_date: date, checkin_slot: str = "morning"
    ) -> dict | None:
        return self.repo.get_checkin(
            user_id=user_id, check_date=check_date, checkin_slot=checkin_slot
        )

    def get_checkin_by_id(self, user_id: int, checkin_id: int) -> dict | None:
        return self.repo.get_checkin_by_id(user_id=user_id, checkin_id=checkin_id)

    def upsert_checkin(self, **kwargs) -> int:
        logger.info(
            "Upserting %s check-in for user %d on %s",
            kwargs.get("checkin_slot", "morning"),
            kwargs["user_id"],
            kwargs["check_date"],
        )
        return self.repo.upsert_checkin(**kwargs)

    def upsert_midday(self, **kwargs) -> int:
        logger.info("Upserting midday check-in for user %d", kwargs["user_id"])
        return self.repo.upsert_midday(**kwargs)

    def upsert_evening(self, **kwargs) -> int:
        logger.info("Upserting evening check-in for user %d", kwargs["user_id"])
        return self.repo.upsert_evening(**kwargs)

    def update_tomorrow_intention(
        self,
        user_id: int,
        check_date: date,
        intention: str,
        checkin_slot: str = "morning",
    ) -> None:
        self.repo.update_tomorrow_intention(
            user_id=user_id,
            check_date=check_date,
            intention=intention,
            checkin_slot=checkin_slot,
        )

    def delete_checkin(self, user_id: int, checkin_id: int) -> bool:
        logger.info("Deleting check-in %d for user %d", checkin_id, user_id)
        return self.repo.delete_checkin(user_id=user_id, checkin_id=checkin_id)
