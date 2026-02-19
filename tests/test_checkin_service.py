"""Unit tests for CheckinService -- daily check-in operations."""

from datetime import date
from unittest.mock import patch


from rivaflow.core.services.checkin_service import CheckinService


class TestGetUserTimezone:
    """Tests for get_user_timezone."""

    @patch("rivaflow.core.services.checkin_service.ProfileRepository")
    def test_returns_timezone_from_profile(self, MockProfileRepo):
        """Should return timezone string when profile has one."""
        MockProfileRepo.get.return_value = {"timezone": "Australia/Sydney"}

        service = CheckinService()
        result = service.get_user_timezone(user_id=1)

        assert result == "Australia/Sydney"
        MockProfileRepo.get.assert_called_once_with(1)

    @patch("rivaflow.core.services.checkin_service.ProfileRepository")
    def test_returns_none_when_no_profile(self, MockProfileRepo):
        """Should return None when user has no profile."""
        MockProfileRepo.get.return_value = None

        service = CheckinService()
        result = service.get_user_timezone(user_id=99)

        assert result is None

    @patch("rivaflow.core.services.checkin_service.ProfileRepository")
    def test_returns_none_when_no_timezone_set(self, MockProfileRepo):
        """Should return None when profile exists but timezone is not set."""
        MockProfileRepo.get.return_value = {"default_gym": "Alliance"}

        service = CheckinService()
        result = service.get_user_timezone(user_id=1)

        assert result is None


class TestGetDayCheckins:
    """Tests for get_day_checkins."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_checkins_for_date(self, MockRepo):
        """Should return checkins for a specific date."""
        mock_checkins = {
            "morning": {"mood": 4, "energy": 3},
            "evening": {"mood": 5, "energy": 4},
        }
        MockRepo.return_value.get_day_checkins.return_value = mock_checkins

        service = CheckinService()
        result = service.get_day_checkins(user_id=1, check_date=date(2025, 1, 20))

        assert result == mock_checkins
        MockRepo.return_value.get_day_checkins.assert_called_once_with(
            user_id=1, check_date=date(2025, 1, 20)
        )


class TestGetCheckinsRange:
    """Tests for get_checkins_range."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_checkins_in_range(self, MockRepo):
        """Should return checkins within a date range."""
        mock_checkins = [
            {"id": 1, "check_date": "2025-01-18"},
            {"id": 2, "check_date": "2025-01-19"},
        ]
        MockRepo.return_value.get_checkins_range.return_value = mock_checkins

        service = CheckinService()
        result = service.get_checkins_range(
            user_id=1,
            start_date=date(2025, 1, 18),
            end_date=date(2025, 1, 20),
        )

        assert len(result) == 2
        MockRepo.return_value.get_checkins_range.assert_called_once_with(
            user_id=1,
            start_date=date(2025, 1, 18),
            end_date=date(2025, 1, 20),
        )


class TestGetCheckin:
    """Tests for get_checkin."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_checkin_for_slot(self, MockRepo):
        """Should return checkin for a specific slot."""
        mock_checkin = {"id": 1, "mood": 4, "checkin_slot": "morning"}
        MockRepo.return_value.get_checkin.return_value = mock_checkin

        service = CheckinService()
        result = service.get_checkin(user_id=1, check_date=date(2025, 1, 20))

        assert result == mock_checkin
        MockRepo.return_value.get_checkin.assert_called_once_with(
            user_id=1,
            check_date=date(2025, 1, 20),
            checkin_slot="morning",
        )

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_none_when_no_checkin(self, MockRepo):
        """Should return None when no checkin exists for the date/slot."""
        MockRepo.return_value.get_checkin.return_value = None

        service = CheckinService()
        result = service.get_checkin(
            user_id=1,
            check_date=date(2025, 1, 20),
            checkin_slot="evening",
        )

        assert result is None


class TestUpsertCheckin:
    """Tests for upsert_checkin."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_upserts_and_returns_id(self, MockRepo):
        """Should upsert a checkin and return the ID."""
        MockRepo.return_value.upsert_checkin.return_value = 42

        service = CheckinService()
        result = service.upsert_checkin(
            user_id=1,
            check_date=date(2025, 1, 20),
            checkin_slot="morning",
            mood=4,
        )

        assert result == 42
        MockRepo.return_value.upsert_checkin.assert_called_once()


class TestDeleteCheckin:
    """Tests for delete_checkin."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_deletes_existing_checkin(self, MockRepo):
        """Should return True when checkin is deleted."""
        MockRepo.return_value.delete_checkin.return_value = True

        service = CheckinService()
        result = service.delete_checkin(user_id=1, checkin_id=42)

        assert result is True
        MockRepo.return_value.delete_checkin.assert_called_once_with(
            user_id=1, checkin_id=42
        )

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_false_when_not_found(self, MockRepo):
        """Should return False when checkin does not exist."""
        MockRepo.return_value.delete_checkin.return_value = False

        service = CheckinService()
        result = service.delete_checkin(user_id=1, checkin_id=999)

        assert result is False


class TestGetCheckinById:
    """Tests for get_checkin_by_id."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_checkin_by_id(self, MockRepo):
        """Should return checkin when found by ID."""
        mock_checkin = {"id": 10, "mood": 3, "user_id": 1}
        MockRepo.return_value.get_checkin_by_id.return_value = mock_checkin

        service = CheckinService()
        result = service.get_checkin_by_id(user_id=1, checkin_id=10)

        assert result == mock_checkin

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_returns_none_for_wrong_user(self, MockRepo):
        """Should return None when checkin belongs to another user."""
        MockRepo.return_value.get_checkin_by_id.return_value = None

        service = CheckinService()
        result = service.get_checkin_by_id(user_id=2, checkin_id=10)

        assert result is None


class TestUpdateTomorrowIntention:
    """Tests for update_tomorrow_intention."""

    @patch("rivaflow.core.services.checkin_service.CheckinRepository")
    def test_updates_intention(self, MockRepo):
        """Should delegate to repo with correct arguments."""
        service = CheckinService()
        service.update_tomorrow_intention(
            user_id=1,
            check_date=date(2025, 1, 20),
            intention="Train hard",
            checkin_slot="evening",
        )

        MockRepo.return_value.update_tomorrow_intention.assert_called_once_with(
            user_id=1,
            check_date=date(2025, 1, 20),
            intention="Train hard",
            checkin_slot="evening",
        )
