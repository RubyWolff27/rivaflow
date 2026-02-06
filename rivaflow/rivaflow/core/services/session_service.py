"""Service layer for training session operations."""

from datetime import date
from typing import Any

from rivaflow.config import SPARRING_CLASS_TYPES
from rivaflow.db.repositories import (
    SessionRepository,
    SessionRollRepository,
    TechniqueRepository,
)
from rivaflow.db.repositories.checkin_repo import CheckinRepository
from rivaflow.db.repositories.glossary_repo import GlossaryRepository
from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository


class SessionService:
    """Business logic for training sessions."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.technique_repo = TechniqueRepository()
        self.roll_repo = SessionRollRepository()
        self.technique_detail_repo = SessionTechniqueRepository()
        self.checkin_repo = CheckinRepository()
        self.glossary_repo = GlossaryRepository()

    def create_session(
        self,
        user_id: int,
        session_date: date,
        class_type: str,
        gym_name: str,
        location: str | None = None,
        class_time: str | None = None,
        duration_mins: int = 60,
        intensity: int = 4,
        rolls: int = 0,
        submissions_for: int = 0,
        submissions_against: int = 0,
        partners: list[str] | None = None,
        techniques: list[str] | None = None,
        notes: str | None = None,
        visibility_level: str = "private",
        instructor_id: int | None = None,
        instructor_name: str | None = None,
        session_rolls: list[dict[str, Any]] | None = None,
        session_techniques: list[dict[str, Any]] | None = None,
        whoop_strain: float | None = None,
        whoop_calories: int | None = None,
        whoop_avg_hr: int | None = None,
        whoop_max_hr: int | None = None,
        attacks_attempted: int = 0,
        attacks_successful: int = 0,
        defenses_attempted: int = 0,
        defenses_successful: int = 0,
    ) -> int:
        """
        Create a new training session and update technique tracking.
        Supports both simple mode (aggregate counts) and detailed mode (individual rolls).
        Returns session ID.
        """
        # Create session
        session_id = self.session_repo.create(
            user_id=user_id,
            session_date=session_date,
            class_time=class_time,
            class_type=class_type,
            gym_name=gym_name,
            location=location,
            duration_mins=duration_mins,
            intensity=intensity,
            rolls=rolls,
            submissions_for=submissions_for,
            submissions_against=submissions_against,
            partners=partners,
            techniques=techniques,
            notes=notes,
            visibility_level=visibility_level,
            instructor_id=instructor_id,
            instructor_name=instructor_name,
            whoop_strain=whoop_strain,
            whoop_calories=whoop_calories,
            whoop_avg_hr=whoop_avg_hr,
            whoop_max_hr=whoop_max_hr,
            attacks_attempted=attacks_attempted,
            attacks_successful=attacks_successful,
            defenses_attempted=defenses_attempted,
            defenses_successful=defenses_successful,
        )

        # Create detailed roll records if provided
        if session_rolls:
            for roll_data in session_rolls:
                self.roll_repo.create(
                    user_id=user_id,
                    session_id=session_id,
                    roll_number=roll_data.get("roll_number", 1),
                    partner_id=roll_data.get("partner_id"),
                    partner_name=roll_data.get("partner_name"),
                    duration_mins=roll_data.get("duration_mins"),
                    submissions_for=roll_data.get("submissions_for"),
                    submissions_against=roll_data.get("submissions_against"),
                    notes=roll_data.get("notes"),
                )

        # Create detailed technique records if provided
        if session_techniques:
            for tech_data in session_techniques:
                self.technique_detail_repo.create(
                    user_id=user_id,
                    session_id=session_id,
                    movement_id=tech_data.get("movement_id"),
                    technique_number=tech_data.get("technique_number", 1),
                    notes=tech_data.get("notes"),
                    media_urls=tech_data.get("media_urls"),
                )

                # Also update the techniques table with movement name
                movement_id = tech_data.get("movement_id")
                if movement_id:
                    movement = self.glossary_repo.get_by_id(movement_id)
                    if movement:
                        tech = self.technique_repo.get_or_create(movement["name"])
                        self.technique_repo.update_last_trained(
                            tech["id"], session_date
                        )

        # Update technique last_trained_date (from simple techniques field)
        if techniques:
            for tech_name in techniques:
                tech = self.technique_repo.get_or_create(tech_name)
                self.technique_repo.update_last_trained(tech["id"], session_date)

        # Create check-in record for this session
        self.checkin_repo.upsert_checkin(
            user_id=user_id,
            check_date=session_date,
            checkin_type="session",
            session_id=session_id,
        )

        return session_id

    def get_session(self, user_id: int, session_id: int) -> dict[str, Any] | None:
        """Get a session by ID."""
        return self.session_repo.get_by_id(user_id, session_id)

    def get_adjacent_sessions(self, user_id: int, session_id: int) -> dict[str, Any]:
        """
        Get the previous and next session IDs for navigation.

        Args:
            user_id: User ID
            session_id: Current session ID

        Returns:
            Dict with previous_session_id and next_session_id (or None if at boundaries)
        """
        # Get current session to find its date
        current_session = self.session_repo.get_by_id(user_id, session_id)
        if not current_session:
            return {"previous_session_id": None, "next_session_id": None}

        current_session["session_date"]
        current_session.get("created_at")

        # Get all sessions ordered by date DESC, created_at DESC (newest first)
        all_sessions = self.session_repo.get_recent(user_id, limit=10000)

        # Find current session index
        current_index = None
        for i, session in enumerate(all_sessions):
            if session["id"] == session_id:
                current_index = i
                break

        if current_index is None:
            return {"previous_session_id": None, "next_session_id": None}

        # Previous session is the one after current (older, later in list)
        previous_session_id = (
            all_sessions[current_index + 1]["id"]
            if current_index + 1 < len(all_sessions)
            else None
        )

        # Next session is the one before current (newer, earlier in list)
        next_session_id = (
            all_sessions[current_index - 1]["id"] if current_index > 0 else None
        )

        return {
            "previous_session_id": previous_session_id,
            "next_session_id": next_session_id,
        }

    def update_session(
        self,
        user_id: int,
        session_id: int,
        session_techniques: list[dict] | None = None,
        **kwargs,
    ) -> dict | None:
        """
        Update a training session and refresh technique tracking.

        Args:
            user_id: User ID for authorization
            session_id: Session ID to update
            session_techniques: Optional list of technique detail dicts
            **kwargs: Session fields to update (session_date, class_type, intensity, etc.)

        Returns:
            Updated session dict or None if not found

        Example:
            update_session(user_id=1, session_id=123, intensity=5, notes="Great!")
        """
        # Get original session to compare techniques
        original = self.session_repo.get_by_id(user_id, session_id)
        if not original:
            return None

        # Update session (pass all kwargs to repo)
        updated = self.session_repo.update(
            user_id=user_id, session_id=session_id, **kwargs
        )

        if not updated:
            return None

        # Update detailed technique records if provided
        if session_techniques is not None:
            # Delete existing technique records
            self.technique_detail_repo.delete_by_session(session_id)
            # Create new technique records
            # Use the session date from the updated session (which includes any changes from kwargs)
            updated_date = updated["session_date"]
            for tech_data in session_techniques:
                self.technique_detail_repo.create(
                    user_id=user_id,
                    session_id=session_id,
                    movement_id=tech_data.get("movement_id"),
                    technique_number=tech_data.get("technique_number", 1),
                    notes=tech_data.get("notes"),
                    media_urls=tech_data.get("media_urls"),
                )

                # Also update the techniques table with movement name
                movement_id = tech_data.get("movement_id")
                if movement_id:
                    movement = self.glossary_repo.get_by_id(movement_id)
                    if movement:
                        tech = self.technique_repo.get_or_create(movement["name"])
                        self.technique_repo.update_last_trained(
                            tech["id"], updated_date
                        )

        # Update technique last_trained_date if techniques changed (from simple techniques field)
        techniques = kwargs.get("techniques")
        if techniques is not None:
            # Use the session date from the updated session
            updated_date = updated["session_date"]
            for tech_name in techniques:
                tech = self.technique_repo.get_or_create(tech_name)
                self.technique_repo.update_last_trained(tech["id"], updated_date)

        return updated

    def delete_session(self, user_id: int, session_id: int) -> bool:
        """Delete a session by ID. Returns True if deleted, False if not found."""
        return self.session_repo.delete(user_id, session_id)

    def get_sessions_by_date_range(
        self, user_id: int, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Get sessions within a date range."""
        return self.session_repo.get_by_date_range(user_id, start_date, end_date)

    def get_recent_sessions(
        self, user_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get most recent sessions."""
        return self.session_repo.get_recent(user_id, limit)

    def get_autocomplete_data(self, user_id: int) -> dict[str, Any]:
        """Get data for autocomplete suggestions."""
        return {
            "gyms": self.session_repo.get_unique_gyms(user_id),
            "locations": self.session_repo.get_unique_locations(user_id),
            "partners": self.session_repo.get_unique_partners(user_id),
            "techniques": self.technique_repo.get_unique_names(),  # Techniques are global
        }

    def get_consecutive_class_type_count(self, user_id: int) -> dict[str, int]:
        """
        Count consecutive sessions of same type from most recent.
        Returns dict with 'gi' and 'no-gi' counts.
        """
        recent_types = self.session_repo.get_last_n_sessions_by_type(user_id, 10)
        counts = {"gi": 0, "no-gi": 0}

        if not recent_types:
            return counts

        # Count consecutive from most recent
        last_type = recent_types[0]
        if last_type not in ["gi", "no-gi"]:
            return counts

        for class_type in recent_types:
            if class_type == last_type:
                if class_type == "gi":
                    counts["gi"] += 1
                elif class_type == "no-gi":
                    counts["no-gi"] += 1
            else:
                break

        return counts

    def is_sparring_class(self, class_type: str) -> bool:
        """Check if a class type requires sparring/rolls."""
        return class_type in SPARRING_CLASS_TYPES

    def format_session_summary(self, session: dict[str, Any]) -> str:
        """Format a session as a human-readable summary."""
        lines = [
            f"Session logged: {session['session_date']}",
            f"  Type: {session['class_type']}",
            f"  Gym: {session['gym_name']}",
        ]

        if session.get("location"):
            lines.append(f"  Location: {session['location']}")

        lines.append(f"  Duration: {session['duration_mins']} mins")
        lines.append(
            f"  Intensity: {'█' * session['intensity']}{'░' * (5 - session['intensity'])} {session['intensity']}/5"
        )

        if session["rolls"] > 0:
            lines.append(f"  Rolls: {session['rolls']}")
            lines.append(
                f"  Subs for: {session['submissions_for']} | against: {session['submissions_against']}"
            )

        if session.get("partners"):
            lines.append(f"  Partners: {', '.join(session['partners'])}")

        if session.get("techniques"):
            lines.append(f"  Techniques: {', '.join(session['techniques'])}")

        if session.get("notes"):
            lines.append(f"  Notes: {session['notes']}")

        return "\n".join(lines)

    def get_session_with_rolls(
        self, user_id: int, session_id: int
    ) -> dict[str, Any] | None:
        """Get a session with detailed roll records included."""
        session = self.session_repo.get_by_id(user_id, session_id)
        if not session:
            return None

        # Fetch detailed rolls
        rolls = self.roll_repo.get_by_session_id(user_id, session_id)
        session["detailed_rolls"] = rolls

        return session

    def get_session_with_details(
        self, user_id: int, session_id: int
    ) -> dict[str, Any] | None:
        """
        Get a session with all related data eagerly loaded (rolls, techniques, media, comments, likes).
        This avoids N+1 queries when displaying session detail views.
        """
        from rivaflow.db.repositories.activity_comment_repo import (
            ActivityCommentRepository,
        )
        from rivaflow.db.repositories.activity_like_repo import ActivityLikeRepository

        session = self.session_repo.get_by_id(user_id, session_id)
        if not session:
            return None

        # Eagerly load all related data
        session["detailed_rolls"] = self.roll_repo.get_by_session_id(
            user_id, session_id
        )
        session["detailed_techniques"] = self.technique_detail_repo.get_by_session_id(
            session_id
        )

        # Load social engagement data
        session["likes"] = ActivityLikeRepository.get_by_activity("session", session_id)
        session["comments"] = ActivityCommentRepository.get_by_activity(
            "session", session_id
        )
        session["like_count"] = len(session["likes"])
        session["comment_count"] = len(session["comments"])
        session["has_liked"] = ActivityLikeRepository.has_user_liked(
            user_id, "session", session_id
        )

        return session

    def get_partner_stats(self, user_id: int, partner_id: int) -> dict[str, Any]:
        """Get analytics for a specific training partner."""
        return self.roll_repo.get_partner_stats(user_id, partner_id)
