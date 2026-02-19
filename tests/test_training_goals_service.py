"""Unit tests for TrainingGoalsService -- monthly training goals."""

from datetime import date
from unittest.mock import patch

import pytest

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.training_goals_service import (
    TrainingGoalsService,
    _month_date_range,
    _valid_month,
)


class TestValidMonth:
    """Tests for _valid_month helper."""

    def test_valid_format(self):
        assert _valid_month("2025-01") is True
        assert _valid_month("2025-12") is True

    def test_invalid_format(self):
        assert _valid_month("") is False
        assert _valid_month("2025") is False
        assert _valid_month("2025-00") is False
        assert _valid_month("2025-13") is False
        assert _valid_month("abcd-ef") is False
        assert _valid_month("2025/01") is False


class TestMonthDateRange:
    """Tests for _month_date_range helper."""

    def test_january(self):
        start, end = _month_date_range("2025-01")
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_february_non_leap(self):
        start, end = _month_date_range("2025-02")
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_february_leap_year(self):
        start, end = _month_date_range("2024-02")
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)


class TestCreateGoal:
    """Tests for create_goal."""

    @patch("rivaflow.core.services.training_goals_service.SessionRepository")
    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_creates_frequency_goal(self, MockGoalRepo, MockSessionRepo):
        """Should create a frequency goal with progress attached."""
        MockGoalRepo.return_value.create.return_value = 1
        mock_goal = {
            "id": 1,
            "goal_type": "frequency",
            "metric": "sessions",
            "target_value": 12,
            "month": "2025-01",
        }
        MockGoalRepo.return_value.get_by_id.return_value = mock_goal
        MockSessionRepo.get_by_date_range.return_value = []

        service = TrainingGoalsService()
        result = service.create_goal(
            user_id=1,
            goal_type="frequency",
            metric="sessions",
            target_value=12,
            month="2025-01",
        )

        assert result["id"] == 1
        assert result["actual_value"] == 0
        assert result["progress_pct"] == 0
        assert result["completed"] is False

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_rejects_invalid_goal_type(self, MockGoalRepo):
        """Should raise ValidationError for invalid goal_type."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="goal_type"):
            service.create_goal(
                user_id=1,
                goal_type="invalid",
                metric="sessions",
                target_value=10,
                month="2025-01",
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_rejects_invalid_metric(self, MockGoalRepo):
        """Should raise ValidationError for invalid metric."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="metric"):
            service.create_goal(
                user_id=1,
                goal_type="frequency",
                metric="invalid",
                target_value=10,
                month="2025-01",
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_rejects_zero_target(self, MockGoalRepo):
        """Should raise ValidationError when target_value is 0."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="target_value"):
            service.create_goal(
                user_id=1,
                goal_type="frequency",
                metric="sessions",
                target_value=0,
                month="2025-01",
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_rejects_invalid_month(self, MockGoalRepo):
        """Should raise ValidationError for invalid month format."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="YYYY-MM"):
            service.create_goal(
                user_id=1,
                goal_type="frequency",
                metric="sessions",
                target_value=10,
                month="invalid",
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_technique_goal_requires_movement_id(self, MockGoalRepo):
        """Should raise ValidationError for technique goal without movement_id."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="movement_id"):
            service.create_goal(
                user_id=1,
                goal_type="technique",
                metric="technique_count",
                target_value=5,
                month="2025-01",
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_technique_goal_requires_technique_count_metric(self, MockGoalRepo):
        """Should raise ValidationError when technique goal uses wrong metric."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="technique_count"):
            service.create_goal(
                user_id=1,
                goal_type="technique",
                metric="sessions",
                target_value=5,
                month="2025-01",
                movement_id=10,
            )

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_frequency_goal_rejects_technique_count(self, MockGoalRepo):
        """Should raise ValidationError for frequency goal with technique_count."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError, match="technique_count"):
            service.create_goal(
                user_id=1,
                goal_type="frequency",
                metric="technique_count",
                target_value=5,
                month="2025-01",
            )


class TestGetGoalsWithProgress:
    """Tests for get_goals_with_progress."""

    @patch("rivaflow.core.services.training_goals_service.SessionRepository")
    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_returns_goals_with_progress(self, MockGoalRepo, MockSessionRepo):
        """Should compute progress for each goal."""
        MockGoalRepo.return_value.list_by_month.return_value = [
            {
                "id": 1,
                "metric": "sessions",
                "target_value": 10,
                "class_type_filter": None,
            },
        ]
        MockSessionRepo.get_by_date_range.return_value = [
            {"id": i, "duration_mins": 60, "rolls": 3} for i in range(5)
        ]

        service = TrainingGoalsService()
        result = service.get_goals_with_progress(user_id=1, month="2025-01")

        assert len(result) == 1
        assert result[0]["actual_value"] == 5
        assert result[0]["progress_pct"] == 50.0
        assert result[0]["completed"] is False

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_returns_empty_when_no_goals(self, MockGoalRepo):
        """Should return empty list when no goals for month."""
        MockGoalRepo.return_value.list_by_month.return_value = []

        service = TrainingGoalsService()
        result = service.get_goals_with_progress(user_id=1, month="2025-01")

        assert result == []

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_rejects_invalid_month(self, MockGoalRepo):
        """Should raise ValidationError for invalid month."""
        service = TrainingGoalsService()
        with pytest.raises(ValidationError):
            service.get_goals_with_progress(user_id=1, month="bad")


class TestGetGoalWithProgress:
    """Tests for get_goal_with_progress."""

    @patch("rivaflow.core.services.training_goals_service.SessionRepository")
    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_returns_goal(self, MockGoalRepo, MockSessionRepo):
        """Should return single goal with progress."""
        MockGoalRepo.return_value.get_by_id.return_value = {
            "id": 1,
            "metric": "rolls",
            "target_value": 50,
            "month": "2025-01",
            "class_type_filter": None,
        }
        MockSessionRepo.get_by_date_range.return_value = [
            {"id": 1, "rolls": 30},
        ]

        service = TrainingGoalsService()
        result = service.get_goal_with_progress(user_id=1, goal_id=1)

        assert result["actual_value"] == 30

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_raises_not_found(self, MockGoalRepo):
        """Should raise NotFoundError when goal does not exist."""
        MockGoalRepo.return_value.get_by_id.return_value = None

        service = TrainingGoalsService()
        with pytest.raises(NotFoundError, match="Goal not found"):
            service.get_goal_with_progress(user_id=1, goal_id=999)


class TestDeleteGoal:
    """Tests for delete_goal."""

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_deletes_goal(self, MockGoalRepo):
        """Should return True when goal is deleted."""
        MockGoalRepo.return_value.delete.return_value = True

        service = TrainingGoalsService()
        result = service.delete_goal(user_id=1, goal_id=1)

        assert result is True

    @patch("rivaflow.core.services.training_goals_service.TrainingGoalRepository")
    def test_raises_not_found(self, MockGoalRepo):
        """Should raise NotFoundError when goal does not exist."""
        MockGoalRepo.return_value.delete.return_value = False

        service = TrainingGoalsService()
        with pytest.raises(NotFoundError):
            service.delete_goal(user_id=1, goal_id=999)


class TestComputeProgress:
    """Tests for _compute_progress."""

    def test_sessions_metric(self):
        """Should count number of sessions."""
        service = TrainingGoalsService()
        goal = {"metric": "sessions", "target_value": 10}
        sessions = [{"id": i} for i in range(8)]

        service._compute_progress(goal, sessions)

        assert goal["actual_value"] == 8
        assert goal["progress_pct"] == 80.0
        assert goal["completed"] is False

    def test_hours_metric(self):
        """Should sum duration_mins and convert to hours."""
        service = TrainingGoalsService()
        goal = {"metric": "hours", "target_value": 10}
        sessions = [
            {"id": 1, "duration_mins": 90},
            {"id": 2, "duration_mins": 60},
        ]

        service._compute_progress(goal, sessions)

        assert goal["actual_value"] == 2.5

    def test_rolls_metric(self):
        """Should sum rolls."""
        service = TrainingGoalsService()
        goal = {"metric": "rolls", "target_value": 50}
        sessions = [{"id": 1, "rolls": 5}, {"id": 2, "rolls": 8}]

        service._compute_progress(goal, sessions)

        assert goal["actual_value"] == 13

    def test_submissions_metric(self):
        """Should sum submissions_for."""
        service = TrainingGoalsService()
        goal = {"metric": "submissions", "target_value": 10}
        sessions = [
            {"id": 1, "submissions_for": 3},
            {"id": 2, "submissions_for": 2},
        ]

        service._compute_progress(goal, sessions)

        assert goal["actual_value"] == 5

    def test_completed_when_target_reached(self):
        """Should set completed=True when target is met."""
        service = TrainingGoalsService()
        goal = {"metric": "sessions", "target_value": 3}
        sessions = [{"id": i} for i in range(5)]

        service._compute_progress(goal, sessions)

        assert goal["completed"] is True
        assert goal["progress_pct"] == 100.0

    def test_class_type_filter(self):
        """Should filter sessions by class_type when filter is set."""
        service = TrainingGoalsService()
        goal = {
            "metric": "sessions",
            "target_value": 10,
            "class_type_filter": "gi",
        }
        sessions = [
            {"id": 1, "class_type": "gi"},
            {"id": 2, "class_type": "no-gi"},
            {"id": 3, "class_type": "gi"},
        ]

        service._compute_progress(goal, sessions)

        assert goal["actual_value"] == 2
