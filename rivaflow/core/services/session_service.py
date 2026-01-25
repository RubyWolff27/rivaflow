"""Service layer for training session operations."""
from datetime import date, datetime
from typing import Optional

from rivaflow.db.repositories import SessionRepository, TechniqueRepository
from rivaflow.config import SPARRING_CLASS_TYPES


class SessionService:
    """Business logic for training sessions."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.technique_repo = TechniqueRepository()

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
    ) -> int:
        """
        Create a new training session and update technique tracking.
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
