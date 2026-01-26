"""Service layer for movements glossary operations."""
from typing import List, Optional

from rivaflow.db.repositories import GlossaryRepository


class GlossaryService:
    """Business logic for movements glossary."""

    def __init__(self):
        self.repo = GlossaryRepository()

    def list_movements(
        self,
        user_id: int,
        category: Optional[str] = None,
        search: Optional[str] = None,
        gi_only: bool = False,
        nogi_only: bool = False,
    ) -> List[dict]:
        """Get all movements with optional filtering."""
        return self.repo.list_all(
            user_id=user_id,
            category=category,
            search=search,
            gi_only=gi_only,
            nogi_only=nogi_only,
        )

    def get_movement(self, user_id: int, movement_id: int, include_custom_videos: bool = False) -> Optional[dict]:
        """Get a specific movement by ID, optionally with custom video links."""
        return self.repo.get_by_id(user_id, movement_id, include_custom_videos=include_custom_videos)

    def get_movement_by_name(self, user_id: int, name: str) -> Optional[dict]:
        """Get a movement by exact name."""
        return self.repo.get_by_name(user_id, name)

    def get_categories(self, user_id: int) -> List[str]:
        """Get list of all movement categories."""
        return self.repo.get_categories(user_id)

    def create_custom_movement(
        self,
        user_id: int,
        name: str,
        category: str,
        subcategory: Optional[str] = None,
        points: int = 0,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        gi_applicable: bool = True,
        nogi_applicable: bool = True,
    ) -> dict:
        """Create a custom user-added movement."""
        return self.repo.create_custom(
            user_id=user_id,
            name=name,
            category=category,
            subcategory=subcategory,
            points=points,
            description=description,
            aliases=aliases,
            gi_applicable=gi_applicable,
            nogi_applicable=nogi_applicable,
        )

    def delete_custom_movement(self, user_id: int, movement_id: int) -> bool:
        """Delete a custom movement. Can only delete custom movements."""
        return self.repo.delete_custom(user_id, movement_id)

    def add_custom_video(
        self,
        user_id: int,
        movement_id: int,
        url: str,
        title: Optional[str] = None,
        video_type: str = "general",
    ) -> dict:
        """Add a custom video link to a movement."""
        return self.repo.add_custom_video(
            user_id=user_id,
            movement_id=movement_id,
            url=url,
            title=title,
            video_type=video_type,
        )

    def delete_custom_video(self, user_id: int, video_id: int) -> bool:
        """Delete a custom video link."""
        return self.repo.delete_custom_video(user_id, video_id)
