"""Unit tests for StreakAnalyticsService — consistency, streaks, milestones."""

from datetime import date, timedelta
from unittest.mock import patch

from rivaflow.core.services.streak_analytics import StreakAnalyticsService


def _make_session(
    session_date,
    duration_mins=60,
    rolls=5,
    intensity=7,
    class_type="gi",
    gym_name="Alliance",
    submissions_for=2,
    submissions_against=1,
):
    """Helper to create a session dict with required fields."""
    return {
        "id": hash(str(session_date)) % 10000,
        "session_date": session_date,
        "duration_mins": duration_mins,
        "rolls": rolls,
        "intensity": intensity,
        "class_type": class_type,
        "gym_name": gym_name,
        "submissions_for": submissions_for,
        "submissions_against": submissions_against,
    }


class TestCalculateStreaks:
    """Tests for _calculate_streaks (private but critical logic)."""

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_empty_sessions_returns_zeros(self, MockGrading, MockSession):
        """Should return (0, 0) for no sessions."""
        service = StreakAnalyticsService()
        current, longest = service._calculate_streaks([])

        assert current == 0
        assert longest == 0

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_single_session_today(self, MockGrading, MockSession):
        """Should return streak of 1 for a session today."""
        today = date.today()
        sessions = [_make_session(today)]

        service = StreakAnalyticsService()
        current, longest = service._calculate_streaks(sessions)

        assert current == 1
        assert longest == 1

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_consecutive_days_streak(self, MockGrading, MockSession):
        """Should correctly count consecutive day streaks."""
        today = date.today()
        sessions = [
            _make_session(today),
            _make_session(today - timedelta(days=1)),
            _make_session(today - timedelta(days=2)),
        ]

        service = StreakAnalyticsService()
        current, longest = service._calculate_streaks(sessions)

        assert current == 3
        assert longest == 3

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_broken_streak(self, MockGrading, MockSession):
        """Should detect a broken streak (gap in dates)."""
        today = date.today()
        sessions = [
            _make_session(today),
            _make_session(today - timedelta(days=1)),
            # gap on day -2
            _make_session(today - timedelta(days=3)),
            _make_session(today - timedelta(days=4)),
            _make_session(today - timedelta(days=5)),
        ]

        service = StreakAnalyticsService()
        current, longest = service._calculate_streaks(sessions)

        assert current == 2
        assert longest == 3

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_no_current_streak_when_gap_from_today(self, MockGrading, MockSession):
        """Should return 0 current streak when last session was >1 day ago."""
        today = date.today()
        sessions = [
            _make_session(today - timedelta(days=5)),
            _make_session(today - timedelta(days=6)),
        ]

        service = StreakAnalyticsService()
        current, longest = service._calculate_streaks(sessions)

        assert current == 0
        assert longest == 2


class TestGetConsistencyAnalytics:
    """Tests for get_consistency_analytics."""

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_returns_expected_keys(self, MockGrading, MockSession):
        """Should return dict with all expected top-level keys."""
        MockSession.return_value.get_by_date_range.return_value = []
        MockSession.return_value.get_recent.return_value = []

        service = StreakAnalyticsService()
        result = service.get_consistency_analytics(user_id=1)

        assert "weekly_volume" in result
        assert "class_type_distribution" in result
        assert "gym_breakdown" in result
        assert "streaks" in result

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_weekly_volume_aggregation(self, MockGrading, MockSession):
        """Should group sessions by week."""
        today = date.today()
        sessions = [
            _make_session(today, duration_mins=60, rolls=5),
            _make_session(today - timedelta(days=1), duration_mins=90, rolls=8),
        ]
        MockSession.return_value.get_by_date_range.return_value = sessions
        MockSession.return_value.get_recent.return_value = sessions

        service = StreakAnalyticsService()
        result = service.get_consistency_analytics(user_id=1)

        total_sessions = sum(w["sessions"] for w in result["weekly_volume"])
        assert total_sessions == 2

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_class_type_distribution(self, MockGrading, MockSession):
        """Should count sessions by class type."""
        today = date.today()
        sessions = [
            _make_session(today, class_type="gi"),
            _make_session(today - timedelta(days=1), class_type="no-gi"),
            _make_session(today - timedelta(days=2), class_type="gi"),
        ]
        MockSession.return_value.get_by_date_range.return_value = sessions
        MockSession.return_value.get_recent.return_value = sessions

        service = StreakAnalyticsService()
        result = service.get_consistency_analytics(user_id=1)

        dist = {d["class_type"]: d["count"] for d in result["class_type_distribution"]}
        assert dist["gi"] == 2
        assert dist["no-gi"] == 1

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_gym_breakdown(self, MockGrading, MockSession):
        """Should count sessions by gym name."""
        today = date.today()
        sessions = [
            _make_session(today, gym_name="Alliance"),
            _make_session(today - timedelta(days=1), gym_name="Gracie Barra"),
            _make_session(today - timedelta(days=2), gym_name="Alliance"),
        ]
        MockSession.return_value.get_by_date_range.return_value = sessions
        MockSession.return_value.get_recent.return_value = sessions

        service = StreakAnalyticsService()
        result = service.get_consistency_analytics(user_id=1)

        gym_map = {g["gym"]: g["sessions"] for g in result["gym_breakdown"]}
        assert gym_map["Alliance"] == 2
        assert gym_map["Gracie Barra"] == 1


