"""Unit tests for MilestoneService — milestone detection and celebration."""

from unittest.mock import patch

from rivaflow.core.services.milestone_service import MilestoneService


class TestCheckAllMilestones:
    """Tests for check_all_milestones."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_new_milestones(
        self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo
    ):
        """Should return list of newly achieved milestones."""
        MockSessionRepo.get_milestone_totals.return_value = {
            "total_sessions": 100,
            "total_rolls": 500,
        }
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 10}

        mock_milestone = {
            "id": 1,
            "milestone_type": "total_sessions",
            "milestone_value": 100,
            "milestone_label": "100 Sessions",
        }
        MockMilestoneRepo.return_value.check_and_create_milestone.side_effect = (
            lambda uid, mt, cv: (mock_milestone if mt == "total_sessions" else None)
        )

        service = MilestoneService()
        result = service.check_all_milestones(user_id=1)

        assert len(result) == 1
        assert result[0]["milestone_type"] == "total_sessions"

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_no_new_milestones(
        self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo
    ):
        """Should return empty list when no new milestones achieved."""
        MockSessionRepo.get_milestone_totals.return_value = {
            "total_sessions": 5,
        }
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 2}
        MockMilestoneRepo.return_value.check_and_create_milestone.return_value = None

        service = MilestoneService()
        result = service.check_all_milestones(user_id=1)

        assert result == []


class TestGetCelebrationDisplay:
    """Tests for get_celebration_display."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_celebration_dict(self, MockMilestoneRepo, MockStreakRepo):
        """Should return celebration display with quote."""
        milestone = {
            "milestone_type": "total_sessions",
            "milestone_value": 100,
            "milestone_label": "100 Sessions",
            "achieved_at": "2025-01-20T10:00:00",
        }

        service = MilestoneService()
        result = service.get_celebration_display(milestone)

        assert result["label"] == "100 Sessions"
        assert result["value"] == 100
        assert result["type"] == "total_sessions"
        assert "quote" in result
        assert "author" in result
        assert result["achieved_at"] == "2025-01-20T10:00:00"


class TestGetProgressToNext:
    """Tests for get_progress_to_next."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_progress_list(
        self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo
    ):
        """Should return progress toward next milestones."""
        MockSessionRepo.get_milestone_totals.return_value = {
            "total_sessions": 80,
        }
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 5}

        MockMilestoneRepo.return_value.get_next_milestone.side_effect = lambda mt, cv: (
            {
                "milestone_value": 100,
                "milestone_label": "100 Sessions",
                "remaining": 20,
                "percentage": 80.0,
            }
            if mt == "total_sessions"
            else {
                "milestone_value": 7,
                "milestone_label": "7-day Streak",
                "remaining": 2,
                "percentage": 71.4,
            }
        )

        service = MilestoneService()
        result = service.get_progress_to_next(user_id=1)

        assert len(result) == 2
        sessions_progress = [p for p in result if p["type"] == "total_sessions"]
        assert len(sessions_progress) == 1
        assert sessions_progress[0]["remaining"] == 20

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_empty_when_no_next_milestones(
        self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo
    ):
        """Should return empty list when all milestones achieved."""
        MockSessionRepo.get_milestone_totals.return_value = {"total_sessions": 9999}
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 9999}
        MockMilestoneRepo.return_value.get_next_milestone.return_value = None

        service = MilestoneService()
        result = service.get_progress_to_next(user_id=1)

        assert result == []


class TestUncelebratedMilestones:
    """Tests for get_uncelebrated_milestones and mark_celebrated."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_get_uncelebrated(self, MockMilestoneRepo, MockStreakRepo):
        """Should return uncelebrated milestones."""
        mock_milestones = [
            {"id": 1, "milestone_label": "50 Sessions"},
            {"id": 2, "milestone_label": "7-day Streak"},
        ]
        MockMilestoneRepo.return_value.get_uncelebrated_milestones.return_value = (
            mock_milestones
        )

        service = MilestoneService()
        result = service.get_uncelebrated_milestones(user_id=1)

        assert len(result) == 2

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_mark_celebrated(self, MockMilestoneRepo, MockStreakRepo):
        """Should delegate mark_celebrated to repo."""
        service = MilestoneService()
        service.mark_celebrated(user_id=1, milestone_id=5)

        MockMilestoneRepo.return_value.mark_celebrated.assert_called_once_with(1, 5)


class TestGetAllAchieved:
    """Tests for get_all_achieved."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_all_achieved(self, MockMilestoneRepo, MockStreakRepo):
        """Should return all achieved milestones."""
        mock_achieved = [
            {"id": 1, "milestone_label": "10 Sessions"},
            {"id": 2, "milestone_label": "50 Sessions"},
        ]
        MockMilestoneRepo.return_value.get_all_achieved.return_value = mock_achieved

        service = MilestoneService()
        result = service.get_all_achieved(user_id=1)

        assert len(result) == 2


class TestGetCurrentTotals:
    """Tests for get_current_totals (public method)."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_includes_streak(self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo):
        """Should include streak from StreakRepository."""
        MockSessionRepo.get_milestone_totals.return_value = {
            "total_sessions": 50,
            "total_rolls": 200,
        }
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 7}

        service = MilestoneService()
        result = service.get_current_totals(user_id=1)

        assert result["total_sessions"] == 50
        assert result["streak"] == 7


class TestGetClosestMilestone:
    """Tests for get_closest_milestone."""

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_closest(self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo):
        """Should return milestone with highest percentage completion."""
        MockSessionRepo.get_milestone_totals.return_value = {
            "total_sessions": 95,
        }
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 3}

        MockMilestoneRepo.return_value.get_next_milestone.side_effect = lambda mt, cv: (
            {
                "milestone_value": 100,
                "milestone_label": "100 Sessions",
                "remaining": 5,
                "percentage": 95.0,
            }
            if mt == "total_sessions"
            else {
                "milestone_value": 7,
                "milestone_label": "7-day Streak",
                "remaining": 4,
                "percentage": 42.9,
            }
        )

        service = MilestoneService()
        result = service.get_closest_milestone(user_id=1)

        assert result is not None
        assert result["percentage"] == 95.0
        assert result["type"] == "total_sessions"

    @patch("rivaflow.core.services.milestone_service.StreakRepository")
    @patch("rivaflow.core.services.milestone_service.SessionRepository")
    @patch("rivaflow.core.services.milestone_service.MilestoneRepository")
    def test_returns_none_when_no_upcoming(
        self, MockMilestoneRepo, MockSessionRepo, MockStreakRepo
    ):
        """Should return None when no upcoming milestones."""
        MockSessionRepo.get_milestone_totals.return_value = {}
        MockStreakRepo.return_value.get_streak.return_value = {"current_streak": 0}
        MockMilestoneRepo.return_value.get_next_milestone.return_value = None

        service = MilestoneService()
        result = service.get_closest_milestone(user_id=1)

        assert result is None
