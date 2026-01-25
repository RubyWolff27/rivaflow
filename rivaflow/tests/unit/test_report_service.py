"""Unit tests for ReportService calculations."""
import pytest
from datetime import date, timedelta
from rivaflow.core.services.report_service import ReportService


class TestReportMetrics:
    """Test report metric calculations for correctness."""

    def test_subs_per_class_formula(self):
        """Verify subs_per_class = submissions_for / total_classes (not including submissions_against)."""
        service = ReportService()

        # Mock sessions: 3 sessions with sf=5,3,2 (total 10) and sa=1,2,1 (total 4)
        sessions = [
            {
                "duration_mins": 60,
                "intensity": 4,
                "rolls": 5,
                "submissions_for": 5,
                "submissions_against": 1,
                "partners": ["Alice"],
            },
            {
                "duration_mins": 60,
                "intensity": 4,
                "rolls": 5,
                "submissions_for": 3,
                "submissions_against": 2,
                "partners": ["Bob"],
            },
            {
                "duration_mins": 60,
                "intensity": 5,
                "rolls": 5,
                "submissions_for": 2,
                "submissions_against": 1,
                "partners": ["Alice", "Charlie"],
            },
        ]

        summary = service._calculate_summary(sessions)

        # Critical assertion: subs_per_class should ONLY count submissions FOR
        assert summary["subs_per_class"] == round(10 / 3, 2)  # 10 sf / 3 classes = 3.33
        assert summary["subs_per_class"] != round(14 / 3, 2)  # NOT (10 sf + 4 sa) / 3 = 4.67

        # Verify other metrics are also correct
        assert summary["total_classes"] == 3
        assert summary["submissions_for"] == 10
        assert summary["submissions_against"] == 4
        assert summary["total_rolls"] == 15
        assert summary["subs_per_roll"] == round(10 / 15, 2)  # 0.67
        assert summary["taps_per_roll"] == round(4 / 15, 2)  # 0.27

    def test_subs_per_roll_formula(self):
        """Verify subs_per_roll = submissions_for / total_rolls."""
        service = ReportService()

        sessions = [
            {"duration_mins": 60, "intensity": 4, "rolls": 10, "submissions_for": 5, "submissions_against": 2, "partners": []},
        ]

        summary = service._calculate_summary(sessions)
        assert summary["subs_per_roll"] == 0.5  # 5 / 10

    def test_taps_per_roll_formula(self):
        """Verify taps_per_roll = submissions_against / total_rolls."""
        service = ReportService()

        sessions = [
            {"duration_mins": 60, "intensity": 4, "rolls": 10, "submissions_for": 3, "submissions_against": 7, "partners": []},
        ]

        summary = service._calculate_summary(sessions)
        assert summary["taps_per_roll"] == 0.7  # 7 / 10

    def test_zero_rolls_no_division_error(self):
        """Verify rates default to 0.0 when rolls=0 (no division by zero)."""
        service = ReportService()

        # Non-sparring session: rolls=0
        sessions = [
            {"duration_mins": 60, "intensity": 3, "rolls": 0, "submissions_for": 0, "submissions_against": 0, "partners": []},
        ]

        summary = service._calculate_summary(sessions)
        assert summary["subs_per_roll"] == 0.0
        assert summary["taps_per_roll"] == 0.0

    def test_unique_partners_count(self):
        """Verify unique partners are counted correctly across sessions."""
        service = ReportService()

        sessions = [
            {"duration_mins": 60, "intensity": 4, "rolls": 5, "submissions_for": 2, "submissions_against": 1, "partners": ["Alice", "Bob"]},
            {"duration_mins": 60, "intensity": 4, "rolls": 5, "submissions_for": 3, "submissions_against": 0, "partners": ["Bob", "Charlie"]},
            {"duration_mins": 60, "intensity": 5, "rolls": 5, "submissions_for": 1, "submissions_against": 2, "partners": ["Alice"]},
        ]

        summary = service._calculate_summary(sessions)
        assert summary["unique_partners"] == 3  # Alice, Bob, Charlie (no duplicates)

    def test_sub_ratio_calculation(self):
        """Verify sub_ratio = submissions_for / submissions_against."""
        service = ReportService()

        sessions = [
            {"duration_mins": 60, "intensity": 4, "rolls": 10, "submissions_for": 6, "submissions_against": 3, "partners": []},
        ]

        summary = service._calculate_summary(sessions)
        assert summary["sub_ratio"] == 2.0  # 6 / 3

    def test_sub_ratio_edge_cases(self):
        """Verify sub_ratio handles edge cases (0 submissions against)."""
        service = ReportService()

        # Case 1: sf > 0, sa = 0 → return sf as float
        sessions = [
            {"duration_mins": 60, "intensity": 4, "rolls": 10, "submissions_for": 5, "submissions_against": 0, "partners": []},
        ]
        summary = service._calculate_summary(sessions)
        assert summary["sub_ratio"] == 5.0  # All submissions, no taps

        # Case 2: sf = 0, sa = 0 → return 0.0
        sessions = [
            {"duration_mins": 60, "intensity": 3, "rolls": 0, "submissions_for": 0, "submissions_against": 0, "partners": []},
        ]
        summary = service._calculate_summary(sessions)
        assert summary["sub_ratio"] == 0.0


