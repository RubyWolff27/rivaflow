"""Unit tests for WaitlistService — waitlist management CRUD."""

from unittest.mock import patch

from rivaflow.core.services.waitlist_service import WaitlistService


class TestCreate:
    """Tests for WaitlistService.create."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_creates_entry_and_returns_dict(self, MockRepo):
        """Should create waitlist entry and return it."""
        expected = {"id": 1, "email": "user@test.com", "status": "waiting"}
        MockRepo.return_value.create.return_value = expected

        service = WaitlistService()
        result = service.create(email="user@test.com", name="Test User")

        assert result == expected
        MockRepo.return_value.create.assert_called_once_with(
            email="user@test.com", name="Test User"
        )

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_passes_all_kwargs(self, MockRepo):
        """Should forward all keyword arguments to the repository."""
        MockRepo.return_value.create.return_value = {"id": 2}

        service = WaitlistService()
        service.create(email="a@b.com", name="A", referral_source="friend")

        call_kwargs = MockRepo.return_value.create.call_args[1]
        assert call_kwargs["referral_source"] == "friend"


class TestGetById:
    """Tests for WaitlistService.get_by_id."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_returns_entry_when_found(self, MockRepo):
        """Should return waitlist entry by ID."""
        entry = {"id": 1, "email": "a@b.com", "status": "waiting"}
        MockRepo.return_value.get_by_id.return_value = entry

        service = WaitlistService()
        result = service.get_by_id(waitlist_id=1)

        assert result == entry

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when ID does not exist."""
        MockRepo.return_value.get_by_id.return_value = None

        service = WaitlistService()
        result = service.get_by_id(waitlist_id=999)

        assert result is None


class TestGetByEmail:
    """Tests for WaitlistService.get_by_email."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_returns_entry_by_email(self, MockRepo):
        """Should return waitlist entry matching email."""
        entry = {"id": 1, "email": "user@test.com"}
        MockRepo.return_value.get_by_email.return_value = entry

        service = WaitlistService()
        result = service.get_by_email(email="user@test.com")

        assert result["email"] == "user@test.com"

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_returns_none_for_unknown_email(self, MockRepo):
        """Should return None when email not on waitlist."""
        MockRepo.return_value.get_by_email.return_value = None

        service = WaitlistService()
        result = service.get_by_email(email="unknown@test.com")

        assert result is None


class TestCounts:
    """Tests for get_waiting_count and get_count."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_get_waiting_count(self, MockRepo):
        """Should return count of waiting entries."""
        MockRepo.return_value.get_waiting_count.return_value = 42

        service = WaitlistService()
        assert service.get_waiting_count() == 42

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_get_count_with_status_filter(self, MockRepo):
        """Should pass status filter to repo."""
        MockRepo.return_value.get_count.return_value = 10

        service = WaitlistService()
        result = service.get_count(status="invited")

        assert result == 10
        MockRepo.return_value.get_count.assert_called_once_with(status="invited")

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_get_count_without_filter(self, MockRepo):
        """Should return total count when no status filter."""
        MockRepo.return_value.get_count.return_value = 100

        service = WaitlistService()
        result = service.get_count()

        assert result == 100
        MockRepo.return_value.get_count.assert_called_once_with(status=None)


class TestInvite:
    """Tests for WaitlistService.invite."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_invite_returns_token(self, MockRepo):
        """Should return invite token on success."""
        MockRepo.return_value.invite.return_value = "abc123token"

        service = WaitlistService()
        result = service.invite(waitlist_id=1, assigned_tier="free")

        assert result == "abc123token"
        MockRepo.return_value.invite.assert_called_once_with(1, assigned_tier="free")

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_invite_returns_none_when_not_found(self, MockRepo):
        """Should return None when waitlist entry not found."""
        MockRepo.return_value.invite.return_value = None

        service = WaitlistService()
        result = service.invite(waitlist_id=999)

        assert result is None


class TestBulkInvite:
    """Tests for WaitlistService.bulk_invite."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_bulk_invite_returns_results(self, MockRepo):
        """Should return list of (id, token) tuples."""
        MockRepo.return_value.bulk_invite.return_value = [
            (1, "token1"),
            (2, "token2"),
        ]

        service = WaitlistService()
        result = service.bulk_invite(waitlist_ids=[1, 2], assigned_tier="pro")

        assert len(result) == 2
        MockRepo.return_value.bulk_invite.assert_called_once_with(
            [1, 2], assigned_tier="pro"
        )


class TestDecline:
    """Tests for WaitlistService.decline."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_decline_returns_true(self, MockRepo):
        """Should return True on successful decline."""
        MockRepo.return_value.decline.return_value = True

        service = WaitlistService()
        result = service.decline(waitlist_id=1)

        assert result is True

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_decline_returns_false_when_not_found(self, MockRepo):
        """Should return False when entry not found."""
        MockRepo.return_value.decline.return_value = False

        service = WaitlistService()
        result = service.decline(waitlist_id=999)

        assert result is False


class TestIsInviteValid:
    """Tests for WaitlistService.is_invite_valid."""

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_valid_token_returns_true(self, MockRepo):
        """Should return True for a valid invite token."""
        MockRepo.return_value.is_invite_valid.return_value = True

        service = WaitlistService()
        assert service.is_invite_valid(token="abc123") is True

    @patch("rivaflow.core.services.waitlist_service.WaitlistRepository")
    def test_invalid_token_returns_false(self, MockRepo):
        """Should return False for an expired or invalid token."""
        MockRepo.return_value.is_invite_valid.return_value = False

        service = WaitlistService()
        assert service.is_invite_valid(token="expired") is False
