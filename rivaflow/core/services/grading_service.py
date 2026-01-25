"""Service layer for grading/belt progression operations."""
from typing import List, Optional

from rivaflow.db.repositories import GradingRepository, ProfileRepository


class GradingService:
    """Business logic for belt gradings."""

    def __init__(self):
        self.repo = GradingRepository()
        self.profile_repo = ProfileRepository()

    def create_grading(
        self, grade: str, date_graded: str, notes: Optional[str] = None
    ) -> dict:
        """
        Create a new grading entry and update the profile's current_grade
        to the most recent grading by date.
        Returns the created grading.
        """
        # Create the grading
        grading = self.repo.create(grade=grade, date_graded=date_graded, notes=notes)

        # Update profile's current_grade to the most recent grading by date
        latest = self.repo.get_latest()
        if latest:
            self.profile_repo.update(current_grade=latest["grade"])

        return grading

    def list_gradings(self) -> List[dict]:
        """Get all gradings, ordered by date (newest first)."""
        return self.repo.list_all(order_by="date_graded DESC, id DESC")

    def get_latest_grading(self) -> Optional[dict]:
        """Get the most recent grading."""
        return self.repo.get_latest()

    def delete_grading(self, grading_id: int) -> bool:
        """
        Delete a grading by ID and update the profile's current_grade
        to the most recent remaining grading by date.
        """
        deleted = self.repo.delete(grading_id)

        if deleted:
            # Update profile's current_grade to the latest remaining grading
            latest = self.repo.get_latest()
            if latest:
                self.profile_repo.update(current_grade=latest["grade"])
            else:
                # No gradings left, clear the current_grade
                self.profile_repo.update(current_grade=None)

        return deleted
