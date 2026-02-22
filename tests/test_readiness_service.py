"""Unit tests for ReadinessService — readiness scoring and check-ins."""

from datetime import date
from unittest.mock import patch

from rivaflow.core.services.readiness_service import ReadinessService


class TestLogReadiness:
    """Tests for log_readiness."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_creates_readiness_and_checkin(self, MockRepo, MockCheckinRepo):
        """Should upsert readiness and create a checkin record."""
        MockRepo.return_value.upsert.return_value = 42

        service = ReadinessService()
        result = service.log_readiness(
            user_id=1,
            check_date=date(2025, 1, 20),
            sleep=4,
            stress=3,
            soreness=2,
            energy=4,
            hotspot_note="left knee",
        )

        assert result == 42
        MockRepo.return_value.upsert.assert_called_once_with(
            user_id=1,
            check_date=date(2025, 1, 20),
            sleep=4,
            stress=3,
            soreness=2,
            energy=4,
            hotspot_note="left knee",
            weight_kg=None,
            hrv_ms=None,
            resting_hr=None,
            spo2=None,
            whoop_recovery_score=None,
            whoop_sleep_score=None,
            data_source=None,
        )
        MockCheckinRepo.return_value.upsert_checkin.assert_called_once_with(
            user_id=1,
            check_date=date(2025, 1, 20),
            checkin_type="readiness",
            readiness_id=42,
        )

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_passes_optional_fields(self, MockRepo, MockCheckinRepo):
        """Should pass optional biometric fields to repo."""
        MockRepo.return_value.upsert.return_value = 43

        service = ReadinessService()
        service.log_readiness(
            user_id=1,
            check_date=date(2025, 1, 20),
            sleep=4,
            stress=3,
            soreness=2,
            energy=4,
            weight_kg=85.5,
            hrv_ms=55.0,
            resting_hr=58,
        )

        call_kwargs = MockRepo.return_value.upsert.call_args[1]
        assert call_kwargs["weight_kg"] == 85.5
        assert call_kwargs["hrv_ms"] == 55.0
        assert call_kwargs["resting_hr"] == 58


class TestGetReadiness:
    """Tests for get_readiness."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_returns_readiness_for_date(self, MockRepo, MockCheckinRepo):
        """Should return readiness entry for specific date."""
        mock_entry = {
            "id": 1,
            "check_date": "2025-01-20",
            "sleep": 4,
            "stress": 3,
            "soreness": 2,
            "energy": 4,
        }
        MockRepo.return_value.get_by_date.return_value = mock_entry

        service = ReadinessService()
        result = service.get_readiness(user_id=1, check_date=date(2025, 1, 20))

        assert result == mock_entry

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_returns_none_when_no_entry(self, MockRepo, MockCheckinRepo):
        """Should return None when no entry exists."""
        MockRepo.return_value.get_by_date.return_value = None

        service = ReadinessService()
        result = service.get_readiness(user_id=1, check_date=date(2025, 1, 20))
        assert result is None


class TestGetLatestReadiness:
    """Tests for get_latest_readiness."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_returns_latest(self, MockRepo, MockCheckinRepo):
        """Should return most recent readiness entry."""
        mock_entry = {"id": 5, "check_date": "2025-01-25"}
        MockRepo.return_value.get_latest.return_value = mock_entry

        service = ReadinessService()
        result = service.get_latest_readiness(user_id=1)

        assert result == mock_entry


class TestGetReadinessRange:
    """Tests for get_readiness_range."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_returns_range(self, MockRepo, MockCheckinRepo):
        """Should return entries within date range."""
        mock_entries = [
            {"id": 1, "check_date": "2025-01-20"},
            {"id": 2, "check_date": "2025-01-21"},
        ]
        MockRepo.return_value.get_by_date_range.return_value = mock_entries

        service = ReadinessService()
        result = service.get_readiness_range(
            user_id=1,
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 25),
        )

        assert len(result) == 2


