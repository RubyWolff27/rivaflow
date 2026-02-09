"""Tests for WHOOP auto-create sessions feature."""

import os

os.environ.setdefault(
    "WHOOP_ENCRYPTION_KEY",
    "IBNCNZo2hOe13DRV3YjzYiuVQpSP7rRifb570_OmhL0=",
)
os.environ.setdefault("ENABLE_WHOOP_INTEGRATION", "true")

from datetime import date  # noqa: E402
from unittest.mock import patch  # noqa: E402

from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.whoop_connection_repo import (
    WhoopConnectionRepository,
)
from rivaflow.db.repositories.whoop_workout_cache_repo import (
    WhoopWorkoutCacheRepository,
)


def _create_test_user(temp_db):
    """Helper to create a test user."""
    from rivaflow.core.auth import hash_password
    from rivaflow.db.repositories import UserRepository

    return UserRepository().create(
        email="whoop-auto@test.com",
        hashed_password=hash_password("testpass"),
        first_name="Test",
        last_name="User",
    )


def _create_whoop_connection(user_id, auto_create=False):
    """Helper to create a WHOOP connection."""
    from rivaflow.core.utils.encryption import encrypt_token

    conn_id = WhoopConnectionRepository.create(
        user_id=user_id,
        access_token_encrypted=encrypt_token("fake-token"),
        refresh_token_encrypted=encrypt_token("fake-refresh"),
        token_expires_at="2099-01-01T00:00:00",
        whoop_user_id="whoop_123",
    )
    if auto_create:
        WhoopConnectionRepository.update_auto_create(user_id, True)
    return conn_id


def _create_bjj_workout(user_id, workout_id="w1", start="2025-06-01T10:00:00"):
    """Helper to create a cached BJJ workout (sport_id=76)."""
    return WhoopWorkoutCacheRepository.upsert(
        user_id=user_id,
        whoop_workout_id=workout_id,
        start_time=start,
        end_time=start[:11] + "11:30:00",
        sport_id=76,
        sport_name="Brazilian Jiu Jitsu",
        strain=12.5,
        avg_heart_rate=145,
        max_heart_rate=175,
        kilojoules=1500.0,
        calories=359,
    )


