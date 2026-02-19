"""Unit tests for performance_scoring — core calculations and partner analytics."""

from datetime import date
from unittest.mock import MagicMock


from rivaflow.core.services.performance_scoring import (
    calculate_daily_timeseries,
    calculate_performance_by_belt,
    calculate_period_summary,
    compute_head_to_head,
    get_session_date,
)


class TestCalculatePeriodSummary:
    """Tests for calculate_period_summary."""

    def test_empty_sessions(self):
        """Should return zeros for empty session list."""
        result = calculate_period_summary([])

        assert result["total_sessions"] == 0
        assert result["total_submissions_for"] == 0
        assert result["total_rolls"] == 0
        assert result["avg_intensity"] == 0.0

    def test_single_session(self):
        """Should correctly summarize a single session."""
        sessions = [
            {
                "submissions_for": 3,
                "submissions_against": 1,
                "rolls": 5,
                "intensity": 8,
            }
        ]

        result = calculate_period_summary(sessions)

        assert result["total_sessions"] == 1
        assert result["total_submissions_for"] == 3
        assert result["total_submissions_against"] == 1
        assert result["total_rolls"] == 5
        assert result["avg_intensity"] == 8.0

    def test_multiple_sessions(self):
        """Should aggregate multiple sessions correctly."""
        sessions = [
            {
                "submissions_for": 2,
                "submissions_against": 1,
                "rolls": 4,
                "intensity": 6,
            },
            {
                "submissions_for": 3,
                "submissions_against": 2,
                "rolls": 6,
                "intensity": 8,
            },
        ]

        result = calculate_period_summary(sessions)

        assert result["total_sessions"] == 2
        assert result["total_submissions_for"] == 5
        assert result["total_submissions_against"] == 3
        assert result["total_rolls"] == 10
        assert result["avg_intensity"] == 7.0

    def test_handles_none_values(self):
        """Should treat None values as 0."""
        sessions = [
            {
                "submissions_for": None,
                "submissions_against": None,
                "rolls": None,
                "intensity": None,
            }
        ]

        result = calculate_period_summary(sessions)

        assert result["total_submissions_for"] == 0
        assert result["total_rolls"] == 0
        assert result["avg_intensity"] == 0.0

    def test_handles_missing_keys(self):
        """Should use 0 defaults for missing keys."""
        sessions = [{}]

        result = calculate_period_summary(sessions)

        assert result["total_sessions"] == 1
        assert result["total_submissions_for"] == 0


