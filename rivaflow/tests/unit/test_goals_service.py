"""Unit tests for GoalsService."""
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from rivaflow.core.services.goals_service import GoalsService


class TestCurrentWeekProgress:
    """Test current week goal progress calculation."""

    @patch('rivaflow.core.services.goals_service.ProfileRepository')
    @patch('rivaflow.core.services.goals_service.SessionRepository')
    @patch('rivaflow.core.services.goals_service.GoalProgressRepository')
    @patch('rivaflow.core.services.goals_service.ReportService')
    def test_calculates_progress_correctly(self, mock_report_service, mock_goal_repo, mock_session_repo, mock_profile_repo):
        """Test that progress percentages are calculated correctly."""
        # Setup
        service = GoalsService()

        # Mock week dates
        today = date(2026, 1, 22)  # Wednesday
        week_start = date(2026, 1, 19)  # Monday
        week_end = date(2026, 1, 25)  # Sunday
        service.report_service.get_week_dates = Mock(return_value=(week_start, week_end))

        # Mock profile with targets
        service.profile_repo.get = Mock(return_value={
            "weekly_sessions_target": 4,
            "weekly_hours_target": 6.0,
            "weekly_rolls_target": 20,
        })

        # Mock sessions (2 sessions, 3 hours, 10 rolls)
        sessions = [
            {"duration_mins": 90, "rolls": 5},
            {"duration_mins": 90, "rolls": 5},
        ]
        service.session_repo.get_by_date_range = Mock(return_value=sessions)

        # Mock goal progress repo
        service.goal_progress_repo.get_by_week = Mock(return_value=None)
        service.goal_progress_repo.create = Mock(return_value=1)

        with patch('rivaflow.core.services.goals_service.date') as mock_date:
            mock_date.today.return_value = today

            # Execute
            progress = service.get_current_week_progress(user_id=1)

        # Verify calculations
        assert progress["actual"]["sessions"] == 2
        assert progress["actual"]["hours"] == 3.0
        assert progress["actual"]["rolls"] == 10

        assert progress["targets"]["sessions"] == 4
        assert progress["targets"]["hours"] == 6.0
        assert progress["targets"]["rolls"] == 20

        # 2/4 = 50%, 3/6 = 50%, 10/20 = 50%
        assert progress["progress"]["sessions_pct"] == 50.0
        assert progress["progress"]["hours_pct"] == 50.0
        assert progress["progress"]["rolls_pct"] == 50.0
        assert progress["progress"]["overall_pct"] == 50.0

        assert progress["completed"] is False
        assert progress["days_remaining"] == 3  # Wed to Sun

    @patch('rivaflow.core.services.goals_service.ProfileRepository')
    @patch('rivaflow.core.services.goals_service.SessionRepository')
    @patch('rivaflow.core.services.goals_service.GoalProgressRepository')
    @patch('rivaflow.core.services.goals_service.ReportService')
    def test_detects_goal_completion(self, mock_report_service, mock_goal_repo, mock_session_repo, mock_profile_repo):
        """Test that completed goals are properly detected."""
        service = GoalsService()

        week_start = date(2026, 1, 19)
        week_end = date(2026, 1, 25)
        service.report_service.get_week_dates = Mock(return_value=(week_start, week_end))

        service.profile_repo.get = Mock(return_value={
            "weekly_sessions_target": 3,
            "weekly_hours_target": 4.5,
            "weekly_rolls_target": 15,
        })

        # Sessions that meet all targets
        sessions = [
            {"duration_mins": 90, "rolls": 5},
            {"duration_mins": 90, "rolls": 5},
            {"duration_mins": 90, "rolls": 5},
        ]
        service.session_repo.get_by_date_range = Mock(return_value=sessions)

        service.goal_progress_repo.get_by_week = Mock(return_value=None)
        service.goal_progress_repo.create = Mock(return_value=1)

        with patch('rivaflow.core.services.goals_service.date') as mock_date:
            mock_date.today.return_value = date(2026, 1, 22)
            progress = service.get_current_week_progress(user_id=1)

        assert progress["completed"] is True
        assert progress["actual"]["sessions"] == 3
        assert progress["actual"]["hours"] == 4.5
        assert progress["actual"]["rolls"] == 15


