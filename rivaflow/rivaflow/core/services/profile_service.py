"""Service layer for user profile operations."""

import logging
import uuid
from datetime import datetime
from pathlib import Path

import filetype

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.db.repositories import ProfileRepository
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class ProfileService:
    """Business logic for user profile."""

    # Photo upload configuration
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(self):
        self.repo = ProfileRepository()
        self.user_repo = UserRepository()

    def get_profile(self, user_id: int) -> dict | None:
        """Get the user profile with progress stats since last promotion."""
        profile = self.repo.get(user_id)
        if not profile:
            return None

        # Calculate sessions and hours since last belt promotion
        from datetime import date

        from rivaflow.db.repositories.grading_repo import GradingRepository
        from rivaflow.db.repositories.session_repo import SessionRepository

        grading_repo = GradingRepository()
        session_repo = SessionRepository()

        latest_grading = grading_repo.get_latest(user_id)

        if latest_grading and latest_grading.get("date_graded"):
            # Sync current_grade from latest grading if it doesn't match
            latest_grade = latest_grading.get("grade", "White")
            if profile.get("current_grade") != latest_grade:
                # Update database
                self.repo.update(user_id, current_grade=latest_grade)
                profile["current_grade"] = latest_grade

            # Get sessions since last grading date
            grading_date_str = latest_grading["date_graded"]
            if isinstance(grading_date_str, str):
                grading_date = date.fromisoformat(grading_date_str)
            else:
                grading_date = grading_date_str

            today = date.today()
            sessions_since_promotion = session_repo.get_by_date_range(
                user_id, grading_date, today
            )

            total_sessions_since = len(sessions_since_promotion)
            total_hours_since = (
                sum(s.get("duration_mins", 0) for s in sessions_since_promotion) / 60
            )

            profile["sessions_since_promotion"] = total_sessions_since
            profile["hours_since_promotion"] = round(total_hours_since, 1)
            profile["promotion_date"] = grading_date_str
        else:
            # No promotion yet, count all sessions
            all_sessions = session_repo.get_by_date_range(
                user_id, date(2020, 1, 1), date.today()
            )
            profile["sessions_since_promotion"] = len(all_sessions)
            profile["hours_since_promotion"] = round(
                sum(s.get("duration_mins", 0) for s in all_sessions) / 60, 1
            )
            profile["promotion_date"] = None

        return profile

    def update_profile(
        self,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: str | None = None,
        sex: str | None = None,
        city: str | None = None,
        state: str | None = None,
        default_gym: str | None = None,
        default_location: str | None = None,
        current_grade: str | None = None,
        current_professor: str | None = None,
        current_instructor_id: int | None = None,
        primary_training_type: str | None = None,
        height_cm: int | None = None,
        target_weight_kg: float | None = None,
        weekly_sessions_target: int | None = None,
        weekly_hours_target: float | None = None,
        weekly_rolls_target: int | None = None,
        weekly_bjj_sessions_target: int | None = None,
        weekly_sc_sessions_target: int | None = None,
        weekly_mobility_sessions_target: int | None = None,
        show_streak_on_dashboard: bool | None = None,
        show_weekly_goals: bool | None = None,
        timezone: str | None = None,
    ) -> dict:
        """Update the user profile. Returns updated profile."""
        return self.repo.update(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            sex=sex,
            city=city,
            state=state,
            default_gym=default_gym,
            default_location=default_location,
            current_grade=current_grade,
            current_professor=current_professor,
            current_instructor_id=current_instructor_id,
            primary_training_type=primary_training_type,
            height_cm=height_cm,
            target_weight_kg=target_weight_kg,
            weekly_sessions_target=weekly_sessions_target,
            weekly_hours_target=weekly_hours_target,
            weekly_rolls_target=weekly_rolls_target,
            weekly_bjj_sessions_target=weekly_bjj_sessions_target,
            weekly_sc_sessions_target=weekly_sc_sessions_target,
            weekly_mobility_sessions_target=weekly_mobility_sessions_target,
            show_streak_on_dashboard=show_streak_on_dashboard,
            show_weekly_goals=show_weekly_goals,
            timezone=timezone,
        )

    def get_default_gym(self, user_id: int) -> str | None:
        """Get the default gym from profile."""
        profile = self.get_profile(user_id)
        return profile.get("default_gym") if profile else None

    def get_current_professor(self, user_id: int) -> str | None:
        """Get the current professor from profile."""
        profile = self.get_profile(user_id)
        return profile.get("current_professor") if profile else None

    def upload_profile_photo(
        self, user_id: int, file_content: bytes, filename: str
    ) -> dict:
        """Handle profile photo upload.

        Args:
            user_id: User ID
            file_content: Raw file bytes
            filename: Original filename

        Returns:
            Dict with avatar_url, filename, and success message

        Raises:
            ValidationError: If file type or size is invalid
        """
        # Validate file extension
        file_ext = Path(filename).suffix.lower() if filename else ""
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file type. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
                details={"allowed_extensions": list(self.ALLOWED_EXTENSIONS)},
            )

        # Validate file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024 * 1024)}MB",
                details={"max_size_mb": self.MAX_FILE_SIZE // (1024 * 1024)},
            )

        # Validate actual file content (magic bytes check)
        kind = filetype.guess(file_content)
        allowed_types = {"jpg", "jpeg", "png", "webp", "gif"}
        if kind is None or kind.extension not in allowed_types:
            detected = kind.extension if kind else "unknown"
            raise ValidationError(
                f"File content is not a valid image (detected: {detected}). "
                f"Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )

        # Generate unique filename: user_{user_id}_{timestamp}_{uuid}.{ext}
        from rivaflow.core.services.storage_service import get_storage

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"user_{user_id}_{timestamp}_{unique_id}{file_ext}"

        # Upload via storage service (local or S3/R2)
        storage = get_storage()
        avatar_url = storage.upload("avatars", new_filename, file_content)

        # Update user's avatar_url in database
        self.user_repo.update_avatar(user_id, avatar_url)

        return {
            "avatar_url": avatar_url,
            "filename": new_filename,
            "message": "Profile photo uploaded successfully",
        }

    def delete_profile_photo(self, user_id: int) -> dict:
        """Delete the current profile photo.

        Args:
            user_id: User ID

        Returns:
            Success message dict

        Raises:
            NotFoundError: If no profile photo exists
        """
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.get("avatar_url"):
            raise NotFoundError("No profile photo to delete")

        avatar_url = user["avatar_url"]

        # Delete file from storage
        from rivaflow.core.services.storage_service import get_storage

        # Extract filename from URL
        filename = avatar_url.rsplit("/", 1)[-1]
        try:
            storage = get_storage()
            storage.delete("avatars", filename)
        except Exception as e:
            logger.warning(f"Error deleting avatar file {filename}: {e}")

        # Clear avatar_url in database
        self.user_repo.update_avatar(user_id, None)

        return {"message": "Profile photo deleted successfully"}
