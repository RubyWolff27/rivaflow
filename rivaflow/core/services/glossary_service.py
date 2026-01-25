"""Service layer for movements glossary operations."""
from typing import List, Optional

from rivaflow.db.repositories import GlossaryRepository


class GlossaryService:
    """Business logic for movements glossary."""

    def __init__(self):
        self.repo = GlossaryRepository()

    def list_movements(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        gi_only: bool = False,
        nogi_only: bool = False,
    ) -> List[dict]:
        """Get all movements with optional filtering."""
        return self.repo.list_all(
            category=category,
            search=search,
            gi_only=gi_only,
            nogi_only=nogi_only,
        )

    def get_movement(self, movement_id: int) -> Optional[dict]:
        """Get a specific movement by ID."""
        return self.repo.get_by_id(movement_id)

    def get_movement_by_name(self, name: str) -> Optional[dict]:
        """Get a movement by exact name."""
        return self.repo.get_by_name(name)

    def get_categories(self) -> List[str]:
        """Get list of all movement categories."""
        return self.repo.get_categories()

    def create_custom_movement(
        self,
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
            name=name,
            category=category,
            subcategory=subcategory,
            points=points,
            description=description,
            aliases=aliases,
            gi_applicable=gi_applicable,
            nogi_applicable=nogi_applicable,
        )

    def delete_custom_movement(self, movement_id: int) -> bool:
        """Delete a custom movement. Can only delete custom movements."""
        return self.repo.delete_custom(movement_id)