class TestLogWeightOnly:
    """Tests for log_weight_only."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_updates_existing_entry(self, MockRepo, MockCheckinRepo):
        """Should update weight on existing readiness entry."""
        existing = {
            "sleep": 4,
            "stress": 3,
            "soreness": 2,
            "energy": 4,
            "hotspot_note": "sore neck",
        }
        MockRepo.return_value.get_by_date.return_value = existing
        MockRepo.return_value.upsert.return_value = 42

        service = ReadinessService()
        result = service.log_weight_only(
            user_id=1, check_date=date(2025, 1, 20), weight_kg=85.0
        )

        assert result == 42
        # Should preserve existing readiness scores
        call_kwargs = MockRepo.return_value.upsert.call_args[1]
        assert call_kwargs["sleep"] == 4
        assert call_kwargs["weight_kg"] == 85.0

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_creates_new_entry_with_defaults(self, MockRepo, MockCheckinRepo):
        """Should create new entry with middle values when no existing."""
        MockRepo.return_value.get_by_date.return_value = None
        MockRepo.return_value.upsert.return_value = 43

        service = ReadinessService()
        result = service.log_weight_only(
            user_id=1, check_date=date(2025, 1, 20), weight_kg=85.0
        )

        assert result == 43
        call_kwargs = MockRepo.return_value.upsert.call_args[1]
        assert call_kwargs["sleep"] == 3
        assert call_kwargs["stress"] == 3
        assert call_kwargs["soreness"] == 3
        assert call_kwargs["energy"] == 3
        assert call_kwargs["weight_kg"] == 85.0


class TestCalculateCompositeScore:
    """Tests for calculate_composite_score."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_max_score(self, MockRepo, MockCheckinRepo):
        """Maximum readiness should score 20."""
        service = ReadinessService()
        readiness = {"sleep": 5, "stress": 1, "soreness": 1, "energy": 5}
        assert service.calculate_composite_score(readiness) == 20

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_min_score(self, MockRepo, MockCheckinRepo):
        """Minimum readiness should score 4."""
        service = ReadinessService()
        readiness = {"sleep": 1, "stress": 5, "soreness": 5, "energy": 1}
        assert service.calculate_composite_score(readiness) == 4

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_middle_score(self, MockRepo, MockCheckinRepo):
        """Middle values should score 12."""
        service = ReadinessService()
        readiness = {"sleep": 3, "stress": 3, "soreness": 3, "energy": 3}
        # 3 + (6-3) + (6-3) + 3 = 3 + 3 + 3 + 3 = 12
        assert service.calculate_composite_score(readiness) == 12


class TestGetScoreLabel:
    """Tests for get_score_label."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_excellent_score(self, MockRepo, MockCheckinRepo):
        """Score >= 17 should be Excellent."""
        service = ReadinessService()
        assert service.get_score_label(17) == "Excellent"
        assert service.get_score_label(20) == "Excellent"

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_good_score(self, MockRepo, MockCheckinRepo):
        """Score 14-16 should be Good."""
        service = ReadinessService()
        assert service.get_score_label(14) == "Good"
        assert service.get_score_label(16) == "Good"

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_moderate_score(self, MockRepo, MockCheckinRepo):
        """Score 11-13 should be Moderate."""
        service = ReadinessService()
        assert service.get_score_label(11) == "Moderate"
        assert service.get_score_label(13) == "Moderate"

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_low_score(self, MockRepo, MockCheckinRepo):
        """Score 8-10 should be Low."""
        service = ReadinessService()
        assert service.get_score_label(8) == "Low"
        assert service.get_score_label(10) == "Low"

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_very_low_score(self, MockRepo, MockCheckinRepo):
        """Score < 8 should be Very Low."""
        service = ReadinessService()
        assert service.get_score_label(4) == "Very Low"
        assert service.get_score_label(7) == "Very Low"


class TestFormatReadinessSummary:
    """Tests for format_readiness_summary."""

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_includes_all_fields(self, MockRepo, MockCheckinRepo):
        """Should include all readiness fields in summary."""
        service = ReadinessService()
        readiness = {
            "check_date": "2025-01-20",
            "sleep": 4,
            "stress": 2,
            "soreness": 2,
            "energy": 4,
            "hotspot_note": "left shoulder",
        }

        summary = service.format_readiness_summary(readiness)

        assert "2025-01-20" in summary
        assert "Hotspot: left shoulder" in summary

    @patch("rivaflow.core.services.readiness_service.CheckinRepository")
    @patch("rivaflow.core.services.readiness_service.ReadinessRepository")
    def test_no_hotspot(self, MockRepo, MockCheckinRepo):
        """Should omit hotspot line when none."""
        service = ReadinessService()
        readiness = {
            "check_date": "2025-01-20",
            "sleep": 3,
            "stress": 3,
            "soreness": 3,
            "energy": 3,
        }

        summary = service.format_readiness_summary(readiness)

        assert "Hotspot" not in summary
