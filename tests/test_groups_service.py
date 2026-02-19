"""Unit tests for GroupsService -- groups and membership management."""

from unittest.mock import patch

from rivaflow.core.services.groups_service import GroupsService


class TestCreate:
    """Tests for create."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_creates_group_and_returns_id(self, MockRepo):
        """Should create a group and return its ID."""
        MockRepo.return_value.create.return_value = 5

        service = GroupsService()
        result = service.create(
            user_id=1, data={"name": "Morning Crew", "description": "Early birds"}
        )

        assert result == 5
        MockRepo.return_value.create.assert_called_once_with(
            user_id=1,
            data={"name": "Morning Crew", "description": "Early birds"},
        )


class TestGetById:
    """Tests for get_by_id."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_group(self, MockRepo):
        """Should return group dict when found."""
        mock_group = {"id": 5, "name": "Morning Crew"}
        MockRepo.return_value.get_by_id.return_value = mock_group

        service = GroupsService()
        result = service.get_by_id(group_id=5)

        assert result == mock_group

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_none_when_not_found(self, MockRepo):
        """Should return None when group does not exist."""
        MockRepo.return_value.get_by_id.return_value = None

        service = GroupsService()
        result = service.get_by_id(group_id=999)

        assert result is None


class TestListByUser:
    """Tests for list_by_user."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_user_groups(self, MockRepo):
        """Should return groups the user belongs to."""
        mock_groups = [
            {"id": 1, "name": "Group A"},
            {"id": 2, "name": "Group B"},
        ]
        MockRepo.return_value.list_by_user.return_value = mock_groups

        service = GroupsService()
        result = service.list_by_user(user_id=1)

        assert len(result) == 2

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_empty_list(self, MockRepo):
        """Should return empty list when user has no groups."""
        MockRepo.return_value.list_by_user.return_value = []

        service = GroupsService()
        result = service.list_by_user(user_id=99)

        assert result == []


class TestListDiscoverable:
    """Tests for list_discoverable."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_discoverable_groups(self, MockRepo):
        """Should return public/discoverable groups."""
        mock_groups = [{"id": 3, "name": "Open Group"}]
        MockRepo.return_value.list_discoverable.return_value = mock_groups

        service = GroupsService()
        result = service.list_discoverable(user_id=1)

        assert len(result) == 1
        MockRepo.return_value.list_discoverable.assert_called_once_with(user_id=1)


class TestGetMembers:
    """Tests for get_members."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_group_members(self, MockRepo):
        """Should return list of group members."""
        mock_members = [
            {"user_id": 1, "role": "admin"},
            {"user_id": 2, "role": "member"},
        ]
        MockRepo.return_value.get_members.return_value = mock_members

        service = GroupsService()
        result = service.get_members(group_id=5)

        assert len(result) == 2


class TestGetMemberCount:
    """Tests for get_member_count."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_count(self, MockRepo):
        """Should return the number of members."""
        MockRepo.return_value.get_member_count.return_value = 15

        service = GroupsService()
        result = service.get_member_count(group_id=5)

        assert result == 15


class TestGetMemberRole:
    """Tests for get_member_role."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_role(self, MockRepo):
        """Should return role string for a member."""
        MockRepo.return_value.get_member_role.return_value = "admin"

        service = GroupsService()
        result = service.get_member_role(group_id=5, user_id=1)

        assert result == "admin"

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_none_for_non_member(self, MockRepo):
        """Should return None when user is not a member."""
        MockRepo.return_value.get_member_role.return_value = None

        service = GroupsService()
        result = service.get_member_role(group_id=5, user_id=99)

        assert result is None


class TestUpdate:
    """Tests for update."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_updates_group(self, MockRepo):
        """Should return True when update succeeds."""
        MockRepo.return_value.update.return_value = True

        service = GroupsService()
        result = service.update(group_id=5, user_id=1, data={"name": "Updated Name"})

        assert result is True

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_false_on_failure(self, MockRepo):
        """Should return False when update fails."""
        MockRepo.return_value.update.return_value = False

        service = GroupsService()
        result = service.update(group_id=5, user_id=99, data={"name": "X"})

        assert result is False


class TestDelete:
    """Tests for delete."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_deletes_group(self, MockRepo):
        """Should return True when group is deleted."""
        MockRepo.return_value.delete.return_value = True

        service = GroupsService()
        result = service.delete(group_id=5, user_id=1)

        assert result is True

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_false_when_not_found(self, MockRepo):
        """Should return False when group does not exist."""
        MockRepo.return_value.delete.return_value = False

        service = GroupsService()
        result = service.delete(group_id=999, user_id=1)

        assert result is False


class TestAddMember:
    """Tests for add_member."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_adds_member(self, MockRepo):
        """Should add member with default role."""
        MockRepo.return_value.add_member.return_value = True

        service = GroupsService()
        result = service.add_member(group_id=5, user_id=2)

        assert result is True
        MockRepo.return_value.add_member.assert_called_once_with(
            group_id=5, user_id=2, role="member"
        )

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_adds_member_with_custom_role(self, MockRepo):
        """Should add member with custom role."""
        MockRepo.return_value.add_member.return_value = True

        service = GroupsService()
        service.add_member(group_id=5, user_id=2, role="admin")

        MockRepo.return_value.add_member.assert_called_once_with(
            group_id=5, user_id=2, role="admin"
        )


class TestRemoveMember:
    """Tests for remove_member."""

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_removes_member(self, MockRepo):
        """Should return True when member is removed."""
        MockRepo.return_value.remove_member.return_value = True

        service = GroupsService()
        result = service.remove_member(group_id=5, user_id=2)

        assert result is True

    @patch("rivaflow.core.services.groups_service.GroupsRepository")
    def test_returns_false_when_not_member(self, MockRepo):
        """Should return False when user is not a member."""
        MockRepo.return_value.remove_member.return_value = False

        service = GroupsService()
        result = service.remove_member(group_id=5, user_id=99)

        assert result is False