class TestAutoCreateFromBjjWorkout:
    """Test auto_create_sessions_for_workouts logic."""

    def test_auto_create_from_bjj_workout(self, temp_db):
        """Creates session with correct fields from BJJ workout."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)
        _create_bjj_workout(uid)

        service = WhoopService()
        with patch.object(service, "get_valid_access_token"):
            created = service.auto_create_sessions_for_workouts(uid)

        assert len(created) == 1

        session = SessionRepository.get_by_id(uid, created[0])
        assert session is not None
        assert session["source"] == "whoop"
        assert session["needs_review"] is True
        assert session["whoop_strain"] == 12.5
        assert session["whoop_avg_hr"] == 145
        assert session["whoop_max_hr"] == 175
        assert session["whoop_calories"] == 359
        assert session["duration_mins"] == 90
        assert session["class_time"] == "10:00"

    def test_creates_from_any_sport(self, temp_db):
        """All workout types create sessions (user classifies on review)."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)

        # Create a running workout (sport_id=0)
        WhoopWorkoutCacheRepository.upsert(
            user_id=uid,
            whoop_workout_id="running1",
            start_time="2025-06-01T07:00:00",
            end_time="2025-06-01T08:00:00",
            sport_id=0,
            sport_name="Running",
        )

        service = WhoopService()
        created = service.auto_create_sessions_for_workouts(uid)
        assert len(created) == 1

    def test_skips_already_linked(self, temp_db):
        """Workouts already linked to a session are skipped."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)
        cache_id = _create_bjj_workout(uid)

        # Manually create a session and link the workout
        session_id = SessionRepository.create(
            user_id=uid,
            session_date=date(2025, 6, 1),
            class_type="no-gi",
            gym_name="Test Gym",
        )
        WhoopWorkoutCacheRepository.link_to_session(cache_id, session_id)

        service = WhoopService()
        created = service.auto_create_sessions_for_workouts(uid)
        assert len(created) == 0

    def test_respects_toggle_off(self, temp_db):
        """When auto_create_sessions=0, no sessions are created."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=False)
        _create_bjj_workout(uid)

        service = WhoopService()
        created = service.auto_create_sessions_for_workouts(uid)
        assert len(created) == 0

    def test_uses_profile_defaults(self, temp_db):
        """Session uses gym and class_type from user profile."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)
        _create_bjj_workout(uid)

        service = WhoopService()
        # Mock profile to return defaults
        with patch.object(
            service.profile_repo,
            "get",
            return_value={
                "default_gym": "Alliance BJJ",
                "primary_training_type": "gi",
            },
        ):
            created = service.auto_create_sessions_for_workouts(uid)

        assert len(created) == 1

        session = SessionRepository.get_by_id(uid, created[0])
        assert session["gym_name"] == "Alliance BJJ"
        assert session["class_type"] == "gi"

    def test_backfill_on_enable(self, temp_db):
        """set_auto_create(enabled=True) backfills existing workouts."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=False)
        _create_bjj_workout(uid, workout_id="w1")
        _create_bjj_workout(uid, workout_id="w2", start="2025-06-02T09:00:00")

        service = WhoopService()
        result = service.set_auto_create_sessions(uid, True)

        assert result["auto_create_sessions"] is True
        assert result["backfilled"] == 2

    def test_sync_triggers_auto_create(self, temp_db):
        """sync_workouts calls auto_create after syncing."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)

        service = WhoopService()

        # Mock the WHOOP API to return a BJJ workout
        mock_response = {
            "records": [
                {
                    "id": "api_workout_1",
                    "sport_id": 76,
                    "sport_name": "Brazilian Jiu Jitsu",
                    "start": "2025-06-01T10:00:00.000Z",
                    "end": "2025-06-01T11:30:00.000Z",
                    "score_state": "SCORED",
                    "score": {
                        "strain": 14.2,
                        "average_heart_rate": 150,
                        "max_heart_rate": 180,
                        "kilojoule": 1800.0,
                    },
                }
            ],
            "next_token": None,
        }

        with (
            patch.object(service, "get_valid_access_token", return_value="tok"),
            patch.object(service.client, "get_workouts", return_value=mock_response),
        ):
            result = service.sync_workouts(uid)

        assert result["auto_sessions_created"] == 1

    def test_no_duplicates(self, temp_db):
        """Re-syncing same workout doesn't create duplicate sessions."""
        from rivaflow.core.services.whoop_service import WhoopService

        user = _create_test_user(temp_db)
        uid = user["id"]
        _create_whoop_connection(uid, auto_create=True)
        _create_bjj_workout(uid)

        service = WhoopService()

        # First run creates
        created1 = service.auto_create_sessions_for_workouts(uid)
        assert len(created1) == 1

        # Second run skips (workout is now linked)
        created2 = service.auto_create_sessions_for_workouts(uid)
        assert len(created2) == 0


class TestSessionRepoSourceFields:
    """Verify source and needs_review in session create/update/read."""

    def test_create_with_source_and_needs_review(self, temp_db):
        user = _create_test_user(temp_db)
        uid = user["id"]

        session_id = SessionRepository.create(
            user_id=uid,
            session_date=date(2025, 6, 1),
            class_type="no-gi",
            gym_name="Test Gym",
            source="whoop",
            needs_review=True,
        )

        session = SessionRepository.get_by_id(uid, session_id)
        assert session["source"] == "whoop"
        assert session["needs_review"] is True

    def test_create_defaults_to_manual(self, temp_db):
        user = _create_test_user(temp_db)
        uid = user["id"]

        session_id = SessionRepository.create(
            user_id=uid,
            session_date=date(2025, 6, 1),
            class_type="gi",
            gym_name="Test Gym",
        )

        session = SessionRepository.get_by_id(uid, session_id)
        assert session["source"] == "manual"
        assert session["needs_review"] is False

    def test_update_clears_needs_review(self, temp_db):
        user = _create_test_user(temp_db)
        uid = user["id"]

        session_id = SessionRepository.create(
            user_id=uid,
            session_date=date(2025, 6, 1),
            class_type="no-gi",
            gym_name="Test Gym",
            source="whoop",
            needs_review=True,
        )

        SessionRepository.update(uid, session_id, needs_review=False)
        # Re-fetch after commit to verify
        refreshed = SessionRepository.get_by_id(uid, session_id)
        assert refreshed is not None
        assert refreshed["needs_review"] is False
