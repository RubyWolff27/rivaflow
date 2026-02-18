"""Unit tests for StreakService — streak tracking and management."""

from datetime import date
from unittest.mock import patch


from rivaflow.core.services.streak_service import StreakService


def _make_streak(current=0, longest=0, grace_days_used=0, last_checkin=None):
    """Helper to build a streak dict."""
    return {
        "current_streak": current,
        "longest_streak": longest,
        "grace_days_used": grace_days_used,
        "last_checkin_date": last_checkin,
    }


class TestRecordCheckin:
    """Tests for record_checkin."""

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_session_checkin_updates_both_streaks(self, MockRepo):
        """Should update both checkin and training streaks for sessions."""
        old_checkin = _make_streak(current=2, longest=5, grace_days_used=0)
        new_checkin = _make_streak(current=3, longest=5, grace_days_used=0)
        old_training = _make_streak(current=1, longest=3, grace_days_used=0)
        new_training = _make_streak(current=2, longest=3, grace_days_used=0)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.side_effect = [old_checkin, old_training]
        mock_repo.update_streak.side_effect = [new_checkin, new_training]

        service = StreakService()
        result = service.record_checkin(
            user_id=1, checkin_type="session", checkin_date=date(2025, 1, 20)
        )

        assert result["checkin_streak"] == new_checkin
        assert result["training_streak"] == new_training
        assert result["streak_extended"] is True
        assert result["longest_beaten"] is False

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_rest_checkin_only_updates_checkin_streak(self, MockRepo):
        """Should only update checkin streak for rest type."""
        old_checkin = _make_streak(current=2, longest=5, grace_days_used=0)
        new_checkin = _make_streak(current=3, longest=5, grace_days_used=0)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = old_checkin
        mock_repo.update_streak.return_value = new_checkin

        service = StreakService()
        result = service.record_checkin(
            user_id=1, checkin_type="rest", checkin_date=date(2025, 1, 20)
        )

        assert result["checkin_streak"] == new_checkin
        assert result["training_streak"] is None

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_streak_extended_flag(self, MockRepo):
        """Should set streak_extended=True when streak grows."""
        old_checkin = _make_streak(current=3, longest=5, grace_days_used=0)
        new_checkin = _make_streak(current=4, longest=5, grace_days_used=0)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = old_checkin
        mock_repo.update_streak.return_value = new_checkin

        service = StreakService()
        result = service.record_checkin(user_id=1, checkin_type="rest")

        assert result["streak_extended"] is True

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_longest_beaten_flag(self, MockRepo):
        """Should set longest_beaten=True when current exceeds longest."""
        old_checkin = _make_streak(current=5, longest=5, grace_days_used=0)
        new_checkin = _make_streak(current=6, longest=5, grace_days_used=0)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = old_checkin
        mock_repo.update_streak.return_value = new_checkin

        service = StreakService()
        result = service.record_checkin(user_id=1, checkin_type="rest")

        assert result["longest_beaten"] is True

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_grace_day_used_flag(self, MockRepo):
        """Should set grace_day_used=True when grace days increase."""
        old_checkin = _make_streak(current=3, longest=5, grace_days_used=0)
        new_checkin = _make_streak(current=4, longest=5, grace_days_used=1)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = old_checkin
        mock_repo.update_streak.return_value = new_checkin

        service = StreakService()
        result = service.record_checkin(user_id=1, checkin_type="rest")

        assert result["grace_day_used"] is True

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_defaults_to_today(self, MockRepo):
        """Should default checkin_date to today."""
        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = _make_streak()
        mock_repo.update_streak.return_value = _make_streak()

        service = StreakService()
        service.record_checkin(user_id=1, checkin_type="rest")

        mock_repo.update_streak.assert_called_once_with(1, "checkin", date.today())


class TestRecordReadinessCheckin:
    """Tests for record_readiness_checkin."""

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_updates_readiness_streak(self, MockRepo):
        """Should update and return readiness streak info."""
        old_streak = _make_streak(current=2, longest=5, grace_days_used=0)
        new_streak = _make_streak(current=3, longest=5, grace_days_used=0)

        mock_repo = MockRepo.return_value
        mock_repo.get_streak.return_value = old_streak
        mock_repo.update_streak.return_value = new_streak

        service = StreakService()
        result = service.record_readiness_checkin(
            user_id=1, checkin_date=date(2025, 1, 20)
        )

        assert result["readiness_streak"] == new_streak
        assert result["streak_extended"] is True
        assert result["longest_beaten"] is False


class TestGetStreakStatus:
    """Tests for get_streak_status."""

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_returns_all_streak_types(self, MockRepo):
        """Should return all streak types and at_risk flag."""
        mock_repo = MockRepo.return_value
        mock_repo.recalculate_checkin_streak.return_value = _make_streak(current=5)
        mock_repo.get_streak.side_effect = [
            _make_streak(current=3),
            _make_streak(current=2),
        ]
        mock_repo.is_streak_at_risk.return_value = False

        service = StreakService()
        result = service.get_streak_status(user_id=1)

        assert "checkin" in result
        assert "training" in result
        assert "readiness" in result
        assert result["any_at_risk"] is False

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_any_at_risk_true(self, MockRepo):
        """Should set any_at_risk=True when any streak is at risk."""
        mock_repo = MockRepo.return_value
        mock_repo.recalculate_checkin_streak.return_value = _make_streak()
        mock_repo.get_streak.return_value = _make_streak()
        mock_repo.is_streak_at_risk.side_effect = [False, True, False]

        service = StreakService()
        result = service.get_streak_status(user_id=1)

        assert result["any_at_risk"] is True


class TestIsStreakAtRisk:
    """Tests for is_streak_at_risk."""

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_specific_streak_type(self, MockRepo):
        """Should check specific streak type."""
        mock_repo = MockRepo.return_value
        mock_repo.is_streak_at_risk.return_value = True

        service = StreakService()
        assert service.is_streak_at_risk(1, "checkin") is True
        mock_repo.is_streak_at_risk.assert_called_once_with(1, "checkin")

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_all_streaks(self, MockRepo):
        """Should check all streak types when none specified."""
        mock_repo = MockRepo.return_value
        mock_repo.is_streak_at_risk.side_effect = [False, False, True]

        service = StreakService()
        assert service.is_streak_at_risk(1) is True


class TestGetStreak:
    """Tests for get_streak and get_all_streaks."""

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_get_streak_delegates(self, MockRepo):
        """Should delegate to repo."""
        mock_repo = MockRepo.return_value
        mock_streak = _make_streak(current=7)
        mock_repo.get_streak.return_value = mock_streak

        service = StreakService()
        result = service.get_streak(1, "checkin")

        assert result == mock_streak
        mock_repo.get_streak.assert_called_once_with(1, "checkin")

    @patch("rivaflow.core.services.streak_service.StreakRepository")
    def test_get_all_streaks_delegates(self, MockRepo):
        """Should delegate to repo."""
        mock_repo = MockRepo.return_value
        mock_all = [_make_streak(current=7), _make_streak(current=3)]
        mock_repo.get_all_streaks.return_value = mock_all

        service = StreakService()
        result = service.get_all_streaks(1)

        assert result == mock_all
