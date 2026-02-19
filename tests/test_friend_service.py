"""Unit tests for FriendService -- training partners and instructors."""

from unittest.mock import patch

from rivaflow.core.services.friend_service import FriendService


class TestCreateFriend:
    """Tests for create_friend."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_creates_friend_with_defaults(self, MockRepo):
        """Should create a friend with default type and return dict."""
        mock_friend = {
            "id": 1,
            "name": "Carlos",
            "friend_type": "training-partner",
        }
        MockRepo.return_value.create.return_value = mock_friend

        service = FriendService()
        result = service.create_friend(user_id=1, name="Carlos")

        assert result == mock_friend
        MockRepo.return_value.create.assert_called_once_with(
            user_id=1,
            name="Carlos",
            friend_type="training-partner",
            belt_rank=None,
            belt_stripes=0,
            instructor_certification=None,
            phone=None,
            email=None,
            notes=None,
        )

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_creates_instructor(self, MockRepo):
        """Should create an instructor with certification."""
        mock_friend = {
            "id": 2,
            "name": "Professor Silva",
            "friend_type": "instructor",
        }
        MockRepo.return_value.create.return_value = mock_friend

        service = FriendService()
        result = service.create_friend(
            user_id=1,
            name="Professor Silva",
            friend_type="instructor",
            belt_rank="black",
            belt_stripes=3,
            instructor_certification="IBJJF",
        )

        assert result["friend_type"] == "instructor"


class TestGetFriend:
    """Tests for get_friend."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_returns_friend_by_id(self, MockRepo):
        """Should return friend dict when found."""
        mock_friend = {"id": 1, "name": "Carlos"}
        MockRepo.return_value.get_by_id.return_value = mock_friend

        service = FriendService()
        result = service.get_friend(user_id=1, friend_id=1)

        assert result == mock_friend

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when friend does not exist."""
        MockRepo.return_value.get_by_id.return_value = None

        service = FriendService()
        result = service.get_friend(user_id=1, friend_id=999)

        assert result is None


class TestGetFriendByName:
    """Tests for get_friend_by_name."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_returns_friend_by_exact_name(self, MockRepo):
        """Should return friend matched by exact name."""
        mock_friend = {"id": 1, "name": "Carlos"}
        MockRepo.return_value.get_by_name.return_value = mock_friend

        service = FriendService()
        result = service.get_friend_by_name(user_id=1, name="Carlos")

        assert result == mock_friend


class TestListFriends:
    """Tests for list_friends."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_lists_all_friends(self, MockRepo):
        """Should return all friends ordered by name."""
        mock_friends = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        MockRepo.return_value.list_all.return_value = mock_friends

        service = FriendService()
        result = service.list_friends(user_id=1)

        assert len(result) == 2
        MockRepo.return_value.list_all.assert_called_once_with(1, order_by="name ASC")


class TestListInstructors:
    """Tests for list_instructors."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_combines_instructors_and_other(self, MockRepo):
        """Should return instructors + other type friends."""
        MockRepo.return_value.list_by_type.side_effect = [
            [{"id": 1, "name": "Prof Silva", "friend_type": "instructor"}],
            [{"id": 3, "name": "Coach Lee", "friend_type": "other"}],
        ]

        service = FriendService()
        result = service.list_instructors(user_id=1)

        assert len(result) == 2
        assert result[0]["friend_type"] == "instructor"
        assert result[1]["friend_type"] == "other"


class TestListTrainingPartners:
    """Tests for list_training_partners."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_combines_partners_and_other(self, MockRepo):
        """Should return training partners + other type friends."""
        MockRepo.return_value.list_by_type.side_effect = [
            [{"id": 2, "name": "Carlos", "friend_type": "training-partner"}],
            [],
        ]

        service = FriendService()
        result = service.list_training_partners(user_id=1)

        assert len(result) == 1
        assert result[0]["friend_type"] == "training-partner"


class TestSearchFriends:
    """Tests for search_friends."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_searches_by_name(self, MockRepo):
        """Should return friends matching search query."""
        MockRepo.return_value.search.return_value = [{"id": 1, "name": "Carlos"}]

        service = FriendService()
        result = service.search_friends(user_id=1, query="Car")

        assert len(result) == 1
        MockRepo.return_value.search.assert_called_once_with(1, "Car")


class TestUpdateFriend:
    """Tests for update_friend."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_updates_friend(self, MockRepo):
        """Should return updated friend dict."""
        mock_updated = {"id": 1, "name": "Carlos Updated"}
        MockRepo.return_value.update.return_value = mock_updated

        service = FriendService()
        result = service.update_friend(user_id=1, friend_id=1, name="Carlos Updated")

        assert result["name"] == "Carlos Updated"

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when friend does not exist."""
        MockRepo.return_value.update.return_value = None

        service = FriendService()
        result = service.update_friend(user_id=1, friend_id=999, name="Ghost")

        assert result is None


class TestDeleteFriend:
    """Tests for delete_friend."""

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_deletes_friend(self, MockRepo):
        """Should return True when friend is deleted."""
        MockRepo.return_value.delete.return_value = True

        service = FriendService()
        result = service.delete_friend(user_id=1, friend_id=1)

        assert result is True

    @patch("rivaflow.core.services.friend_service.FriendRepository")
    def test_returns_false_when_not_found(self, MockRepo):
        """Should return False when friend does not exist."""
        MockRepo.return_value.delete.return_value = False

        service = FriendService()
        result = service.delete_friend(user_id=1, friend_id=999)

        assert result is False


class TestFormatBeltDisplay:
    """Tests for format_belt_display."""

    def test_unranked_when_no_belt(self):
        """Should return 'Unranked' when no belt_rank."""
        service = FriendService()
        result = service.format_belt_display({})
        assert result == "Unranked"

    def test_belt_without_stripes(self):
        """Should format belt without stripes."""
        service = FriendService()
        result = service.format_belt_display({"belt_rank": "blue", "belt_stripes": 0})
        assert result == "Blue Belt"

    def test_belt_with_one_stripe(self):
        """Should format singular stripe."""
        service = FriendService()
        result = service.format_belt_display({"belt_rank": "purple", "belt_stripes": 1})
        assert result == "Purple Belt (1 stripe)"

    def test_belt_with_multiple_stripes(self):
        """Should format plural stripes."""
        service = FriendService()
        result = service.format_belt_display({"belt_rank": "brown", "belt_stripes": 4})
        assert result == "Brown Belt (4 stripes)"