class TestCalculateDailyTimeseries:
    """Tests for calculate_daily_timeseries."""

    def test_basic_timeseries(self):
        """Should produce daily arrays for the date range."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 3)
        sessions = [
            {
                "session_date": date(2025, 1, 1),
                "intensity": 7,
                "rolls": 5,
                "submissions_for": 2,
            },
            {
                "session_date": date(2025, 1, 3),
                "intensity": 9,
                "rolls": 8,
                "submissions_for": 3,
            },
        ]

        result = calculate_daily_timeseries(sessions, start, end)

        assert len(result["sessions"]) == 3
        assert result["sessions"][0] == 1  # Jan 1
        assert result["sessions"][1] == 0  # Jan 2 (no session)
        assert result["sessions"][2] == 1  # Jan 3

    def test_empty_sessions(self):
        """Should return zeros for all days when no sessions."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 2)

        result = calculate_daily_timeseries([], start, end)

        assert result["sessions"] == [0, 0]
        assert result["intensity"] == [0, 0]

    def test_multiple_sessions_same_day(self):
        """Should aggregate multiple sessions on the same day."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 1)
        sessions = [
            {
                "session_date": date(2025, 1, 1),
                "intensity": 6,
                "rolls": 3,
                "submissions_for": 1,
            },
            {
                "session_date": date(2025, 1, 1),
                "intensity": 8,
                "rolls": 5,
                "submissions_for": 2,
            },
        ]

        result = calculate_daily_timeseries(sessions, start, end)

        assert result["sessions"] == [2]
        assert result["rolls"] == [8]  # 3 + 5
        assert result["intensity"] == [7.0]  # avg of 6 and 8


class TestCalculatePerformanceByBelt:
    """Tests for calculate_performance_by_belt."""

    def test_no_gradings(self):
        """Should return 'unranked' stats when no gradings."""
        sessions = [
            {"submissions_for": 2, "submissions_against": 1},
            {"submissions_for": 3, "submissions_against": 0},
        ]

        result = calculate_performance_by_belt(sessions, [])

        assert len(result) == 1
        assert result[0]["belt"] == "unranked"
        assert result[0]["sessions"] == 2
        assert result[0]["subs_for"] == 5

    def test_single_grading(self):
        """Should calculate stats from grading date to today."""
        sessions = [
            {
                "session_date": date(2025, 1, 15),
                "submissions_for": 2,
                "submissions_against": 1,
            },
        ]
        gradings = [{"grade": "blue", "date_graded": "2025-01-01"}]

        result = calculate_performance_by_belt(sessions, gradings)

        assert len(result) == 1
        assert result[0]["belt"] == "blue"
        assert result[0]["sessions"] == 1

    def test_multiple_gradings(self):
        """Should split sessions across belt periods."""
        sessions = [
            {
                "session_date": date(2024, 6, 15),
                "submissions_for": 1,
                "submissions_against": 0,
            },
            {
                "session_date": date(2025, 2, 15),
                "submissions_for": 3,
                "submissions_against": 1,
            },
        ]
        gradings = [
            {"grade": "white", "date_graded": "2024-01-01"},
            {"grade": "blue", "date_graded": "2025-01-01"},
        ]

        result = calculate_performance_by_belt(sessions, gradings)

        assert len(result) == 2
        assert result[0]["belt"] == "white"
        assert result[0]["sessions"] == 1
        assert result[1]["belt"] == "blue"
        assert result[1]["sessions"] == 1


class TestGetSessionDate:
    """Tests for get_session_date helper."""

    def test_returns_session_date_when_found(self):
        """Should return the session's date."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = {"session_date": date(2025, 1, 15)}

        result = get_session_date(mock_repo, user_id=1, session_id=10)

        assert result == date(2025, 1, 15)

    def test_returns_today_when_not_found(self):
        """Should return today when session not found."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None

        result = get_session_date(mock_repo, user_id=1, session_id=999)

        assert result == date.today()


class TestComputeHeadToHead:
    """Tests for compute_head_to_head."""

    def test_returns_comparison(self):
        """Should return stats for both partners."""
        mock_roll_repo = MagicMock()
        mock_friend_repo = MagicMock()

        mock_friend_repo.get_by_id.side_effect = [
            {"name": "Alice", "belt_rank": "blue"},
            {"name": "Bob", "belt_rank": "purple"},
        ]
        mock_roll_repo.get_partner_stats.side_effect = [
            {"total_rolls": 10, "total_submissions_for": 5},
            {"total_rolls": 8, "total_submissions_for": 3},
        ]

        result = compute_head_to_head(
            mock_roll_repo, mock_friend_repo, user_id=1, partner1_id=2, partner2_id=3
        )

        assert result["partner1"]["name"] == "Alice"
        assert result["partner2"]["name"] == "Bob"
        assert result["partner1"]["total_rolls"] == 10

    def test_returns_empty_when_partner_not_found(self):
        """Should return empty dict when a partner is missing."""
        mock_roll_repo = MagicMock()
        mock_friend_repo = MagicMock()

        mock_friend_repo.get_by_id.side_effect = [
            {"name": "Alice", "belt_rank": "blue"},
            None,
        ]

        result = compute_head_to_head(
            mock_roll_repo, mock_friend_repo, user_id=1, partner1_id=2, partner2_id=999
        )

        assert result == {}
