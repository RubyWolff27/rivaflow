"""Tests for WHOOP sync service -- data transformation and parsing."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

# Generate a valid Fernet key for test encryption
from cryptography.fernet import Fernet

from rivaflow.core.services.whoop_service import WhoopService

_TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _set_whoop_env(monkeypatch):
    """Set required WHOOP environment variables for all tests."""
    monkeypatch.setenv("WHOOP_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("WHOOP_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("WHOOP_REDIRECT_URI", "http://localhost/cb")
    monkeypatch.setenv("WHOOP_ENCRYPTION_KEY", _TEST_FERNET_KEY)


def _make_connected_service(user_id):
    """Create a WhoopService with a fake connection for the user."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()
    svc.connection_repo.upsert(
        user_id=user_id,
        access_token_encrypted=encrypt_token("fake-access"),
        refresh_token_encrypted=encrypt_token("fake-refresh"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        whoop_user_id="whoop-sync-test",
    )
    return svc


# ------------------------------------------------------------------ #
# sync_workouts -- data mapping
# ------------------------------------------------------------------ #


def _build_workout(
    workout_id="w1",
    sport_id=76,
    sport_name="Brazilian Jiu-Jitsu",
    kilojoule=500.0,
    strain=12.5,
    avg_hr=145,
    max_hr=180,
    zone_duration=None,
):
    """Build a WHOOP workout API record."""
    score = {
        "kilojoule": kilojoule,
        "strain": strain,
        "average_heart_rate": avg_hr,
        "max_heart_rate": max_hr,
        "zone_duration": zone_duration,
    }
    return {
        "id": workout_id,
        "sport_id": sport_id,
        "sport_name": sport_name,
        "start": "2025-01-20T10:00:00+00:00",
        "end": "2025-01-20T11:30:00+00:00",
        "timezone_offset": "+11:00",
        "score": score,
        "score_state": "SCORED",
    }


def test_sync_workouts_maps_fields(temp_db, test_user):
    """sync_workouts caches workout data with correct field mapping."""
    svc = _make_connected_service(test_user["id"])

    workout = _build_workout(
        kilojoule=500.0,
        strain=12.5,
        avg_hr=145,
        max_hr=180,
    )

    # Mock API calls
    svc.client.get_workouts = MagicMock(
        return_value={"records": [workout], "next_token": None}
    )
    # Mock auto-create and backfill to avoid needing full setup
    svc.auto_create_sessions_for_workouts = MagicMock(return_value=[])
    svc.backfill_session_timezones = MagicMock(return_value=0)

    result = svc.sync_workouts(test_user["id"], days_back=7)

    assert result["total_fetched"] == 1
    assert result["created"] == 1
    assert result["updated"] == 0

    # Verify cached data
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT * FROM whoop_workout_cache" " WHERE user_id = ?"),
            (test_user["id"],),
        )
        row = cursor.fetchone()

    assert row is not None
    cached = dict(row)
    assert cached["whoop_workout_id"] == "w1"
    assert cached["sport_id"] == 76
    assert float(cached["strain"]) == 12.5
    assert cached["avg_heart_rate"] == 145
    assert cached["max_heart_rate"] == 180
    # kilojoule -> calories: round(500 / 4.184) = 120
    assert cached["calories"] == round(500.0 / 4.184)


def test_sync_workouts_null_score(temp_db, test_user):
    """sync_workouts handles workout with null score gracefully."""
    svc = _make_connected_service(test_user["id"])

    workout = {
        "id": "w-null",
        "sport_id": 76,
        "sport_name": "BJJ",
        "start": "2025-01-20T10:00:00Z",
        "end": "2025-01-20T11:00:00Z",
        "score": None,
        "score_state": "PENDING_PROCESSING",
    }

    svc.client.get_workouts = MagicMock(
        return_value={"records": [workout], "next_token": None}
    )
    svc.auto_create_sessions_for_workouts = MagicMock(return_value=[])
    svc.backfill_session_timezones = MagicMock(return_value=0)

    result = svc.sync_workouts(test_user["id"])
    assert result["total_fetched"] == 1
    assert result["created"] == 1


