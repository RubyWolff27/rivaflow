"""Unit tests for PrivacyService redaction logic."""
import pytest

from rivaflow.core.services.privacy_service import PrivacyService


class TestPrivacyRedaction:
    """Test privacy redaction at different visibility levels."""

    def setup_method(self):
        """Create a sample session with all fields."""
        self.full_session = {
            "id": 123,
            "session_date": "2025-01-25",
            "class_type": "gi",
            "gym_name": "Alliance BJJ",
            "location": "San Diego, CA",
            "duration_mins": 90,
            "intensity": 4,
            "rolls": 5,
            "submissions_for": 3,
            "submissions_against": 1,
            "partners": ["Alice", "Bob"],
            "techniques": ["armbar", "triangle"],
            "notes": "Great class, worked on guard passing",
            "whoop_strain": 15.2,
            "visibility_level": "full",
        }

    def test_private_returns_none(self):
        """Verify private sessions return None (never shared)."""
        result = PrivacyService.redact_session(self.full_session, visibility="private")
        assert result is None

    def test_attendance_includes_only_metadata(self):
        """Verify attendance level includes only gym/date/type/location."""
        result = PrivacyService.redact_session(self.full_session, visibility="attendance")

        # Should include attendance fields
        assert "gym_name" in result
        assert "session_date" in result
        assert "class_type" in result
        assert "location" in result
        assert result["gym_name"] == "Alliance BJJ"

        # Should NOT include sensitive training details
        assert "techniques" not in result
        assert "partners" not in result
        assert "notes" not in result
        assert "submissions_for" not in result
        assert "submissions_against" not in result
        assert "whoop_strain" not in result

        # Should include id and visibility for reference
        assert result["id"] == 123
        assert result["visibility_level"] == "attendance"

    def test_summary_includes_stats_not_specifics(self):
        """Verify summary level includes duration/intensity/rolls but not details."""
        result = PrivacyService.redact_session(self.full_session, visibility="summary")

        # Should include attendance fields
        assert "gym_name" in result
        assert "session_date" in result
        assert "class_type" in result

        # Should include summary stats
        assert "duration_mins" in result
        assert "intensity" in result
        assert "rolls" in result
        assert result["duration_mins"] == 90
        assert result["intensity"] == 4
        assert result["rolls"] == 5

        # Should NOT include training specifics
        assert "techniques" not in result
        assert "partners" not in result
        assert "notes" not in result
        assert "submissions_for" not in result  # No sub counts in summary
        assert "submissions_against" not in result

    def test_full_includes_everything(self):
        """Verify full visibility returns complete session."""
        result = PrivacyService.redact_session(self.full_session, visibility="full")

        # Should include all fields
        assert "gym_name" in result
        assert "techniques" in result
        assert "partners" in result
        assert "notes" in result
        assert "submissions_for" in result
        assert result["notes"] == "Great class, worked on guard passing"

    def test_missing_optional_fields_handled(self):
        """Verify redaction works when optional fields are missing."""
        minimal_session = {
            "id": 456,
            "session_date": "2025-01-25",
            "class_type": "no-gi",
            "gym_name": "Gracie Barra",
            "duration_mins": 60,
            "intensity": 3,
            "rolls": 0,
        }

        result = PrivacyService.redact_session(minimal_session, visibility="summary")

        assert result["gym_name"] == "Gracie Barra"
        assert result["rolls"] == 0
        assert "techniques" not in result
        assert "notes" not in result

    def test_invalid_visibility_raises_error(self):
        """Verify invalid visibility level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid visibility level"):
            PrivacyService.redact_session(self.full_session, visibility="invalid")


class TestShareFieldsOverride:
    """Test share_fields granular control."""

    def test_share_fields_adds_to_base_visibility(self):
        """Verify share_fields can extend base visibility level."""
        session = {
            "gym_name": "Alliance",
            "session_date": "2025-01-25",
            "class_type": "gi",
            "instructor_name": "Professor Jones",
            "techniques": ["armbar"],
        }

        result = PrivacyService.redact_session(
            session,
            visibility="attendance",
            share_fields=["instructor_name"],  # Add instructor to attendance
        )

        # Should include attendance fields + instructor
        assert "gym_name" in result
        assert "instructor_name" in result
        assert result["instructor_name"] == "Professor Jones"

        # Should still not include techniques (not in share_fields)
        assert "techniques" not in result


class TestSessionsListRedaction:
    """Test batch redaction of session lists."""

    def test_redact_sessions_list(self):
        """Verify list redaction respects individual visibility settings."""
        sessions = [
            {"id": 1, "gym_name": "Gym A", "session_date": "2025-01-20", "class_type": "gi", "notes": "Secret", "visibility_level": "private"},
            {"id": 2, "gym_name": "Gym B", "session_date": "2025-01-21", "class_type": "no-gi", "notes": "Public", "visibility_level": "attendance"},
            {"id": 3, "gym_name": "Gym C", "session_date": "2025-01-22", "class_type": "gi", "notes": "Details", "visibility_level": "summary", "duration_mins": 60, "intensity": 4, "rolls": 5},
        ]

        result = PrivacyService.redact_sessions_list(sessions)

        # Should exclude private session
        assert len(result) == 2
        assert all(s["id"] != 1 for s in result)

        # Session 2 (attendance) should not have notes
        session_2 = next(s for s in result if s["id"] == 2)
        assert "gym_name" in session_2
        assert "notes" not in session_2

        # Session 3 (summary) should have duration but not notes
        session_3 = next(s for s in result if s["id"] == 3)
        assert "duration_mins" in session_3
        assert "notes" not in session_3

    def test_default_visibility_applied(self):
        """Verify default visibility used when not specified per session."""
        sessions = [
            {"id": 1, "gym_name": "Gym A", "session_date": "2025-01-20", "class_type": "gi", "notes": "No visibility set"},
        ]

        # Default to attendance
        result = PrivacyService.redact_sessions_list(sessions, default_visibility="attendance")

        assert len(result) == 1
        assert "gym_name" in result[0]
        assert "notes" not in result[0]


class TestPrivacyRecommendations:
    """Test privacy level recommendations."""

    def test_recommend_summary_for_notes(self):
        """Verify summary recommended when session has personal notes."""
        session = {
            "gym_name": "Alliance",
            "notes": "Working on knee injury rehab",
        }

        recommendation = PrivacyService.get_privacy_recommendation(session)

        assert recommendation["recommended"] == "summary"
        assert "notes" in recommendation["reason"]

    def test_recommend_summary_for_techniques(self):
        """Verify summary recommended when session has technique details."""
        session = {
            "gym_name": "Alliance",
            "techniques": ["armbar", "triangle"],
        }

        recommendation = PrivacyService.get_privacy_recommendation(session)

        assert recommendation["recommended"] == "summary"
        assert "technique" in recommendation["reason"]

    def test_recommend_attendance_for_simple_session(self):
        """Verify attendance recommended for basic sessions."""
        session = {
            "gym_name": "Alliance",
            "session_date": "2025-01-25",
            "class_type": "gi",
            "duration_mins": 60,
            "intensity": 4,
        }

        recommendation = PrivacyService.get_privacy_recommendation(session)

        assert recommendation["recommended"] == "attendance"
        assert "Basic attendance" in recommendation["reason"]


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    def test_is_shareable(self):
        """Verify is_shareable correctly identifies private sessions."""
        from rivaflow.core.services.privacy_service import is_shareable

        private_session = {"visibility_level": "private"}
        public_session = {"visibility_level": "attendance"}

        assert is_shareable(public_session) is True
        assert is_shareable(private_session) is False

    def test_redact_for_feed(self):
        """Verify redact_for_feed applies session's visibility."""
        from rivaflow.core.services.privacy_service import redact_for_feed

        session = {
            "gym_name": "Alliance",
            "session_date": "2025-01-25",
            "class_type": "gi",
            "techniques": ["armbar"],
            "visibility_level": "attendance",
        }

        result = redact_for_feed(session)

        assert result is not None
        assert "gym_name" in result
        assert "techniques" not in result  # Attendance redaction applied


