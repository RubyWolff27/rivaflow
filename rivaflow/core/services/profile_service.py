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
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        sex: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        default_gym: Optional[str] = None,
        current_grade: Optional[str] = None,
        current_professor: Optional[str] = None,
    ) -> dict:
        """Update the user profile. Returns updated profile."""
        return self.repo.update(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex=sex,
            city=city,
            state=state,
            default_gym=default_gym,
            current_grade=current_grade,
            current_professor=current_professor,
        )

    def get_default_gym(self) -> Optional[str]:
        """Get the default gym from profile."""
        profile = self.get_profile()
        return profile.get("default_gym") if profile else None

    def get_current_professor(self) -> Optional[str]:
        """Get the current professor from profile."""
        profile = self.get_profile()
        return profile.get("current_professor") if profile else None
