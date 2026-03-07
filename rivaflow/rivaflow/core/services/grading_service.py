"""Service layer for grading/belt progression operations."""

from rivaflow.db.repositories import GradingRepository, ProfileRepository, SessionRepository


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
        professor: str | None = None,
        instructor_id: int | None = None,
        notes: str | None = None,
        photo_url: str | None = None,
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
            photo_url=photo_url,
        )

        # Update profile's current_grade to the most recent grading by date
        latest = self.repo.get_latest(user_id)
        if latest:
            self.profile_repo.update(user_id, current_grade=latest["grade"])

        return grading

    def list_gradings(self, user_id: int) -> list[dict]:
        """Get all gradings, ordered by date (newest first)."""
        return self.repo.list_all(user_id, order_by="date_graded DESC, id DESC")

    def get_latest_grading(self, user_id: int) -> dict | None:
        """Get the most recent grading."""
        return self.repo.get_latest(user_id)

    def update_grading(
        self,
        user_id: int,
        grading_id: int,
        grade: str | None = None,
        date_graded: str | None = None,
        professor: str | None = None,
        instructor_id: int | None = None,
        notes: str | None = None,
        photo_url: str | None = None,
    ) -> dict | None:
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

    def get_promotion_stats(self, user_id: int, grading_id: int) -> dict:
        """Get training stats since the previous belt promotion.

        Returns:
            Dict with total_sessions, total_hours, total_rolls, class_types breakdown
        """
        from datetime import date

        from rivaflow.db.database import convert_query, get_connection

        # Get all gradings ordered by date
        gradings = self.repo.list_all(user_id, order_by="date_graded DESC, id DESC")

        # Find the current grading and its predecessor
        current_grading = None
        previous_grading = None
        found_current = False
        for g in gradings:
            if g["id"] == grading_id:
                current_grading = g
                found_current = True
                continue
            if found_current:
                previous_grading = g
                break

        if not current_grading:
            return {
                "total_sessions": 0,
                "total_hours": 0.0,
                "total_rolls": 0,
                "class_types": {},
            }

        current_date = str(current_grading["date_graded"])
        start_date = str(previous_grading["date_graded"]) if previous_grading else "2000-01-01"

        # Query sessions between the two dates
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    SELECT
                        COUNT(*) as total_sessions,
                        COALESCE(SUM(duration_mins), 0) as total_minutes,
                        COALESCE(SUM(rolls), 0) as total_rolls,
                        class_type
                    FROM sessions
                    WHERE user_id = ?
                      AND session_date >= ?
                      AND session_date <= ?
                    GROUP BY class_type
                """),
                (user_id, start_date, current_date),
            )
            rows = cursor.fetchall()

        total_sessions = 0
        total_minutes = 0
        total_rolls = 0
        class_types: dict[str, int] = {}

        for row in rows:
            r = dict(row)
            count = r["total_sessions"] or 0
            total_sessions += count
            total_minutes += r["total_minutes"] or 0
            total_rolls += r["total_rolls"] or 0
            ct = r["class_type"]
            if ct:
                class_types[ct] = count

        return {
            "total_sessions": total_sessions,
            "total_hours": round(total_minutes / 60, 1),
            "total_rolls": total_rolls,
            "class_types": class_types,
        }

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
