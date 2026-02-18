"""Activity photo service."""

import logging

from rivaflow.core.services.storage_service import get_storage
from rivaflow.db.repositories import ActivityPhotoRepository

logger = logging.getLogger(__name__)


class PhotoService:
    """Wraps ActivityPhotoRepository + storage."""

    def __init__(self):
        self.repo = ActivityPhotoRepository()

    def create(self, **kwargs) -> int:
        logger.info(
            "Creating photo for user %d, %s #%d",
            kwargs["user_id"],
            kwargs["activity_type"],
            kwargs["activity_id"],
        )
        return self.repo.create(**kwargs)

    def get_by_id(self, user_id: int, photo_id: int) -> dict | None:
        return self.repo.get_by_id(user_id, photo_id)

    def get_by_activity(
        self, user_id: int, activity_type: str, activity_id: int
    ) -> list[dict]:
        return self.repo.get_by_activity(user_id, activity_type, activity_id)

    def count_by_activity(
        self, user_id: int, activity_type: str, activity_id: int
    ) -> int:
        return self.repo.count_by_activity(user_id, activity_type, activity_id)

    def update_caption(self, user_id: int, photo_id: int, caption: str) -> bool:
        return self.repo.update_caption(user_id, photo_id, caption)

    def delete(self, user_id: int, photo_id: int) -> bool:
        logger.info("Deleting photo %d for user %d", photo_id, user_id)
        return self.repo.delete(user_id, photo_id)

    def delete_file(self, folder: str, filename: str) -> None:
        logger.info("Deleting file %s from %s", filename, folder)
        storage = get_storage()
        storage.delete(folder, filename)

    def upload_file(self, folder: str, filename: str, content: bytes) -> str:
        storage = get_storage()
        return storage.upload(folder, filename, content)
