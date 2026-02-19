"""Unit tests for RestService -- rest day logging."""

import json
from datetime import date, timedelta
from unittest.mock import patch

from rivaflow.core.services.rest_service import RestService


class TestLogRestDay:
    """Tests for log_rest_day."""

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_logs_rest_day_with_all_fields(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should log rest day and return complete result dict."""
        MockInsight.return_value.generate_insight.return_value = {
            "message": "Take it easy"
        }
        MockCheckinRepo.return_value.upsert_checkin.return_value = 42
        MockStreak.return_value.record_checkin.return_value = {"checkin_streak": 5}
        MockMilestone.return_value.check_all_milestones.return_value = []

        service = RestService()
        result = service.log_rest_day(
            user_id=1,
            rest_type="recovery",
            note="Feeling sore",
            tomorrow_intention="Train hard",
            rest_date=date(2025, 1, 20),
        )

        assert result["checkin_id"] == 42
        assert result["check_date"] == "2025-01-20"
        assert result["rest_type"] == "recovery"
        assert result["rest_note"] == "Feeling sore"
        assert result["tomorrow_intention"] == "Train hard"
        assert result["streak_info"]["checkin_streak"] == 5
        assert result["insight"]["message"] == "Take it easy"
        assert result["milestones"] == []

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_defaults_to_today(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should default rest_date to today when not provided."""
        MockInsight.return_value.generate_insight.return_value = {}
        MockCheckinRepo.return_value.upsert_checkin.return_value = 1
        MockStreak.return_value.record_checkin.return_value = {}
        MockMilestone.return_value.check_all_milestones.return_value = []

        service = RestService()
        result = service.log_rest_day(user_id=1)

        assert result["check_date"] == date.today().isoformat()

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_upsert_receives_correct_args(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should pass correct arguments to checkin upsert."""
        insight = {"tip": "hydrate"}
        MockInsight.return_value.generate_insight.return_value = insight
        MockCheckinRepo.return_value.upsert_checkin.return_value = 10
        MockStreak.return_value.record_checkin.return_value = {}
        MockMilestone.return_value.check_all_milestones.return_value = []

        service = RestService()
        service.log_rest_day(
            user_id=1,
            rest_type="injury",
            note="Knee pain",
            rest_date=date(2025, 2, 1),
        )

        MockCheckinRepo.return_value.upsert_checkin.assert_called_once_with(
            user_id=1,
            check_date=date(2025, 2, 1),
            checkin_type="rest",
            rest_type="injury",
            rest_note="Knee pain",
            tomorrow_intention=None,
            insight_shown=json.dumps(insight),
        )

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_records_checkin_streak(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should call streak_service.record_checkin with rest type."""
        MockInsight.return_value.generate_insight.return_value = {}
        MockCheckinRepo.return_value.upsert_checkin.return_value = 1
        MockStreak.return_value.record_checkin.return_value = {"streak": 3}
        MockMilestone.return_value.check_all_milestones.return_value = []

        service = RestService()
        rest_date = date(2025, 1, 20)
        service.log_rest_day(user_id=1, rest_date=rest_date)

        MockStreak.return_value.record_checkin.assert_called_once_with(
            1, "rest", rest_date
        )

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_checks_milestones(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should check milestones after logging rest day."""
        MockInsight.return_value.generate_insight.return_value = {}
        MockCheckinRepo.return_value.upsert_checkin.return_value = 1
        MockStreak.return_value.record_checkin.return_value = {}
        MockMilestone.return_value.check_all_milestones.return_value = [
            {"type": "rest_warrior", "label": "Rest Warrior"}
        ]

        service = RestService()
        result = service.log_rest_day(user_id=1)

        assert len(result["milestones"]) == 1
        assert result["milestones"][0]["type"] == "rest_warrior"


class TestGetRecentRestDays:
    """Tests for get_recent_rest_days."""

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_filters_rest_checkins_only(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should only return checkins with type 'rest'."""
        MockCheckinRepo.return_value.get_checkins_range.return_value = [
            {"id": 1, "checkin_type": "rest", "rest_type": "recovery"},
            {"id": 2, "checkin_type": "training"},
            {"id": 3, "checkin_type": "rest", "rest_type": "life"},
        ]

        service = RestService()
        result = service.get_recent_rest_days(user_id=1, days=30)

        assert len(result) == 2
        assert all(r["checkin_type"] == "rest" for r in result)

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_returns_empty_when_no_rest_days(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should return empty list when no rest days exist."""
        MockCheckinRepo.return_value.get_checkins_range.return_value = [
            {"id": 1, "checkin_type": "training"},
        ]

        service = RestService()
        result = service.get_recent_rest_days(user_id=1)

        assert result == []

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_uses_correct_date_range(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should query the correct date range based on days param."""
        MockCheckinRepo.return_value.get_checkins_range.return_value = []

        service = RestService()
        service.get_recent_rest_days(user_id=1, days=7)

        call_args = MockCheckinRepo.return_value.get_checkins_range.call_args
        start_date = call_args[0][1]
        end_date = call_args[0][2]

        assert end_date == date.today()
        assert start_date == date.today() - timedelta(days=7)


class TestGetRestDayCount:
    """Tests for get_rest_day_count."""

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_counts_rest_days(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should return the count of rest days."""
        MockCheckinRepo.return_value.get_checkins_range.return_value = [
            {"id": 1, "checkin_type": "rest"},
            {"id": 2, "checkin_type": "rest"},
            {"id": 3, "checkin_type": "training"},
        ]

        service = RestService()
        result = service.get_rest_day_count(user_id=1, days=7)

        assert result == 2

    @patch("rivaflow.core.services.rest_service.InsightService")
    @patch("rivaflow.core.services.rest_service.MilestoneService")
    @patch("rivaflow.core.services.rest_service.StreakService")
    @patch("rivaflow.core.services.rest_service.CheckinRepository")
    def test_returns_zero_when_no_rest(
        self, MockCheckinRepo, MockStreak, MockMilestone, MockInsight
    ):
        """Should return 0 when there are no rest days."""
        MockCheckinRepo.return_value.get_checkins_range.return_value = []

        service = RestService()
        result = service.get_rest_day_count(user_id=1)

        assert result == 0