class TestReportDateRanges:
    """Test date range calculations (Monday-Sunday weeks)."""

    def test_week_dates_monday_boundary(self):
        """Verify week starts on Monday and ends on Sunday."""
        service = ReportService()

        # Test with a known Wednesday (Jan 15, 2025)
        target_date = date(2025, 1, 15)
        monday, sunday = service.get_week_dates(target_date)

        assert monday.weekday() == 0  # Monday
        assert sunday.weekday() == 6  # Sunday
        assert (sunday - monday).days == 6  # Exactly 6 days apart
        assert monday == date(2025, 1, 13)
        assert sunday == date(2025, 1, 19)

    def test_week_dates_on_monday(self):
        """Verify Monday returns itself as start of week."""
        service = ReportService()

        monday = date(2025, 1, 13)  # A Monday
        start, end = service.get_week_dates(monday)

        assert start == monday
        assert end == date(2025, 1, 19)  # Following Sunday

    def test_week_dates_on_sunday(self):
        """Verify Sunday returns correct Monday-Sunday range."""
        service = ReportService()

        sunday = date(2025, 1, 19)  # A Sunday
        start, end = service.get_week_dates(sunday)

        assert start == date(2025, 1, 13)  # Previous Monday
        assert end == sunday

    def test_month_dates_calculation(self):
        """Verify month returns first and last day of month."""
        service = ReportService()

        # Test January 2025 (31 days)
        target_date = date(2025, 1, 15)
        first, last = service.get_month_dates(target_date)

        assert first == date(2025, 1, 1)
        assert last == date(2025, 1, 31)

    def test_month_dates_february_leap_year(self):
        """Verify February leap year calculation."""
        service = ReportService()

        # 2024 is a leap year
        target_date = date(2024, 2, 10)
        first, last = service.get_month_dates(target_date)

        assert first == date(2024, 2, 1)
        assert last == date(2024, 2, 29)  # Leap year

    def test_month_dates_december_year_wrap(self):
        """Verify December correctly wraps to next year."""
        service = ReportService()

        target_date = date(2024, 12, 15)
        first, last = service.get_month_dates(target_date)

        assert first == date(2024, 12, 1)
        assert last == date(2024, 12, 31)


class TestReportEmptyData:
    """Test report generation with no data."""

    def test_empty_summary(self):
        """Verify empty summary returns all zeros."""
        service = ReportService()

        summary = service._empty_summary()

        assert summary["total_classes"] == 0
        assert summary["total_hours"] == 0.0
        assert summary["total_rolls"] == 0
        assert summary["unique_partners"] == 0
        assert summary["submissions_for"] == 0
        assert summary["submissions_against"] == 0
        assert summary["avg_intensity"] == 0.0
        assert summary["subs_per_class"] == 0.0
        assert summary["subs_per_roll"] == 0.0
        assert summary["taps_per_roll"] == 0.0
        assert summary["sub_ratio"] == 0.0
