"""Service layer for user profile operations."""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from rivaflow.db.repositories import ProfileRepository
from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.core.exceptions import ValidationError, NotFoundError


class ProfileService:
    """Business logic for user profile."""

    # Photo upload configuration
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    def __init__(self):
        self.repo = ProfileRepository()
        self.user_repo = UserRepository()

        # Configure upload directory
        self.upload_dir = Path(__file__).parent.parent.parent.parent / "uploads" / "avatars"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def get_profile(self, user_id: int) -> Optional[dict]:
        """Get the user profile with progress stats since last promotion."""
        profile = self.repo.get(user_id)
        if not profile:
            return None

        # Calculate sessions and hours since last belt promotion
        from rivaflow.db.repositories.grading_repo import GradingRepository
        from rivaflow.db.repositories.session_repo import SessionRepository
        from datetime import date

        grading_repo = GradingRepository()
        session_repo = SessionRepository()

        latest_grading = grading_repo.get_latest(user_id)

        if latest_grading and latest_grading.get('date_graded'):
            # Always sync current_grade from latest grading
            profile['current_grade'] = latest_grading.get('grade', 'White')

            # Get sessions since last grading date
            grading_date_str = latest_grading['date_graded']
            if isinstance(grading_date_str, str):
                grading_date = date.fromisoformat(grading_date_str)
            else:
                grading_date = grading_date_str

            today = date.today()
            sessions_since_promotion = session_repo.get_by_date_range(user_id, grading_date, today)

            total_sessions_since = len(sessions_since_promotion)
            total_hours_since = sum(s.get('duration_mins', 0) for s in sessions_since_promotion) / 60

            profile['sessions_since_promotion'] = total_sessions_since
            profile['hours_since_promotion'] = round(total_hours_since, 1)
            profile['promotion_date'] = grading_date_str
        else:
            # No promotion yet, count all sessions
            all_sessions = session_repo.get_by_date_range(user_id, date(2020, 1, 1), date.today())
            profile['sessions_since_promotion'] = len(all_sessions)
            profile['hours_since_promotion'] = round(sum(s.get('duration_mins', 0) for s in all_sessions) / 60, 1)
            profile['promotion_date'] = None

        return profile

    def update_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        sex: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        default_gym: Optional[str] = None,
        default_location: Optional[str] = None,
        current_grade: Optional[str] = None,
        current_professor: Optional[str] = None,
        current_instructor_id: Optional[int] = None,
        primary_training_type: Optional[str] = None,
        height_cm: Optional[int] = None,
        target_weight_kg: Optional[float] = None,
        weekly_sessions_target: Optional[int] = None,
        weekly_hours_target: Optional[float] = None,
        weekly_rolls_target: Optional[int] = None,
        weekly_bjj_sessions_target: Optional[int] = None,
        weekly_sc_sessions_target: Optional[int] = None,
        weekly_mobility_sessions_target: Optional[int] = None,
        show_streak_on_dashboard: Optional[bool] = None,
        show_weekly_goals: Optional[bool] = None,
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
        )

    def get_default_gym(self, user_id: int) -> Optional[str]:
        """Get the default gym from profile."""
        profile = self.get_profile(user_id)
        return profile.get("default_gym") if profile else None

    def get_current_professor(self, user_id: int) -> Optional[str]:
        """Get the current professor from profile."""
        profile = self.get_profile(user_id)
        return profile.get("current_professor") if profile else None

    def upload_profile_photo(
        self,
        user_id: int,
        file_content: bytes,
        filename: str
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
                details={"allowed_extensions": list(self.ALLOWED_EXTENSIONS)}
            )

        # Validate file size
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024 * 1024)}MB",
                details={"max_size_mb": self.MAX_FILE_SIZE // (1024 * 1024)}
            )

        # Generate unique filename: user_{user_id}_{timestamp}_{uuid}.{ext}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"user_{user_id}_{timestamp}_{unique_id}{file_ext}"
        file_path = self.upload_dir / new_filename

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Set secure file permissions (user read/write only)
        os.chmod(file_path, 0o600)

        # Update user's avatar_url in database
        avatar_url = f"/uploads/avatars/{new_filename}"
        self.user_repo.update_avatar(user_id, avatar_url)

        return {
            "avatar_url": avatar_url,
            "filename": new_filename,
            "message": "Profile photo uploaded successfully"
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

        # Extract filename from URL (format: /uploads/avatars/filename.jpg)
        if avatar_url.startswith("/uploads/avatars/"):
            filename = avatar_url.replace("/uploads/avatars/", "")
            file_path = self.upload_dir / filename

            # Delete file if it exists
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception as e:
                    # Log error but continue to clear database entry
                    # In production, this should use proper logging
                    print(f"Warning: Error deleting file {file_path}: {e}")

        # Clear avatar_url in database
        self.user_repo.update_avatar(user_id, None)

        return {"message": "Profile photo deleted successfully"}
