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
            password="securepass123",
            first_name="John",
            last_name="Doe",
        )

        assert registration is not None
        user_id = registration["user"]["id"]

        # Step 2: User logs their first training session
        session = session_service.log_session(
            user_id=user_id,
            session_date=date.today(),
            class_type="gi",
            gym_name="Gracie Barra",
            location="Los Angeles",
            duration_minutes=60,
            intensity=4,
            roll_count=5,
        )

        assert session is not None
        assert session["gym_name"] == "Gracie Barra"

        # Step 3: User views their stats
        repo = SessionRepository()
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
            weight=75.5,
        )

        assert readiness is not None

        # Evening: Log training session
        session = session_service.log_session(
            user_id=user_id,
            session_date=today,
            class_type="no-gi",
            gym_name="Local Academy",
            duration_minutes=90,
            intensity=5,
            roll_count=8,
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
                duration_minutes=60,
                intensity=4,
            )

        # View analytics
        analytics_service = AnalyticsService()
        weekly_stats = analytics_service.get_week_summary(
            user_id=user_id, week_start=date.today() - timedelta(days=6)
        )

        assert weekly_stats is not None
        assert weekly_stats["total_sessions"] > 0

    def test_monthly_progress_tracking(self, temp_db, test_user, session_factory):
        """Test: User tracks progress over a month."""
        user_id = test_user["id"]

        # Log sessions across a month
        for i in range(30):
            session_date = date.today() - timedelta(days=i)
            session_factory(
                session_date=session_date,
                duration_minutes=60,
                intensity=4,
            )

        # Get monthly analytics
        analytics_service = AnalyticsService()
        monthly_stats = analytics_service.get_monthly_summary(
            user_id=user_id, month=date.today().month, year=date.today().year
        )

        assert monthly_stats is not None
        assert monthly_stats.get("total_sessions", 0) > 0


class TestMultiUserInteraction:
    """Test interactions between multiple users."""

    def test_user_follow_workflow(self, temp_db, test_user, test_user2):
        """Test: User follows another user → views their profile."""
        from rivaflow.db.repositories.user_relationship_repo import (
            UserRelationshipRepository,
        )

        user1_id = test_user["id"]
        user2_id = test_user2["id"]

        # User1 follows User2
        relationship_repo = UserRelationshipRepository()
        relationship_repo.create_relationship(
            follower_id=user1_id, following_id=user2_id
        )

        # Verify relationship exists
        is_following = relationship_repo.is_following(
            follower_id=user1_id, following_id=user2_id
        )

        assert is_following is True

        # Get User2's followers
        followers = relationship_repo.get_followers(user_id=user2_id)
        assert len(followers) > 0

    def test_social_feed_workflow(
        self, temp_db, test_user, test_user2, session_factory
    ):
        """Test: Users follow each other → view social feed."""
        from rivaflow.db.repositories.user_relationship_repo import (
            UserRelationshipRepository,
        )

        user1_id = test_user["id"]
        user2_id = test_user2["id"]

        # Create mutual following
        relationship_repo = UserRelationshipRepository()
        relationship_repo.create_relationship(user1_id, user2_id)
        relationship_repo.create_relationship(user2_id, user1_id)

        # Both users log sessions
        session_factory(user_id=user1_id, gym_name="Gym A")
        session_factory(user_id=user2_id, gym_name="Gym B")

        # Get follower sessions
        following_ids = [
            rel["following_id"] for rel in relationship_repo.get_following(user1_id)
        ]

        assert user2_id in following_ids


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
        session1 = session_service.log_session(
            user_id=user_id,
            session_date=today,
            class_type="gi",
            gym_name="Test Gym",
            duration_minutes=60,
            intensity=4,
        )

        assert session1 is not None

        # Log second session on same day (should be allowed)
        session2 = session_service.log_session(
            user_id=user_id,
            session_date=today,
            class_type="no-gi",
            gym_name="Test Gym",
            duration_minutes=90,
            intensity=5,
        )

        assert session2 is not None

        # Verify both sessions exist
        repo = SessionRepository()
        sessions = repo.list_by_user(user_id)
        assert len(sessions) >= 2

    def test_invalid_data_rejection(self, temp_db, test_user):
        """Test: User submits invalid data → validation error."""
        session_service = SessionService()

        # Try to log session with negative duration
        with pytest.raises((ValueError, Exception)):
            session_service.log_session(
                user_id=test_user["id"],
                session_date=date.today(),
                class_type="gi",
                gym_name="Test Gym",
                duration_minutes=-10,  # Invalid
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

        streak = streak_service.get_current_streak(user_id, "training")
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
