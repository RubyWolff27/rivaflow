"""Privacy redaction and sharing controls service."""
from typing import Optional, List, Dict, Any


class PrivacyService:
    """Enforce privacy levels and redaction rules.

    Privacy Levels:
    - private: Never share (returns None)
    - attendance: Only gym/location/date/class_type (no training details)
    - summary: Include duration/intensity/rolls count (no specifics)
    - full: Share everything

    This service implements "privacy-by-default" and granular redaction
    to prepare for social features ("Strava for martial arts").
    """

    # Define what fields are included at each visibility level
    ATTENDANCE_FIELDS = {
        "session_date",
        "class_type",
        "gym_name",
        "location",
    }

    SUMMARY_FIELDS = ATTENDANCE_FIELDS | {
        "duration_mins",
        "intensity",
        "rolls",  # Count only, no details
    }

    # Fields that contain sensitive training details (never in attendance/summary)
    SENSITIVE_FIELDS = {
        "techniques",
        "partners",
        "notes",
        "submissions_for",
        "submissions_against",
        "detailed_rolls",
        "session_techniques",
        "whoop_strain",
        "whoop_calories",
        "whoop_avg_hr",
        "whoop_max_hr",
    }

    @staticmethod
    def redact_session(
        session: Dict[str, Any],
        visibility: str = "private",
        audience_scope: Optional[str] = None,
        share_fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Redact session based on privacy settings.

        Args:
            session: Full session dictionary
            visibility: "private" | "attendance" | "summary" | "full"
            audience_scope: Optional scope (for future: "partners" | "circle" | "gym" | "public")
            share_fields: Optional list of additional fields to include (overrides visibility)

        Returns:
            Redacted session dict or None if private

        Examples:
            >>> session = {"gym_name": "Alliance", "techniques": ["armbar"], "notes": "Great"}
            >>> PrivacyService.redact_session(session, "attendance")
            {"gym_name": "Alliance", "session_date": "...", "class_type": "gi"}

            >>> PrivacyService.redact_session(session, "private")
            None
        """
        if visibility == "private":
            return None  # Never share private sessions

        # Start with empty dict
        redacted = {}

        if visibility == "attendance":
            # Only attendance metadata (who/what/when/where)
            for field in PrivacyService.ATTENDANCE_FIELDS:
                if field in session:
                    redacted[field] = session[field]

        elif visibility == "summary":
            # Include summary stats (no specifics)
            for field in PrivacyService.SUMMARY_FIELDS:
                if field in session:
                    redacted[field] = session[field]

        elif visibility == "full":
            # Include everything
            redacted = session.copy()

        else:
            raise ValueError(f"Invalid visibility level: {visibility}")

        # Apply share_fields overrides (granular control)
        if share_fields:
            for field in share_fields:
                if field in session:
                    redacted[field] = session[field]

        # Always include id and visibility level for reference
        if "id" in session:
            redacted["id"] = session["id"]
        redacted["visibility_level"] = visibility

        return redacted

    @staticmethod
    def redact_sessions_list(
        sessions: List[Dict[str, Any]],
        default_visibility: str = "private",
    ) -> List[Dict[str, Any]]:
        """Redact a list of sessions based on their individual visibility settings.

        Args:
            sessions: List of session dictionaries
            default_visibility: Fallback visibility if not specified per session

        Returns:
            List of redacted sessions (private sessions excluded)
        """
        redacted_list = []

        for session in sessions:
            visibility = session.get("visibility_level", default_visibility)
            audience_scope = session.get("audience_scope")
            share_fields_json = session.get("share_fields")

            # Parse share_fields if JSON string
            share_fields = None
            if share_fields_json:
                import json
                try:
                    share_fields = json.loads(share_fields_json) if isinstance(share_fields_json, str) else share_fields_json
                except (json.JSONDecodeError, TypeError):
                    pass

            redacted = PrivacyService.redact_session(
                session,
                visibility=visibility,
                audience_scope=audience_scope,
                share_fields=share_fields,
            )

            if redacted:  # Exclude private sessions (None)
                redacted_list.append(redacted)

        return redacted_list

    @staticmethod
    def enforce_audience_scope(
        session: Dict[str, Any],
        viewer_id: Optional[int],
        viewer_relationships: Optional[Dict[str, bool]] = None,
    ) -> bool:
        """Check if viewer is in session's audience scope.

        This is for future social features. Currently returns True (no enforcement).

        Args:
            session: Session dictionary with audience_scope field
            viewer_id: ID of user attempting to view
            viewer_relationships: Dict of {
                "is_training_partner": bool,
                "is_following": bool,
                "is_same_gym": bool,
            }

        Returns:
            True if viewer is allowed to see session, False otherwise

        Future Implementation:
            - "private": Only session owner
            - "partners": Training partners only (check partner consent table)
            - "circle": Followers only (check follows table)
            - "gym": Same gym members (check club memberships)
            - "public": Everyone
        """
        audience_scope = session.get("audience_scope")

        if not audience_scope or audience_scope == "public":
            return True  # Public sessions visible to all

        # TODO: Implement relationship checks when social features added
        # For now, allow all (single-user app)
        return True

    @staticmethod
    def validate_share_fields(share_fields: List[str]) -> List[str]:
        """Validate and filter share_fields list.

        Ensures athletes can't accidentally share sensitive fields
        via share_fields override without explicit intent.

        Args:
            share_fields: List of field names to share

        Returns:
            Filtered list with only valid, non-sensitive overrides
        """
        # Allow only non-sensitive extensions to base visibility
        safe_extensions = {
            "instructor_name",
            "instructor_id",
            "created_at",
            "updated_at",
        }

        return [f for f in share_fields if f in safe_extensions]

    @staticmethod
    def get_privacy_recommendation(
        session: Dict[str, Any],
    ) -> Dict[str, str]:
        """Get privacy recommendation for session based on content.

        Helps athletes choose appropriate visibility level.

        Returns:
            {
                "recommended": "attendance" | "summary" | "full",
                "reason": "Explanation for recommendation",
            }
        """
        has_notes = bool(session.get("notes"))
        has_techniques = bool(session.get("techniques") or session.get("session_techniques"))
        has_partners = bool(session.get("partners"))
        has_detailed_rolls = bool(session.get("detailed_rolls"))

        # Recommend more restrictive levels if sensitive content exists
        if has_notes or has_detailed_rolls:
            return {
                "recommended": "summary",
                "reason": "Session contains personal notes or detailed roll data",
            }

        if has_techniques or has_partners:
            return {
                "recommended": "summary",
                "reason": "Session includes technique details or training partners",
            }

        # Simple session: just attended class
        return {
            "recommended": "attendance",
            "reason": "Basic attendance share (gym, date, class type only)",
        }


# Convenience functions for common use cases

def redact_for_export(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Redact sessions for CSV export (respects individual privacy settings)."""
    return PrivacyService.redact_sessions_list(sessions)


def redact_for_feed(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Redact session for activity feed display (future social feature)."""
    visibility = session.get("visibility_level", "private")
    return PrivacyService.redact_session(session, visibility=visibility)


def is_shareable(session: Dict[str, Any]) -> bool:
    """Check if session is shareable (not private)."""
    visibility = session.get("visibility_level", "private")
    return visibility != "private"