def test_sync_workouts_pagination(temp_db, test_user):
    """sync_workouts follows pagination tokens."""
    svc = _make_connected_service(test_user["id"])

    page1 = {
        "records": [_build_workout(workout_id="w-p1")],
        "next_token": "page2",
    }
    page2 = {
        "records": [_build_workout(workout_id="w-p2")],
        "next_token": None,
    }

    svc.client.get_workouts = MagicMock(side_effect=[page1, page2])
    svc.auto_create_sessions_for_workouts = MagicMock(return_value=[])
    svc.backfill_session_timezones = MagicMock(return_value=0)

    result = svc.sync_workouts(test_user["id"])
    assert result["total_fetched"] == 2
    assert svc.client.get_workouts.call_count == 2


def test_sync_workouts_upsert_updates(temp_db, test_user):
    """sync_workouts increments 'updated' count on duplicate workout."""
    svc = _make_connected_service(test_user["id"])

    workout = _build_workout(workout_id="w-dup")

    svc.client.get_workouts = MagicMock(
        return_value={"records": [workout], "next_token": None}
    )
    svc.auto_create_sessions_for_workouts = MagicMock(return_value=[])
    svc.backfill_session_timezones = MagicMock(return_value=0)

    # First sync creates
    r1 = svc.sync_workouts(test_user["id"])
    assert r1["created"] == 1

    # Second sync updates
    r2 = svc.sync_workouts(test_user["id"])
    assert r2["updated"] == 1


def test_sync_workouts_missing_zone_durations(temp_db, test_user):
    """sync_workouts handles missing zone_durations without error."""
    svc = _make_connected_service(test_user["id"])

    workout = _build_workout(zone_duration=None)

    svc.client.get_workouts = MagicMock(
        return_value={"records": [workout], "next_token": None}
    )
    svc.auto_create_sessions_for_workouts = MagicMock(return_value=[])
    svc.backfill_session_timezones = MagicMock(return_value=0)

    result = svc.sync_workouts(test_user["id"])
    assert result["total_fetched"] == 1


# ------------------------------------------------------------------ #
# sync_recovery -- data mapping
# ------------------------------------------------------------------ #


def _build_cycle(cycle_id="c1"):
    return {
        "id": cycle_id,
        "start": "2025-01-19T22:00:00Z",
        "end": "2025-01-20T08:00:00Z",
    }


def _build_recovery(cycle_id="c1"):
    return {
        "cycle_id": cycle_id,
        "score": {
            "recovery_score": 85,
            "resting_heart_rate": 52,
            "hrv_rmssd_milli": 65.3,
            "spo2_percentage": 98.0,
            "skin_temp_celsius": 33.5,
        },
    }


def _build_sleep(cycle_id="c1"):
    return {
        "cycle_id": cycle_id,
        "score": {
            "sleep_performance_percentage": 92,
            "total_in_bed_time_milli": 28800000,
            "sleep_needed_baseline_milli": 27000000,
            "sleep_debt_milli": 0,
            "total_light_sleep_time_milli": 10000000,
            "total_slow_wave_sleep_time_milli": 8000000,
            "total_rem_sleep_time_milli": 7000000,
            "total_awake_time_milli": 3800000,
        },
    }


def test_sync_recovery_maps_fields(temp_db, test_user):
    """sync_recovery caches recovery data with correct field mapping."""
    svc = _make_connected_service(test_user["id"])

    svc.client.get_cycles = MagicMock(
        return_value={
            "records": [_build_cycle()],
            "next_token": None,
        }
    )
    svc.client.get_recovery = MagicMock(
        return_value={
            "records": [_build_recovery()],
            "next_token": None,
        }
    )
    svc.client.get_sleep = MagicMock(
        return_value={
            "records": [_build_sleep()],
            "next_token": None,
        }
    )

    result = svc.sync_recovery(test_user["id"], days_back=7)

    assert result["total_fetched"] == 1
    assert result["created"] == 1

    # Verify cached data
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT * FROM whoop_recovery_cache" " WHERE user_id = ?"),
            (test_user["id"],),
        )
        row = cursor.fetchone()

    assert row is not None
    cached = dict(row)
    assert cached["whoop_cycle_id"] == "c1"
    assert float(cached["recovery_score"]) == 85
    assert float(cached["resting_hr"]) == 52
    assert float(cached["hrv_ms"]) == 65.3
    assert float(cached["spo2"]) == 98.0
    assert float(cached["sleep_performance"]) == 92
    assert cached["sleep_duration_ms"] == 28800000