class TestStreakCalculations:
    """Test streak tracking functionality."""

    @patch('rivaflow.core.services.goals_service.AnalyticsService')
    def test_retrieves_training_streaks_from_analytics(self, mock_analytics_service):
        """Test that training streaks are retrieved from AnalyticsService."""
        service = GoalsService()

        # Mock analytics response
        service.analytics_service.get_consistency_analytics = Mock(return_value={
            "streaks": {
                "current": 7,
                "longest": 14,
            }
        })

        with patch('rivaflow.core.services.goals_service.date') as mock_date:
            mock_date.today.return_value = date(2026, 1, 22)

            streaks = service.get_training_streaks(user_id=1)

        assert streaks["current_streak"] == 7
        assert streaks["longest_streak"] == 14
        assert streaks["last_updated"] == "2026-01-22"

    @patch('rivaflow.core.services.goals_service.GoalProgressRepository')
    def test_calculates_goal_completion_streaks(self, mock_goal_repo):
        """Test calculation of consecutive weeks hitting all goals."""
        service = GoalsService()

        service.goal_progress_repo.get_completion_streak = Mock(return_value={
            "current_streak": 3,
            "longest_streak": 5,
        })

        streaks = service.get_goal_completion_streak(user_id=1)

        assert streaks["current_streak"] == 3
        assert streaks["longest_streak"] == 5


class TestGoalsUpdate:
    """Test goal target updates."""

    @patch('rivaflow.core.services.goals_service.ProfileRepository')
    @patch('rivaflow.db.database.get_connection')
    def test_updates_profile_goals(self, mock_get_connection, mock_profile_repo):
        """Test updating weekly goal targets in profile."""
        service = GoalsService()

        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_get_connection.return_value = mock_conn

        # Mock profile get to return updated values
        service.profile_repo.get = Mock(side_effect=[
            # First call (existing)
            {
                "weekly_sessions_target": 3,
                "weekly_hours_target": 4.5,
                "weekly_rolls_target": 15,
            },
            # Second call (after update)
            {
                "weekly_sessions_target": 5,
                "weekly_hours_target": 7.5,
                "weekly_rolls_target": 25,
            }
        ])

        updated = service.update_profile_goals(
            user_id=1,
            weekly_sessions_target=5,
            weekly_hours_target=7.5,
            weekly_rolls_target=25,
        )

        # Verify database update was called
        mock_cursor.execute.assert_called_once()

        # Verify updated values returned
        assert updated["weekly_sessions_target"] == 5
        assert updated["weekly_hours_target"] == 7.5
        assert updated["weekly_rolls_target"] == 25


class TestGoalsTrend:
    """Test goal completion trend calculation."""

    @patch('rivaflow.core.services.goals_service.GoalProgressRepository')
    def test_calculates_completion_percentage(self, mock_goal_repo):
        """Test that completion percentage is calculated correctly for trends."""
        service = GoalsService()

        # Mock goal progress records
        mock_goal_repo_instance = Mock()
        service.goal_progress_repo = mock_goal_repo_instance

        mock_goal_repo_instance.get_recent_weeks.return_value = [
            {
                "week_start_date": "2026-01-12",
                "week_end_date": "2026-01-18",
                "target_sessions": 4,
                "actual_sessions": 4,
                "target_hours": 6.0,
                "actual_hours": 6.0,
                "target_rolls": 20,
                "actual_rolls": 20,
                "completed_at": "2026-01-18 23:00:00",
            },
            {
                "week_start_date": "2026-01-05",
                "week_end_date": "2026-01-11",
                "target_sessions": 4,
                "actual_sessions": 2,
                "target_hours": 6.0,
                "actual_hours": 3.0,
                "target_rolls": 20,
                "actual_rolls": 10,
                "completed_at": None,
            },
        ]

        trend = service.get_recent_weeks_trend(user_id=1, weeks=2)

        assert len(trend) == 2

        # Week 1: 100% all targets met
        assert trend[0]["completion_pct"] == 100.0
        assert trend[0]["completed"] is True

        # Week 2: 50% average (50% sessions, 50% hours, 50% rolls)
        assert trend[1]["completion_pct"] == 50.0
        assert trend[1]["completed"] is False


class TestGoalsSummary:
    """Test comprehensive goals summary."""

    @patch('rivaflow.core.services.goals_service.GoalsService.get_current_week_progress')
    @patch('rivaflow.core.services.goals_service.GoalsService.get_training_streaks')
    @patch('rivaflow.core.services.goals_service.GoalsService.get_goal_completion_streak')
    @patch('rivaflow.core.services.goals_service.GoalsService.get_recent_weeks_trend')
    def test_returns_complete_summary(self, mock_trend, mock_goal_streaks, mock_training_streaks, mock_current):
        """Test that summary combines all goal data."""
        service = GoalsService()

        mock_current.return_value = {"week_start": "2026-01-19"}
        mock_training_streaks.return_value = {"current_streak": 5}
        mock_goal_streaks.return_value = {"current_streak": 2}
        mock_trend.return_value = [{"week_start": "2026-01-12"}]

        summary = service.get_goals_summary(user_id=1)

        assert "current_week" in summary
        assert "training_streaks" in summary
        assert "goal_streaks" in summary
        assert "recent_trend" in summary

        assert summary["current_week"]["week_start"] == "2026-01-19"
        assert summary["training_streaks"]["current_streak"] == 5
        assert summary["goal_streaks"]["current_streak"] == 2
        assert len(summary["recent_trend"]) == 1