class TestSensitiveFieldsProtection:
    """Test that sensitive fields are never leaked."""

    def test_sensitive_fields_never_in_attendance(self):
        """Verify all sensitive fields excluded from attendance."""
        session = {
            "gym_name": "Alliance",
            "session_date": "2025-01-25",
            "class_type": "gi",
            "techniques": ["armbar"],
            "partners": ["Alice"],
            "notes": "Secret",
            "submissions_for": 3,
            "submissions_against": 1,
            "whoop_strain": 15.2,
        }

        result = PrivacyService.redact_session(session, visibility="attendance")

        # Verify NO sensitive fields present
        for field in PrivacyService.SENSITIVE_FIELDS:
            assert field not in result, f"Sensitive field '{field}' leaked in attendance mode"

    def test_sensitive_fields_never_in_summary(self):
        """Verify sensitive fields excluded from summary."""
        session = {
            "gym_name": "Alliance",
            "session_date": "2025-01-25",
            "class_type": "gi",
            "duration_mins": 60,
            "intensity": 4,
            "rolls": 5,
            "techniques": ["armbar"],
            "partners": ["Alice"],
            "notes": "Secret",
            "submissions_for": 3,
            "submissions_against": 1,
        }

        result = PrivacyService.redact_session(session, visibility="summary")

        # Verify submission counts excluded from summary
        assert "submissions_for" not in result
        assert "submissions_against" not in result
        assert "techniques" not in result
        assert "partners" not in result
        assert "notes" not in result
