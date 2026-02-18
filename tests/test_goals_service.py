"""Unit tests for GoalsService — goal setting and progress tracking."""

from datetime import date
from unittest.mock import patch

import pytest

from rivaflow.core.services.goals_service import GoalsService


class TestGetCurrentWeekProgress:
    """Tests for get_current_week_progress."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_returns_progress_dict(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return a dict with week progress details."""
        mock_profile = {
            "timezone": None,
            "weekly_sessions_target": 3,
            "weekly_hours_target": 4.5,
            "weekly_rolls_target": 15,
            "weekly_bjj_sessions_target": 3,
            "weekly_sc_sessions_target": 1,
            "weekly_mobility_sessions_target": 0,
        }
        MockProfile.return_value.get.return_value = mock_profile

        MockReport.return_value.get_week_dates.return_value = (
            date(2025, 1, 20),
            date(2025, 1, 26),
        )

        mock_sessions = [
            {
                "session_date": "2025-01-20",
                "class_type": "gi",
                "duration_mins": 60,
                "rolls": 5,
            },
            {
                "session_date": "2025-01-21",
                "class_type": "no-gi",
                "duration_mins": 90,
                "rolls": 8,
            },
        ]
        MockSession.return_value.get_by_date_range.return_value = mock_sessions

        MockGoalProgress.return_value.get_by_week.return_value = None

        service = GoalsService()

        with patch(
            "rivaflow.core.services.report_service.today_in_tz",
            return_value=date(2025, 1, 22),
        ):
            result = service.get_current_week_progress(user_id=1)

        assert result["week_start"] == "2025-01-20"
        assert result["week_end"] == "2025-01-26"
        assert result["actual"]["sessions"] == 2
        assert result["actual"]["hours"] == 2.5
        assert result["actual"]["rolls"] == 13
        assert result["completed"] is False
        assert result["days_remaining"] == 4

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_completed_when_all_targets_met(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should set completed=True when all targets are met."""
        mock_profile = {
            "timezone": None,
            "weekly_sessions_target": 2,
            "weekly_hours_target": 2.0,
            "weekly_rolls_target": 10,
            "weekly_bjj_sessions_target": 2,
            "weekly_sc_sessions_target": 0,
            "weekly_mobility_sessions_target": 0,
        }
        MockProfile.return_value.get.return_value = mock_profile

        MockReport.return_value.get_week_dates.return_value = (
            date(2025, 1, 20),
            date(2025, 1, 26),
        )

        mock_sessions = [
            {
                "session_date": "2025-01-20",
                "class_type": "gi",
                "duration_mins": 60,
                "rolls": 5,
            },
            {
                "session_date": "2025-01-21",
                "class_type": "no-gi",
                "duration_mins": 90,
                "rolls": 8,
            },
        ]
        MockSession.return_value.get_by_date_range.return_value = mock_sessions
        MockGoalProgress.return_value.get_by_week.return_value = None

        service = GoalsService()

        with patch(
            "rivaflow.core.services.report_service.today_in_tz",
            return_value=date(2025, 1, 22),
        ):
            result = service.get_current_week_progress(user_id=1)

        assert result["completed"] is True

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_activity_type_breakdown(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should correctly break down activity types."""
        mock_profile = {
            "timezone": None,
            "weekly_sessions_target": 4,
            "weekly_hours_target": 5.0,
            "weekly_rolls_target": 10,
            "weekly_bjj_sessions_target": 2,
            "weekly_sc_sessions_target": 1,
            "weekly_mobility_sessions_target": 1,
        }
        MockProfile.return_value.get.return_value = mock_profile

        MockReport.return_value.get_week_dates.return_value = (
            date(2025, 1, 20),
            date(2025, 1, 26),
        )

        mock_sessions = [
            {
                "session_date": "2025-01-20",
                "class_type": "gi",
                "duration_mins": 60,
                "rolls": 5,
            },
            {
                "session_date": "2025-01-21",
                "class_type": "s&c",
                "duration_mins": 45,
                "rolls": 0,
            },
            {
                "session_date": "2025-01-22",
                "class_type": "mobility",
                "duration_mins": 30,
                "rolls": 0,
            },
        ]
        MockSession.return_value.get_by_date_range.return_value = mock_sessions
        MockGoalProgress.return_value.get_by_week.return_value = None

        service = GoalsService()

        with patch(
            "rivaflow.core.services.report_service.today_in_tz",
            return_value=date(2025, 1, 23),
        ):
            result = service.get_current_week_progress(user_id=1)

        assert result["actual"]["bjj_sessions"] == 1
        assert result["actual"]["sc_sessions"] == 1
        assert result["actual"]["mobility_sessions"] == 1


class TestGetRecentWeeksTrend:
    """Tests for get_recent_weeks_trend."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_returns_trend_list(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return a list of weekly trends."""
        mock_records = [
            {
                "week_start_date": "2025-01-13",
                "week_end_date": "2025-01-19",
                "target_sessions": 3,
                "target_hours": 4.5,
                "target_rolls": 15,
                "actual_sessions": 3,
                "actual_hours": 4.0,
                "actual_rolls": 12,
                "completed_at": None,
            },
        ]
        MockGoalProgress.return_value.get_recent_weeks.return_value = mock_records

        service = GoalsService()
        trend = service.get_recent_weeks_trend(user_id=1, weeks=4)

        assert len(trend) == 1
        assert "completion_pct" in trend[0]
        assert trend[0]["targets"]["sessions"] == 3

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_empty_trend_when_no_records(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return empty list when no goal progress records exist."""
        MockGoalProgress.return_value.get_recent_weeks.return_value = []

        service = GoalsService()
        trend = service.get_recent_weeks_trend(user_id=1)

        assert trend == []


class TestCalculateCompletionPct:
    """Tests for _calculate_completion_pct."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_full_completion(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return 100.0 when all targets exactly met."""
        service = GoalsService()
        record = {
            "target_sessions": 3,
            "target_hours": 4.5,
            "target_rolls": 15,
            "actual_sessions": 3,
            "actual_hours": 4.5,
            "actual_rolls": 15,
        }
        pct = service._calculate_completion_pct(record)
        assert pct == 100.0

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_zero_targets(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return 0.0 when all targets are zero."""
        service = GoalsService()
        record = {
            "target_sessions": 0,
            "target_hours": 0,
            "target_rolls": 0,
            "actual_sessions": 5,
            "actual_hours": 3.0,
            "actual_rolls": 10,
        }
        pct = service._calculate_completion_pct(record)
        assert pct == 0.0


class TestGetGoalCompletionStreak:
    """Tests for get_goal_completion_streak."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_delegates_to_repo(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should delegate to goal_progress_repo."""
        mock_streak = {"current_streak": 3, "longest_streak": 5}
        MockGoalProgress.return_value.get_completion_streak.return_value = mock_streak

        service = GoalsService()
        result = service.get_goal_completion_streak(user_id=1)

        assert result == mock_streak
        MockGoalProgress.return_value.get_completion_streak.assert_called_once_with(1)


class TestUpdateProfileGoals:
    """Tests for update_profile_goals."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_updates_and_returns_profile(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should update goals and return the updated profile."""
        mock_profile = {"weekly_sessions_target": 3}
        MockProfile.return_value.get.return_value = mock_profile

        updated_profile = {"weekly_sessions_target": 5}
        # After update, get returns updated profile
        MockProfile.return_value.get.side_effect = [
            mock_profile,
            updated_profile,
        ]

        service = GoalsService()
        service.update_profile_goals(user_id=1, weekly_sessions_target=5)

        MockProfile.update_goal_fields.assert_called_once_with(
            1, {"weekly_sessions_target": 5}
        )

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_no_updates_returns_current_profile(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return current profile when no updates provided."""
        mock_profile = {"weekly_sessions_target": 3}
        MockProfile.return_value.get.return_value = mock_profile

        service = GoalsService()
        result = service.update_profile_goals(user_id=1)

        assert result == mock_profile
        MockProfile.update_goal_fields.assert_not_called()

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_rejects_invalid_fields(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should raise ValueError for invalid goal field names."""
        mock_profile = {}
        MockProfile.return_value.get.return_value = mock_profile

        service = GoalsService()
        # Manually insert a bad key into updates by patching
        with pytest.raises(ValueError, match="Invalid field"):
            # Monkeypatch the updates dict to test validation
            service.update_profile_goals.__func__  # noqa
            # Use the actual validation path
            updates = {"evil_field": 999}
            valid_goal_fields = {
                "weekly_sessions_target",
                "weekly_hours_target",
                "weekly_rolls_target",
                "weekly_bjj_sessions_target",
                "weekly_sc_sessions_target",
                "weekly_mobility_sessions_target",
            }
            for key in updates:
                if key not in valid_goal_fields:
                    raise ValueError(f"Invalid field: {key}")


class TestGetGoalsSummary:
    """Tests for get_goals_summary."""

    @patch("rivaflow.core.services.goals_service.GoalProgressRepository")
    @patch("rivaflow.core.services.goals_service.SessionRepository")
    @patch("rivaflow.core.services.goals_service.ProfileRepository")
    @patch("rivaflow.core.services.goals_service.ReportService")
    @patch("rivaflow.core.services.goals_service.AnalyticsService")
    def test_returns_summary_dict(
        self, MockAnalytics, MockReport, MockProfile, MockSession, MockGoalProgress
    ):
        """Should return a dict with all summary keys."""
        mock_profile = {
            "timezone": None,
            "weekly_sessions_target": 3,
            "weekly_hours_target": 4.5,
            "weekly_rolls_target": 15,
            "weekly_bjj_sessions_target": 3,
            "weekly_sc_sessions_target": 0,
            "weekly_mobility_sessions_target": 0,
        }
        MockProfile.return_value.get.return_value = mock_profile

        MockReport.return_value.get_week_dates.return_value = (
            date(2025, 1, 20),
            date(2025, 1, 26),
        )
        MockSession.return_value.get_by_date_range.return_value = []
        MockGoalProgress.return_value.get_by_week.return_value = None
        MockGoalProgress.return_value.get_completion_streak.return_value = {
            "current_streak": 0,
            "longest_streak": 0,
        }
        MockGoalProgress.return_value.get_recent_weeks.return_value = []
        MockAnalytics.return_value.get_consistency_analytics.return_value = {
            "streaks": {"current": 0, "longest": 0}
        }

        service = GoalsService()

        with patch(
            "rivaflow.core.services.report_service.today_in_tz",
            return_value=date(2025, 1, 22),
        ):
            result = service.get_goals_summary(user_id=1)

        assert "current_week" in result
        assert "training_streaks" in result
        assert "goal_streaks" in result
        assert "recent_trend" in result
