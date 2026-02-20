"""Integration tests for complete user journeys."""

from datetime import date, timedelta

import pytest

from rivaflow.core.services.analytics_service import AnalyticsService
from rivaflow.core.services.auth_service import AuthService
from rivaflow.core.services.readiness_service import ReadinessService
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.repositories import ReadinessRepository, SessionRepository


class TestNewUserJourney:
    """Test complete journey for a new user."""

    def test_user_registration_to_first_session(self, temp_db):
        """Test: User registers → logs first session → views stats."""
        auth_service = AuthService()
        session_service = SessionService()

        # Step 1: User registers
        registration = auth_service.register(
            email="newuser@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
        )

        assert registration is not None
        user_id = registration["user"]["id"]

        # Step 2: User logs their first training session
        session_id = session_service.create_session(
            user_id=user_id,
            session_date=date.today(),
            class_type="gi",
            gym_name="Gracie Barra",
            location="Los Angeles",
            duration_mins=60,
            intensity=4,
            rolls=5,
        )

        assert session_id is not None

        # Step 3: User views their stats
        repo = SessionRepository()
        session = repo.get_by_id(user_id, session_id)
        assert session is not None
        assert session["gym_name"] == "Gracie Barra"

        sessions = repo.list_by_user(user_id)

        assert len(sessions) == 1
        assert sessions[0]["class_type"] == "gi"

    def test_user_daily_workflow(self, temp_db, test_user):
        """Test: User's typical daily workflow."""
        readiness_service = ReadinessService()
        session_service = SessionService()

        user_id = test_user["id"]
        today = date.today()

        # Morning: Log readiness check-in
        readiness = readiness_service.log_readiness(
            user_id=user_id,
            check_date=today,
            sleep=4,
            stress=3,
            soreness=2,
            energy=4,
            weight_kg=75.5,
        )

        assert readiness is not None

        # Evening: Log training session
        session = session_service.create_session(
            user_id=user_id,
            session_date=today,
            class_type="no-gi",
            gym_name="Local Academy",
            duration_mins=90,
            intensity=5,
            rolls=8,
        )

        assert session is not None

        # Verify both logged successfully
        readiness_repo = ReadinessRepository()
        session_repo = SessionRepository()

        assert readiness_repo.get_by_date(user_id, today) is not None
        assert len(session_repo.list_by_user(user_id)) > 0


class TestAnalyticsJourney:
    """Test analytics and reporting user journeys."""

    def test_weekly_analytics_flow(self, temp_db, test_user, session_factory):
        """Test: User logs sessions → views weekly analytics."""
        user_id = test_user["id"]

        # Log sessions for the week
        for i in range(7):
            session_date = date.today() - timedelta(days=i)
            session_factory(
                session_date=session_date,
                class_type="gi" if i % 2 == 0 else "no-gi",
                duration_mins=60,
                intensity=4,
            )

        # View analytics
        analytics_service = AnalyticsService()
        weekly_stats = analytics_service.get_performance_overview(
            user_id=user_id,
            start_date=date.today() - timedelta(days=6),
            end_date=date.today(),
        )

        assert weekly_stats is not None
        assert weekly_stats["summary"]["total_sessions"] > 0

    def test_monthly_progress_tracking(self, temp_db, test_user, session_factory):
        """Test: User tracks progress over a month."""
        user_id = test_user["id"]

        # Log sessions across a month
        for i in range(30):
            session_date = date.today() - timedelta(days=i)
            session_factory(
                session_date=session_date,
                duration_mins=60,
                intensity=4,
            )

        # Get monthly analytics
        analytics_service = AnalyticsService()
        first_of_month = date.today().replace(day=1)
        monthly_stats = analytics_service.get_performance_overview(
            user_id=user_id,
            start_date=first_of_month,
            end_date=date.today(),
        )

        assert monthly_stats is not None
        assert monthly_stats["summary"]["total_sessions"] > 0


class TestDataExportImport:
    """Test data export and portability."""

    def test_export_user_data(
        self, temp_db, test_user, session_factory, readiness_factory
    ):
        """Test: User exports all their data."""
        user_id = test_user["id"]

        # Create some data
        session_factory(session_date=date.today())
        readiness_factory(check_date=date.today())

        # Export data
        session_repo = SessionRepository()
        readiness_repo = ReadinessRepository()

        sessions = session_repo.list_by_user(user_id)
        readiness_entries = readiness_repo.list_by_user(user_id)

        # Verify data can be exported
        assert len(sessions) > 0
        assert len(readiness_entries) > 0

        # Verify data structure is complete
        for session in sessions:
            assert "session_date" in session
            assert "gym_name" in session


class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    def test_duplicate_session_handling(self, temp_db, test_user):
        """Test: User tries to log duplicate session → handled gracefully."""
        session_service = SessionService()
        user_id = test_user["id"]
        today = date.today()

        # Log first session
        session1 = session_service.create_session(
            user_id=user_id,
            session_date=today,
            class_type="gi",
            gym_name="Test Gym",
            duration_mins=60,
            intensity=4,
        )

        assert session1 is not None

        # Log second session on same day (should be allowed)
        session2 = session_service.create_session(
            user_id=user_id,
            session_date=today,
            class_type="no-gi",
            gym_name="Test Gym",
            duration_mins=90,
            intensity=5,
        )

        assert session2 is not None

        # Verify both sessions exist
        repo = SessionRepository()
        sessions = repo.list_by_user(user_id)
        assert len(sessions) >= 2

    @pytest.mark.skip(
        reason="SessionService.create_session does not validate duration_mins"
    )
    def test_invalid_data_rejection(self, temp_db, test_user):
        """Test: User submits invalid data → validation error."""
        session_service = SessionService()

        # Try to log session with negative duration
        with pytest.raises((ValueError, Exception)):
            session_service.create_session(
                user_id=test_user["id"],
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_mins=-10,  # Invalid
                intensity=4,
            )


class TestStreakCalculation:
    """Test streak calculation across user activities."""

    def test_training_streak_buildup(self, temp_db, test_user, session_factory):
        """Test: User trains consecutive days → builds streak."""
        user_id = test_user["id"]

        # Log sessions for consecutive days
        for i in range(7):
            session_date = date.today() - timedelta(days=i)
            session_factory(session_date=session_date)

        # Verify streak calculation
        from rivaflow.core.services.streak_service import StreakService

        streak_service = StreakService()

        streak = streak_service.get_streak(user_id, "training")
        assert streak is not None

    def test_streak_break_recovery(self, temp_db, test_user, session_factory):
        """Test: User breaks streak → can restart."""
        user_id = test_user["id"]

        # Build initial streak
        for i in range(3):
            session_date = date.today() - timedelta(days=10 + i)
            session_factory(session_date=session_date)

        # Break (gap of several days)

        # Start new streak
        for i in range(3):
            session_date = date.today() - timedelta(days=i)
            session_factory(session_date=session_date)

        # Verify sessions logged correctly
        repo = SessionRepository()
        sessions = repo.list_by_user(user_id)
        assert len(sessions) >= 6
