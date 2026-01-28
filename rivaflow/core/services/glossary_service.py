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
        # Movements are global, user_id not needed for listing
        return self.repo.list_all(
            category=category,
            search=search,
            gi_only=gi_only,
            nogi_only=nogi_only,
        )

    def get_movement(self, user_id: int, movement_id: int, include_custom_videos: bool = False) -> Optional[dict]:
        """Get a specific movement by ID, optionally with custom video links."""
        # Movements are global, but custom videos are user-specific
        return self.repo.get_by_id(movement_id, include_custom_videos=include_custom_videos)

    def get_movement_by_name(self, user_id: int, name: str) -> Optional[dict]:
        """Get a movement by exact name."""
        # Movements are global
        return self.repo.get_by_name(name)

    def get_categories(self, user_id: int) -> List[str]:
        """Get list of all movement categories."""
        # Categories are global
        return self.repo.get_categories()

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
        # Custom movements are global (not user-specific)
        return self.repo.create_custom(
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
        # Custom movements are global
        return self.repo.delete_custom(movement_id)

    def add_custom_video(
        self,
        user_id: int,
        movement_id: int,
        url: str,
        title: Optional[str] = None,
        video_type: str = "general",
    ) -> dict:
        """Add a custom video link to a movement."""
        # Custom videos are global
        return self.repo.add_custom_video(
            movement_id=movement_id,
            url=url,
            title=title,
            video_type=video_type,
        )

    def delete_custom_video(self, user_id: int, video_id: int) -> bool:
        """Delete a custom video link."""
        # Custom videos are global
        return self.repo.delete_custom_video(video_id)
