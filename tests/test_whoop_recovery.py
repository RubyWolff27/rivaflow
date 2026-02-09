"""Tests for WHOOP recovery cache, sync, and readiness auto-fill."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from rivaflow.db.repositories.whoop_recovery_cache_repo import (
    WhoopRecoveryCacheRepository,
)


class TestWhoopRecoveryCacheRepo:
    """Tests for WhoopRecoveryCacheRepository CRUD operations."""

    def test_upsert_creates_new_record(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        row_id = repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_123",
            recovery_score=85.0,
            resting_hr=55,
            hrv_ms=65.0,
            spo2=98.0,
            sleep_performance=90.0,
            sleep_duration_ms=28800000,
            cycle_start="2025-02-01",
        )
        assert row_id > 0

    def test_upsert_updates_existing_record(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        id1 = repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_123",
            recovery_score=85.0,
            cycle_start="2025-02-01",
        )
        id2 = repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_123",
            recovery_score=90.0,
            cycle_start="2025-02-01",
        )
        # Should update same row, not create new
        assert id1 == id2
        row = repo.get_latest(1)
        assert row is not None
        assert row["recovery_score"] == 90.0

    def test_get_latest_returns_most_recent(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_1",
            recovery_score=70.0,
            cycle_start="2025-02-01",
        )
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_2",
            recovery_score=85.0,
            cycle_start="2025-02-02",
        )
        latest = repo.get_latest(1)
        assert latest is not None
        assert latest["recovery_score"] == 85.0
        assert latest["whoop_cycle_id"] == "cycle_2"

    def test_get_latest_returns_none_for_no_data(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        assert repo.get_latest(999) is None

    def test_get_by_date_range(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        for day in range(1, 6):
            repo.upsert(
                user_id=1,
                whoop_cycle_id=f"cycle_{day}",
                recovery_score=60.0 + day * 5,
                cycle_start=f"2025-02-0{day}",
            )
        results = repo.get_by_date_range(1, "2025-02-02", "2025-02-04")
        assert len(results) == 3
        # Should be ordered by cycle_start DESC
        assert results[0]["whoop_cycle_id"] == "cycle_4"

    def test_delete_by_user(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_1",
            recovery_score=70.0,
            cycle_start="2025-02-01",
        )
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_2",
            recovery_score=80.0,
            cycle_start="2025-02-02",
        )
        deleted = repo.delete_by_user(1)
        assert deleted == 2
        assert repo.get_latest(1) is None

    def test_delete_by_user_no_data(self, temp_db):
        repo = WhoopRecoveryCacheRepository()
        deleted = repo.delete_by_user(999)
        assert deleted == 0


class TestWhoopServiceRecovery:
    """Tests for WhoopService recovery methods."""

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_apply_recovery_to_readiness_high_recovery(self, mock_client_cls, temp_db):
        from rivaflow.core.services.whoop_service import WhoopService

        service = WhoopService()

        # Insert a recovery record
        repo = WhoopRecoveryCacheRepository()
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_today",
            recovery_score=92.0,
            hrv_ms=75.0,
            resting_hr=52,
            spo2=98.5,
            sleep_performance=95.0,
            cycle_start="2025-02-08",
        )

        result = service.apply_recovery_to_readiness(1, "2025-02-08")
        assert result is not None
        assert result["sleep"] == 5  # 90-100% maps to 5
        assert result["energy"] == 5
        assert result["hrv_ms"] == 75.0
        assert result["resting_hr"] == 52
        assert result["data_source"] == "whoop"

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_apply_recovery_to_readiness_low_recovery(self, mock_client_cls, temp_db):
        from rivaflow.core.services.whoop_service import WhoopService

        service = WhoopService()

        repo = WhoopRecoveryCacheRepository()
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_low",
            recovery_score=25.0,
            hrv_ms=30.0,
            resting_hr=68,
            cycle_start="2025-02-08",
        )

        result = service.apply_recovery_to_readiness(1, "2025-02-08")
        assert result is not None
        assert result["sleep"] == 1  # 1-33% maps to 1
        assert result["energy"] == 1

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_apply_recovery_to_readiness_medium_recovery(
        self, mock_client_cls, temp_db
    ):
        from rivaflow.core.services.whoop_service import WhoopService

        service = WhoopService()

        repo = WhoopRecoveryCacheRepository()
        repo.upsert(
            user_id=1,
            whoop_cycle_id="cycle_med",
            recovery_score=55.0,
            hrv_ms=50.0,
            resting_hr=60,
            cycle_start="2025-02-08",
        )

        result = service.apply_recovery_to_readiness(1, "2025-02-08")
        assert result is not None
        assert result["sleep"] == 3  # 50-66% maps to 3
        assert result["energy"] == 3

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_apply_recovery_no_data(self, mock_client_cls, temp_db):
        from rivaflow.core.services.whoop_service import WhoopService

        service = WhoopService()
        result = service.apply_recovery_to_readiness(1, "2025-02-08")
        assert result is None

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_check_scope_compatibility_needs_reauth(self, mock_client_cls, temp_db):
        from rivaflow.core.services.whoop_service import WhoopService
        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )

        service = WhoopService()
        conn_repo = WhoopConnectionRepository()

        # Create a connection with old (limited) scopes
        conn_repo.create(
            user_id=1,
            whoop_user_id="whoop_123",
            access_token_encrypted="fake_token",
            refresh_token_encrypted="fake_refresh",
            token_expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes="read:workout read:profile offline",
        )

        result = service.check_scope_compatibility(1)
        assert result["needs_reauth"] is True
        assert len(result["missing_scopes"]) > 0
        assert "read:recovery" in result["missing_scopes"]

    @patch("rivaflow.core.services.whoop_service.WhoopClient")
    def test_check_scope_compatibility_all_scopes(self, mock_client_cls, temp_db):
        from rivaflow.core.services.whoop_service import WhoopService
        from rivaflow.core.services.whoop_client import WHOOP_SCOPES
        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )

        service = WhoopService()
        conn_repo = WhoopConnectionRepository()

        # Create connection with all current scopes
        conn_repo.create(
            user_id=1,
            whoop_user_id="whoop_123",
            access_token_encrypted="fake_token",
            refresh_token_encrypted="fake_refresh",
            token_expires_at=datetime.now(UTC) + timedelta(hours=1),
            scopes=WHOOP_SCOPES,
        )

        result = service.check_scope_compatibility(1)
        assert result["needs_reauth"] is False
        assert len(result["missing_scopes"]) == 0