class TestGetTrainingFrequencyHeatmap:
    """Tests for get_training_frequency_heatmap."""

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_empty_calendar(self, MockGrading, MockSession):
        """Should return calendar with all zero counts when no sessions."""
        MockSession.return_value.get_by_date_range.return_value = []

        service = StreakAnalyticsService()
        result = service.get_training_frequency_heatmap(
            user_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
        )

        assert len(result["calendar"]) == 3
        assert result["total_active_days"] == 0
        assert result["activity_rate"] == 0

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_heatmap_with_sessions(self, MockGrading, MockSession):
        """Should populate calendar with session data."""
        sessions = [
            _make_session(date(2025, 1, 1), intensity=7),
            _make_session(date(2025, 1, 3), intensity=9),
        ]
        MockSession.return_value.get_by_date_range.return_value = sessions

        service = StreakAnalyticsService()
        result = service.get_training_frequency_heatmap(
            user_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
        )

        assert result["total_active_days"] == 2
        assert result["total_days"] == 3
        # activity_rate = 2/3 * 100 = 66.7
        assert result["activity_rate"] == 66.7


class TestGetMilestones:
    """Tests for get_milestones."""

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_milestones_with_no_sessions(self, MockGrading, MockSession):
        """Should handle empty session list gracefully."""
        MockSession.return_value.get_recent.return_value = []
        MockGrading.return_value.list_all.return_value = []

        service = StreakAnalyticsService()
        result = service.get_milestones(user_id=1)

        assert result["belt_progression"] == []
        assert result["personal_records"]["most_rolls_session"] == 0
        assert result["rolling_totals"]["lifetime"]["sessions"] == 0

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_milestones_personal_records(self, MockGrading, MockSession):
        """Should calculate personal records from sessions."""
        sessions = [
            _make_session(
                date(2025, 1, 1),
                rolls=12,
                duration_mins=120,
                submissions_for=5,
                submissions_against=2,
            ),
            _make_session(
                date(2025, 1, 2),
                rolls=8,
                duration_mins=60,
                submissions_for=3,
                submissions_against=1,
            ),
        ]
        MockSession.return_value.get_recent.return_value = sessions
        MockGrading.return_value.list_all.return_value = []

        service = StreakAnalyticsService()
        result = service.get_milestones(user_id=1)

        assert result["personal_records"]["most_rolls_session"] == 12
        assert result["personal_records"]["longest_session"] == 120

    @patch("rivaflow.core.services.streak_analytics.SessionRepository")
    @patch("rivaflow.core.services.streak_analytics.GradingRepository")
    def test_milestones_rolling_totals(self, MockGrading, MockSession):
        """Should calculate lifetime totals correctly."""
        sessions = [
            _make_session(
                date(2025, 1, 1),
                duration_mins=60,
                rolls=5,
                submissions_for=2,
            ),
            _make_session(
                date(2025, 1, 2),
                duration_mins=90,
                rolls=8,
                submissions_for=3,
            ),
        ]
        MockSession.return_value.get_recent.return_value = sessions
        MockGrading.return_value.list_all.return_value = []

        service = StreakAnalyticsService()
        result = service.get_milestones(user_id=1)

        lifetime = result["rolling_totals"]["lifetime"]
        assert lifetime["sessions"] == 2
        assert lifetime["hours"] == 2.5  # (60+90)/60
        assert lifetime["rolls"] == 13
        assert lifetime["submissions"] == 5
