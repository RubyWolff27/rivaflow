"""Service layer for monthly training goals."""

import calendar
from datetime import date

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.session_technique_repo import (
    SessionTechniqueRepository,
)
from rivaflow.db.repositories.training_goal_repo import TrainingGoalRepository

VALID_METRICS = {"sessions", "hours", "rolls", "submissions", "technique_count"}
VALID_GOAL_TYPES = {"frequency", "technique"}


class TrainingGoalsService:
    """Business logic for monthly training goals."""

    def __init__(self):
        self.goal_repo = TrainingGoalRepository()
        self.session_repo = SessionRepository()

    def create_goal(
        self,
        user_id: int,
        goal_type: str,
        metric: str,
        target_value: int,
        month: str,
        movement_id: int | None = None,
        class_type_filter: str | None = None,
    ) -> dict:
        """Create a new training goal with validation."""
        if goal_type not in VALID_GOAL_TYPES:
            raise ValidationError(
                f"goal_type must be one of: {', '.join(VALID_GOAL_TYPES)}"
            )
        if metric not in VALID_METRICS:
            raise ValidationError(f"metric must be one of: {', '.join(VALID_METRICS)}")
        if target_value <= 0:
            raise ValidationError("target_value must be greater than 0")

        # Validate month format YYYY-MM
        if not _valid_month(month):
            raise ValidationError("month must be in YYYY-MM format")

        # Technique goals require movement_id and metric=technique_count
        if goal_type == "technique":
            if not movement_id:
                raise ValidationError("movement_id is required for technique goals")
            if metric != "technique_count":
                raise ValidationError(
                    "technique goals must use metric 'technique_count'"
                )
        elif goal_type == "frequency" and metric == "technique_count":
            raise ValidationError("frequency goals cannot use metric 'technique_count'")

        goal_id = self.goal_repo.create(
            user_id=user_id,
            goal_type=goal_type,
            metric=metric,
            target_value=target_value,
            month=month,
            movement_id=movement_id,
            class_type_filter=class_type_filter,
        )

        goal = self.goal_repo.get_by_id(goal_id, user_id)
        if not goal:
            raise ValidationError("Failed to create goal")

        return self._attach_progress(goal, user_id, month)

    def get_goals_with_progress(self, user_id: int, month: str) -> list[dict]:
        """Get all goals for a month with computed progress."""
        if not _valid_month(month):
            raise ValidationError("month must be in YYYY-MM format")

        goals = self.goal_repo.list_by_month(user_id, month)
        if not goals:
            return []

        # Pre-fetch sessions for the month once
        start, end = _month_date_range(month)
        sessions = SessionRepository.get_by_date_range(user_id, start, end)

        for goal in goals:
            self._compute_progress(goal, sessions)

        return goals

    def get_goal_with_progress(self, user_id: int, goal_id: int) -> dict:
        """Get a single goal with progress."""
        goal = self.goal_repo.get_by_id(goal_id, user_id)
        if not goal:
            raise NotFoundError("Goal not found")
        return self._attach_progress(goal, user_id, goal["month"])

    def update_goal(
        self,
        user_id: int,
        goal_id: int,
        target_value: int | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """Update a training goal."""
        if target_value is not None and target_value <= 0:
            raise ValidationError("target_value must be greater than 0")

        result = self.goal_repo.update(
            goal_id, user_id, target_value=target_value, is_active=is_active
        )
        if not result:
            raise NotFoundError("Goal not found")

        return self._attach_progress(result, user_id, result["month"])

    def delete_goal(self, user_id: int, goal_id: int) -> bool:
        """Delete a training goal."""
        deleted = self.goal_repo.delete(goal_id, user_id)
        if not deleted:
            raise NotFoundError("Goal not found")
        return True

    # --- helpers ---

    def _attach_progress(self, goal: dict, user_id: int, month: str) -> dict:
        """Attach progress fields to a single goal."""
        start, end = _month_date_range(month)
        sessions = SessionRepository.get_by_date_range(user_id, start, end)
        self._compute_progress(goal, sessions)
        return goal

    def _compute_progress(self, goal: dict, sessions: list[dict]) -> None:
        """Compute actual_value, progress_pct, completed in-place."""
        metric = goal["metric"]
        class_filter = goal.get("class_type_filter")

        # Optionally filter sessions by class_type
        filtered = sessions
        if class_filter:
            filtered = [s for s in sessions if s.get("class_type") == class_filter]

        if metric == "sessions":
            actual = len(filtered)
        elif metric == "hours":
            actual = round(sum(s.get("duration_mins", 0) for s in filtered) / 60, 1)
        elif metric == "rolls":
            actual = sum(s.get("rolls", 0) for s in filtered)
        elif metric == "submissions":
            actual = sum(s.get("submissions_for", 0) for s in filtered)
        elif metric == "technique_count":
            movement_id = goal.get("movement_id")
            if movement_id and filtered:
                session_ids = [s["id"] for s in filtered]
                actual = SessionTechniqueRepository.count_by_movement_in_sessions(
                    movement_id, session_ids
                )
            else:
                actual = 0
        else:
            actual = 0

        target = goal["target_value"]
        goal["actual_value"] = actual
        goal["progress_pct"] = (
            round(min(actual / target, 1.0) * 100, 1) if target > 0 else 0
        )
        goal["completed"] = actual >= target


def _valid_month(month: str) -> bool:
    """Validate YYYY-MM format."""
    if not month or len(month) != 7 or month[4] != "-":
        return False
    try:
        int(month[:4])
        m = int(month[5:])
        return 1 <= m <= 12
    except ValueError:
        return False


def _month_date_range(month: str) -> tuple[date, date]:
    """Return (first_day, last_day) for a YYYY-MM string."""
    year = int(month[:4])
    m = int(month[5:])
    last_day = calendar.monthrange(year, m)[1]
    return date(year, m, 1), date(year, m, last_day)
