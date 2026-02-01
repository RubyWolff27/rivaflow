"""Service layer for grading/belt progression operations."""
from typing import List, Optional

from rivaflow.db.repositories import GradingRepository, ProfileRepository


class GradingService:
    """Business logic for belt gradings."""

    def __init__(self):
        self.repo = GradingRepository()
        self.profile_repo = ProfileRepository()

    def create_grading(
        self,
        user_id: int,
        grade: str,
        date_graded: str,
        professor: Optional[str] = None,
        instructor_id: Optional[int] = None,
        notes: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> dict:
        """
        Create a new grading entry and update the profile's current_grade
        to the most recent grading by date.
        Returns the created grading.
        """
        # Create the grading
        grading = self.repo.create(
            user_id=user_id,
            grade=grade,
            date_graded=date_graded,
            professor=professor,
            instructor_id=instructor_id,
            notes=notes,
            photo_url=photo_url
        )

        # Update profile's current_grade to the most recent grading by date
        latest = self.repo.get_latest(user_id)
        if latest:
            self.profile_repo.update(user_id, current_grade=latest["grade"])

        return grading

    def list_gradings(self, user_id: int) -> List[dict]:
        """Get all gradings, ordered by date (newest first)."""
        return self.repo.list_all(user_id, order_by="date_graded DESC, id DESC")

    def get_latest_grading(self, user_id: int) -> Optional[dict]:
        """Get the most recent grading."""
        return self.repo.get_latest(user_id)

    def update_grading(
        self,
        user_id: int,
        grading_id: int,
        grade: Optional[str] = None,
        date_graded: Optional[str] = None,
        professor: Optional[str] = None,
        instructor_id: Optional[int] = None,
        notes: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Update a grading and refresh the profile's current_grade
        to the most recent grading by date.
        Returns the updated grading or None if not found.
        """
        updated = self.repo.update(
            user_id=user_id,
            grading_id=grading_id,
            grade=grade,
            date_graded=date_graded,
            professor=professor,
            instructor_id=instructor_id,
            notes=notes,
            photo_url=photo_url,
        )

        if updated:
            # Update profile's current_grade to the latest grading by date
            latest = self.repo.get_latest(user_id)
            if latest:
                self.profile_repo.update(user_id, current_grade=latest["grade"])

        return updated

    def delete_grading(self, user_id: int, grading_id: int) -> bool:
        """
        Delete a grading by ID and update the profile's current_grade
        to the most recent remaining grading by date.
        """
        deleted = self.repo.delete(user_id, grading_id)

        if deleted:
            # Update profile's current_grade to the latest remaining grading
            latest = self.repo.get_latest(user_id)
            if latest:
                self.profile_repo.update(user_id, current_grade=latest["grade"])
            else:
                # No gradings left, clear the current_grade
                self.profile_repo.update(user_id, current_grade=None)

        return deleted
