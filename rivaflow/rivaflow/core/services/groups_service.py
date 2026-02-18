"""Groups service."""

import logging

from rivaflow.db.repositories.groups_repo import GroupsRepository

logger = logging.getLogger(__name__)


class GroupsService:
    """Wraps GroupsRepository."""

    def __init__(self):
        self.repo = GroupsRepository()

    def create(self, user_id: int, data: dict) -> int:
        logger.info("Creating group '%s' for user %d", data.get("name"), user_id)
        return self.repo.create(user_id=user_id, data=data)

    def get_by_id(self, group_id: int) -> dict | None:
        return self.repo.get_by_id(group_id)

    def list_by_user(self, user_id: int) -> list[dict]:
        return self.repo.list_by_user(user_id=user_id)

    def list_discoverable(self, user_id: int) -> list[dict]:
        return self.repo.list_discoverable(user_id=user_id)

    def get_members(self, group_id: int) -> list[dict]:
        return self.repo.get_members(group_id)

    def get_member_count(self, group_id: int) -> int:
        return self.repo.get_member_count(group_id)

    def get_member_role(self, group_id: int, user_id: int) -> str | None:
        return self.repo.get_member_role(group_id, user_id)

    def update(self, group_id: int, user_id: int, data: dict) -> bool:
        logger.info("Updating group %d", group_id)
        return self.repo.update(group_id=group_id, user_id=user_id, data=data)

    def delete(self, group_id: int, user_id: int) -> bool:
        logger.info("Deleting group %d", group_id)
        return self.repo.delete(group_id=group_id, user_id=user_id)

    def add_member(self, group_id: int, user_id: int, role: str = "member") -> bool:
        logger.info("Adding user %d to group %d", user_id, group_id)
        return self.repo.add_member(group_id=group_id, user_id=user_id, role=role)

    def remove_member(self, group_id: int, user_id: int) -> bool:
        logger.info("Removing user %d from group %d", user_id, group_id)
        return self.repo.remove_member(group_id=group_id, user_id=user_id)
