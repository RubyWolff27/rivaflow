"""Tests for ReportService."""
from datetime import date
from unittest.mock import patch
import tempfile
from pathlib import Path

from rivaflow.core.services.report_service import ReportService
from rivaflow.core.services.session_service import SessionService


def test_get_week_dates(temp_db):
    """Test getting week date range."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = ReportService()

        # Test with a known date (Wednesday, Jan 22, 2025)
        target_date = date(2025, 1, 22)
        start, end = service.get_week_dates(target_date)

        # Should return Monday Jan 20 - Sunday Jan 26
        assert start == date(2025, 1, 20)
        assert end == date(2025, 1, 26)
        assert start.weekday() == 0  # Monday
        assert end.weekday() == 6  # Sunday


def test_get_month_dates(temp_db):
    """Test getting month date range."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = ReportService()

        target_date = date(2025, 1, 15)
        start, end = service.get_month_dates(target_date)

        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)


def test_generate_report_with_sessions(temp_db):
    """Test generating report with session data."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create some sessions
        session_service = SessionService()
        for i in range(3):
            session_service.create_session(
                session_date=date(2025, 1, 20 + i),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=60,
                intensity=4,
                rolls=5,
                submissions_for=2,
                submissions_against=1,
            )

        report_service = ReportService()
        report = report_service.generate_report(date(2025, 1, 20), date(2025, 1, 22))

        # Verify summary
        assert report["summary"]["total_classes"] == 3
        assert report["summary"]["total_hours"] == 3.0
        assert report["summary"]["total_rolls"] == 15
        assert report["summary"]["submissions_for"] == 6
        assert report["summary"]["submissions_against"] == 3


def test_generate_report_empty(temp_db):
    """Test generating report with no sessions."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        service = ReportService()
        report = service.generate_report(date(2025, 1, 20), date(2025, 1, 22))

        assert report["summary"]["total_classes"] == 0
        assert len(report["sessions"]) == 0


def test_breakdown_by_type(temp_db):
    """Test breakdown by class type."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create mixed sessions
        session_service = SessionService()
        session_service.create_session(
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
            rolls=5,
        )
        session_service.create_session(
            session_date=date(2025, 1, 21),
            class_type="no-gi",
            gym_name="Test Gym",
            rolls=4,
        )

        report_service = ReportService()
        report = report_service.generate_report(date(2025, 1, 20), date(2025, 1, 21))

        breakdown = report["breakdown_by_type"]
        assert breakdown["gi"]["classes"] == 1
        assert breakdown["no-gi"]["classes"] == 1


def test_export_to_csv(temp_db):
    """Test CSV export."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        # Setup: Create session
        session_service = SessionService()
        session_service.create_session(
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
        )

        # Export
        report_service = ReportService()
        report = report_service.generate_report(date(2025, 1, 20), date(2025, 1, 20))

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            csv_path = f.name

        report_service.export_to_csv(report["sessions"], csv_path)

        # Verify file exists and has content
        csv_file = Path(csv_path)
        assert csv_file.exists()
        content = csv_file.read_text()
        assert "Test Gym" in content

        # Cleanup
        csv_file.unlink()


def test_calculate_rates(temp_db):
    """Test rate calculations."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        session_service = SessionService()
        session_service.create_session(
            session_date=date(2025, 1, 20),
            class_type="gi",
            gym_name="Test Gym",
            rolls=10,
            submissions_for=3,
            submissions_against=2,
        )

        report_service = ReportService()
        report = report_service.generate_report(date(2025, 1, 20), date(2025, 1, 20))

        # Verify rates (rounded to 2 decimal places)
        assert abs(report["summary"]["subs_per_roll"] - 0.3) < 0.01  # 3/10
        assert abs(report["summary"]["taps_per_roll"] - 0.2) < 0.01  # 2/10
        assert abs(report["summary"]["sub_ratio"] - 1.5) < 0.01  # 3/2
