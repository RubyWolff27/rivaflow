"""Service layer for user profile operations."""
from typing import Optional

from rivaflow.db.repositories import ProfileRepository


class ProfileService:
    """Business logic for user profile."""

    def __init__(self):
        self.repo = ProfileRepository()

    def get_profile(self) -> Optional[dict]:
        """Get the user profile."""
        return self.repo.get()

    def update_profile(
        self,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        default_gym: Optional[str] = None,
        current_grade: Optional[str] = None,
    ) -> dict:
        """Update the user profile. Returns updated profile."""
        return self.repo.update(
            age=age,
            sex=sex,
            default_gym=default_gym,
            current_grade=current_grade,
        )

    def get_default_gym(self) -> Optional[str]:
        """Get the default gym from profile."""
        profile = self.get_profile()
        return profile.get("default_gym") if profile else None
