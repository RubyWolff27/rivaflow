"""Streak tracking business logic."""

from datetime import date

from rivaflow.db.repositories.streak_repo import StreakRepository


class StreakService:
    """Business logic for streak tracking and management."""

    def __init__(self):
        self.streak_repo = StreakRepository()

    def record_checkin(
        self, user_id: int, checkin_type: str, checkin_date: date | None = None
    ) -> dict:
        """
        Record a check-in and update relevant streaks.

        Args:
            user_id: User ID
            checkin_type: 'session', 'rest', or 'readiness_only'
            checkin_date: Date of check-in (defaults to today)

        Returns dict with:
        - checkin_streak: current checkin streak
        - training_streak: current training streak (if session)
        - readiness_streak: current readiness streak (if readiness logged)
        - streak_extended: bool - did we extend a streak?
        - grace_day_used: bool - did we use a grace day?
        - longest_beaten: bool - did we beat our longest streak?
        """
        if checkin_date is None:
            checkin_date = date.today()

        result = {
            "checkin_streak": None,
            "training_streak": None,
            "readiness_streak": None,
            "streak_extended": False,
            "grace_day_used": False,
            "longest_beaten": False,
        }

        # Always update check-in streak
        old_checkin_streak = self.streak_repo.get_streak(user_id, "checkin")
        new_checkin_streak = self.streak_repo.update_streak(
            user_id, "checkin", checkin_date
        )
        result["checkin_streak"] = new_checkin_streak

        if new_checkin_streak["current_streak"] > old_checkin_streak["current_streak"]:
            result["streak_extended"] = True

        if (
            new_checkin_streak["grace_days_used"]
            > old_checkin_streak["grace_days_used"]
        ):
            result["grace_day_used"] = True

        if new_checkin_streak["current_streak"] > old_checkin_streak["longest_streak"]:
            result["longest_beaten"] = True

        # Update training streak if session
        if checkin_type == "session":
            old_training_streak = self.streak_repo.get_streak(user_id, "training")
            new_training_streak = self.streak_repo.update_streak(
                user_id, "training", checkin_date
            )
            result["training_streak"] = new_training_streak

            if (
                new_training_streak["current_streak"]
                > old_training_streak["longest_streak"]
            ):
                result["longest_beaten"] = True

        # Update readiness streak if readiness was logged
        # (This will be called separately when readiness is logged)

        return result

    def record_readiness_checkin(
        self, user_id: int, checkin_date: date | None = None
    ) -> dict:
        """
        Record a readiness check-in and update readiness streak.

        Returns dict with:
        - readiness_streak: current readiness streak
        - streak_extended: bool
        - grace_day_used: bool
        - longest_beaten: bool
        """
        if checkin_date is None:
            checkin_date = date.today()

        old_readiness_streak = self.streak_repo.get_streak(user_id, "readiness")
        new_readiness_streak = self.streak_repo.update_streak(
            user_id, "readiness", checkin_date
        )

        return {
            "readiness_streak": new_readiness_streak,
            "streak_extended": new_readiness_streak["current_streak"]
            > old_readiness_streak["current_streak"],
            "grace_day_used": new_readiness_streak["grace_days_used"]
            > old_readiness_streak["grace_days_used"],
            "longest_beaten": new_readiness_streak["current_streak"]
            > old_readiness_streak["longest_streak"],
        }

    def get_streak_status(self, user_id: int) -> dict:
        """
        Get current status of all streaks.

        Returns dict with:
        - checkin: streak dict
        - training: streak dict
        - readiness: streak dict
        - any_at_risk: bool
        """
        streaks = {
            "checkin": self.streak_repo.get_streak(user_id, "checkin"),
            "training": self.streak_repo.get_streak(user_id, "training"),
            "readiness": self.streak_repo.get_streak(user_id, "readiness"),
        }

        streaks["any_at_risk"] = (
            self.streak_repo.is_streak_at_risk(user_id, "checkin")
            or self.streak_repo.is_streak_at_risk(user_id, "training")
            or self.streak_repo.is_streak_at_risk(user_id, "readiness")
        )

        return streaks

    def is_streak_at_risk(self, user_id: int, streak_type: str | None = None) -> bool:
        """
        Check if user will lose streak if they don't check in today.

        Args:
            user_id: User ID
            streak_type: Specific streak type to check, or None to check all

        Returns:
            True if any streak is at risk (or specified streak is at risk)
        """
        if streak_type:
            return self.streak_repo.is_streak_at_risk(user_id, streak_type)

        return (
            self.streak_repo.is_streak_at_risk(user_id, "checkin")
            or self.streak_repo.is_streak_at_risk(user_id, "training")
            or self.streak_repo.is_streak_at_risk(user_id, "readiness")
        )

    def get_streak(self, user_id: int, streak_type: str) -> dict:
        """Get a specific streak."""
        return self.streak_repo.get_streak(user_id, streak_type)

    def get_all_streaks(self, user_id: int) -> list[dict]:
        """Get all streak types."""
        return self.streak_repo.get_all_streaks(user_id)
