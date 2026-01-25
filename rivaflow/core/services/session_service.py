"""Service layer for training session operations."""
from datetime import date, datetime
from typing import Optional, List

from rivaflow.db.repositories import SessionRepository, TechniqueRepository, SessionRollRepository
from rivaflow.config import SPARRING_CLASS_TYPES


class SessionService:
    """Business logic for training sessions."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.technique_repo = TechniqueRepository()
        self.roll_repo = SessionRollRepository()

    def create_session(
        self,
        session_date: date,
        class_type: str,
        gym_name: str,
        location: Optional[str] = None,
        duration_mins: int = 60,
        intensity: int = 4,
        rolls: int = 0,
        submissions_for: int = 0,
        submissions_against: int = 0,
        partners: Optional[list[str]] = None,
        techniques: Optional[list[str]] = None,
        notes: Optional[str] = None,
        visibility_level: str = "private",
        instructor_id: Optional[int] = None,
        instructor_name: Optional[str] = None,
        session_rolls: Optional[List[dict]] = None,
    ) -> int:
        """
        Create a new training session and update technique tracking.
        Supports both simple mode (aggregate counts) and detailed mode (individual rolls).
        Returns session ID.
        """
        # Create session
        session_id = self.session_repo.create(
            session_date=session_date,
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
        )

        # Create detailed roll records if provided
        if session_rolls:
            for roll_data in session_rolls:
                self.roll_repo.create(
                    session_id=session_id,
                    roll_number=roll_data.get("roll_number", 1),
                    partner_id=roll_data.get("partner_id"),
                    partner_name=roll_data.get("partner_name"),
                    duration_mins=roll_data.get("duration_mins"),
                    submissions_for=roll_data.get("submissions_for"),
                    submissions_against=roll_data.get("submissions_against"),
                    notes=roll_data.get("notes"),
                )

        # Update technique last_trained_date
        if techniques:
            for tech_name in techniques:
                tech = self.technique_repo.get_or_create(tech_name)
                self.technique_repo.update_last_trained(tech["id"], session_date)

        return session_id

    def get_session(self, session_id: int) -> Optional[dict]:
        """Get a session by ID."""
        return self.session_repo.get_by_id(session_id)

    def update_session(
        self,
        session_id: int,
        session_date: Optional[date] = None,
        class_type: Optional[str] = None,
        gym_name: Optional[str] = None,
        location: Optional[str] = None,
        duration_mins: Optional[int] = None,
        intensity: Optional[int] = None,
        rolls: Optional[int] = None,
        submissions_for: Optional[int] = None,
        submissions_against: Optional[int] = None,
        partners: Optional[list[str]] = None,
        techniques: Optional[list[str]] = None,
        notes: Optional[str] = None,
        visibility_level: Optional[str] = None,
        instructor_id: Optional[int] = None,
        instructor_name: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Update a training session and refresh technique tracking.
        Returns updated session or None if not found.
        """
        # Get original session to compare techniques
        original = self.session_repo.get_by_id(session_id)
        if not original:
            return None

        # Update session
        updated = self.session_repo.update(
            session_id=session_id,
            session_date=session_date,
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
        )

        if not updated:
            return None

        # Update technique last_trained_date if techniques changed
        if techniques is not None:
            updated_date = session_date if session_date else original["session_date"]
            for tech_name in techniques:
                tech = self.technique_repo.get_or_create(tech_name)
                self.technique_repo.update_last_trained(tech["id"], updated_date)

        return updated

    def get_sessions_by_date_range(self, start_date: date, end_date: date) -> list[dict]:
        """Get sessions within a date range."""
        return self.session_repo.get_by_date_range(start_date, end_date)

    def get_recent_sessions(self, limit: int = 10) -> list[dict]:
        """Get most recent sessions."""
        return self.session_repo.get_recent(limit)

    def get_autocomplete_data(self) -> dict:
        """Get data for autocomplete suggestions."""
        return {
            "gyms": self.session_repo.get_unique_gyms(),
            "locations": self.session_repo.get_unique_locations(),
            "partners": self.session_repo.get_unique_partners(),
            "techniques": self.technique_repo.get_unique_names(),
        }

    def get_consecutive_class_type_count(self) -> dict[str, int]:
        """
        Count consecutive sessions of same type from most recent.
        Returns dict with 'gi' and 'no-gi' counts.
        """
        recent_types = self.session_repo.get_last_n_sessions_by_type(10)
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

    def format_session_summary(self, session: dict) -> str:
        """Format a session as a human-readable summary."""
        lines = [
            f"Session logged: {session['session_date']}",
            f"  Type: {session['class_type']}",
            f"  Gym: {session['gym_name']}",
        ]

        if session.get("location"):
            lines.append(f"  Location: {session['location']}")

        lines.append(f"  Duration: {session['duration_mins']} mins")
        lines.append(f"  Intensity: {'█' * session['intensity']}{'░' * (5 - session['intensity'])} {session['intensity']}/5")

        if session["rolls"] > 0:
            lines.append(f"  Rolls: {session['rolls']}")
            lines.append(f"  Subs for: {session['submissions_for']} | against: {session['submissions_against']}")

        if session.get("partners"):
            lines.append(f"  Partners: {', '.join(session['partners'])}")

        if session.get("techniques"):
            lines.append(f"  Techniques: {', '.join(session['techniques'])}")

        if session.get("notes"):
            lines.append(f"  Notes: {session['notes']}")

        return "\n".join(lines)

    def get_session_with_rolls(self, session_id: int) -> Optional[dict]:
        """Get a session with detailed roll records included."""
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return None

        # Fetch detailed rolls
        rolls = self.roll_repo.get_by_session_id(session_id)
        session["detailed_rolls"] = rolls

        return session

    def get_partner_stats(self, partner_id: int) -> dict:
        """Get analytics for a specific training partner."""
        return self.roll_repo.get_partner_stats(partner_id)