def test_sync_recovery_missing_data(temp_db, test_user):
    """sync_recovery handles cycles without recovery/sleep data."""
    svc = _make_connected_service(test_user["id"])

    # Cycle with no matching recovery or sleep
    svc.client.get_cycles = MagicMock(
        return_value={
            "records": [_build_cycle("c-orphan")],
            "next_token": None,
        }
    )
    svc.client.get_recovery = MagicMock(
        return_value={"records": [], "next_token": None}
    )
    svc.client.get_sleep = MagicMock(return_value={"records": [], "next_token": None})

    result = svc.sync_recovery(test_user["id"])
    assert result["total_fetched"] == 1
    assert result["created"] == 1

    # Verify null fields
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "SELECT recovery_score, hrv_ms"
                " FROM whoop_recovery_cache WHERE user_id = ?"
            ),
            (test_user["id"],),
        )
        row = cursor.fetchone()

    cached = dict(row)
    assert cached["recovery_score"] is None
    assert cached["hrv_ms"] is None


def test_sync_recovery_pagination(temp_db, test_user):
    """sync_recovery follows pagination tokens for all endpoints."""
    svc = _make_connected_service(test_user["id"])

    svc.client.get_cycles = MagicMock(
        side_effect=[
            {
                "records": [_build_cycle("c-a")],
                "next_token": "tok",
            },
            {
                "records": [_build_cycle("c-b")],
                "next_token": None,
            },
        ]
    )
    svc.client.get_recovery = MagicMock(
        return_value={"records": [], "next_token": None}
    )
    svc.client.get_sleep = MagicMock(return_value={"records": [], "next_token": None})

    result = svc.sync_recovery(test_user["id"])
    assert result["total_fetched"] == 2


# ------------------------------------------------------------------ #
# apply_recovery_to_readiness -- mapping logic
# ------------------------------------------------------------------ #


def test_apply_recovery_to_readiness_high_score(temp_db, test_user):
    """High recovery score maps to sleep=5, energy=5."""
    svc = _make_connected_service(test_user["id"])

    # Insert a recovery cache row with a high score
    svc.recovery_cache_repo.upsert(
        user_id=test_user["id"],
        whoop_cycle_id="c-high",
        recovery_score=95,
        resting_hr=48,
        hrv_ms=80.0,
        spo2=99.0,
        sleep_performance=95,
        cycle_start="2025-01-19T22:00:00Z",
        cycle_end="2025-01-20T08:00:00Z",
    )

    result = svc.apply_recovery_to_readiness(test_user["id"], "2025-01-20")
    assert result is not None
    assert result["sleep"] == 5
    assert result["energy"] == 5
    assert result["data_source"] == "whoop"
    assert result["whoop_recovery_score"] == 95


def test_apply_recovery_to_readiness_low_score(temp_db, test_user):
    """Low recovery score maps to sleep=1, energy=1."""
    svc = _make_connected_service(test_user["id"])

    svc.recovery_cache_repo.upsert(
        user_id=test_user["id"],
        whoop_cycle_id="c-low",
        recovery_score=20,
        cycle_start="2025-01-19T22:00:00Z",
        cycle_end="2025-01-20T08:00:00Z",
    )

    result = svc.apply_recovery_to_readiness(test_user["id"], "2025-01-20")
    assert result is not None
    assert result["sleep"] == 1
    assert result["energy"] == 1


def test_apply_recovery_to_readiness_medium_score(temp_db, test_user):
    """Medium recovery score (67-89) maps to sleep=4, energy=4."""
    svc = _make_connected_service(test_user["id"])

    svc.recovery_cache_repo.upsert(
        user_id=test_user["id"],
        whoop_cycle_id="c-med",
        recovery_score=75,
        cycle_start="2025-01-19T22:00:00Z",
        cycle_end="2025-01-20T08:00:00Z",
    )

    result = svc.apply_recovery_to_readiness(test_user["id"], "2025-01-20")
    assert result is not None
    assert result["sleep"] == 4
    assert result["energy"] == 4


def test_apply_recovery_no_data(temp_db, test_user):
    """apply_recovery_to_readiness returns None when no cached data."""
    svc = _make_connected_service(test_user["id"])

    # Mock sync to prevent actual HTTP calls
    svc.sync_recovery = MagicMock()

    result = svc.apply_recovery_to_readiness(test_user["id"], "2025-01-20")
    assert result is None
