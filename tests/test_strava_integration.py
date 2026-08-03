"""Database-backed tests for the Strava integration.

Covers the behaviour that determines whether the July backfill actually repairs
the gap: token rotation, sync idempotency, and needs_review session creation.
Strava's HTTP layer is stubbed — no network.
"""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

os.environ.setdefault(
    "TOKEN_ENCRYPTION_KEY", "wKm3vTHnqRz9nQ5xVYQzKzR2mJ8LxN0pQ7sT4uV6wXY="
)

from rivaflow.core.services.strava_service import (  # noqa: E402
    StravaAuthExpiredError,
    StravaNotConnectedError,
    StravaService,
)
from rivaflow.core.utils.encryption import encrypt_token  # noqa: E402
from rivaflow.db.repositories.session_repo import SessionRepository  # noqa: E402
from rivaflow.db.repositories.strava_repo import StravaRepository  # noqa: E402


def _connect(user_id: int, expires_in_sec: int = 3600) -> None:
    """Give a user a working Strava connection."""
    StravaRepository.upsert_connection(
        user_id=user_id,
        athlete_id="9001",
        access_token_encrypted=encrypt_token("access-original"),
        refresh_token_encrypted=encrypt_token("refresh-original"),
        token_expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_sec),
        scopes="read,activity:read_all",
    )


def _summary(
    activity_id: int, name: str = "BJJ", start: str = "2026-07-14T20:30:00Z"
) -> dict:
    return {
        "id": activity_id,
        "name": name,
        "type": "Workout",
        "sport_type": "Workout",
        "start_date": start,
        "start_date_local": start,
        "elapsed_time": 3600,
        "moving_time": 3300,
    }


def _detail(activity_id: int) -> dict:
    return {
        "id": activity_id,
        "average_heartrate": 148.0,
        "max_heartrate": 181.0,
        "calories": 620,
        "suffer_score": 55.0,
        "has_heartrate": True,
    }


class TestConnectionLifecycle:
    def test_status_reports_disconnected_before_connect(self, test_user):
        status = StravaService.get_status(test_user["id"])
        assert status["connected"] is False
        assert status["cached_activities"] == 0

    def test_status_reports_connected_after_connect(self, test_user):
        _connect(test_user["id"])
        status = StravaService.get_status(test_user["id"])
        assert status["connected"] is True
        assert status["athlete_id"] == "9001"
        assert status["has_private_scope"] is True

    def test_disconnect_clears_tokens(self, test_user):
        _connect(test_user["id"])
        assert StravaService.disconnect(test_user["id"]) is True
        assert StravaService.get_status(test_user["id"])["connected"] is False

    def test_reconnect_preserves_auto_create_preference(self, test_user):
        """Re-auth after an expired refresh token must not reset user settings."""
        _connect(test_user["id"])
        StravaRepository.set_auto_create(test_user["id"], False)
        _connect(test_user["id"])
        assert (
            StravaService.get_status(test_user["id"])["auto_create_sessions"] is False
        )

    def test_sync_without_connection_raises(self, test_user):
        with pytest.raises(StravaNotConnectedError):
            StravaService.sync(test_user["id"], days=7)


class TestOAuthState:
    def test_state_round_trips_to_user_id(self, test_user):
        token = StravaRepository.create_state(test_user["id"])
        assert StravaRepository.consume_state(token) == test_user["id"]

    def test_state_is_single_use(self, test_user):
        """A replayed callback must not connect a second time."""
        token = StravaRepository.create_state(test_user["id"])
        StravaRepository.consume_state(token)
        assert StravaRepository.consume_state(token) is None

    def test_unknown_state_is_rejected(self, temp_db):
        assert StravaRepository.consume_state("not-a-real-state") is None


class TestTokenRefresh:
    def test_valid_token_is_reused(self, test_user):
        _connect(test_user["id"], expires_in_sec=3600)
        with patch(
            "rivaflow.core.services.strava_service.StravaClient.refresh"
        ) as refresh:
            assert StravaService.get_access_token(test_user["id"]) == "access-original"
            refresh.assert_not_called()

    def test_expired_token_triggers_refresh(self, test_user):
        _connect(test_user["id"], expires_in_sec=-10)
        payload = {
            "access_token": "access-new",
            "refresh_token": "refresh-new",
            "expires_at": int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
        }
        with patch(
            "rivaflow.core.services.strava_service.StravaClient.refresh",
            return_value=payload,
        ):
            assert StravaService.get_access_token(test_user["id"]) == "access-new"

    def test_rotated_refresh_token_is_persisted(self, test_user):
        """Strava invalidates the old refresh token — losing the new one bricks sync."""
        _connect(test_user["id"], expires_in_sec=-10)
        payload = {
            "access_token": "access-new",
            "refresh_token": "refresh-rotated",
            "expires_at": int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
        }
        with patch(
            "rivaflow.core.services.strava_service.StravaClient.refresh",
            return_value=payload,
        ):
            StravaService.get_access_token(test_user["id"])

        # Second call must reuse the stored (now valid) access token, and the
        # persisted refresh token must be the rotated one.
        from rivaflow.core.utils.encryption import decrypt_token

        row = StravaRepository.get_connection_row(test_user["id"])
        assert decrypt_token(row["refresh_token_encrypted"]) == "refresh-rotated"

    def test_token_expiring_within_skew_is_refreshed_early(self, test_user):
        """A token with 60s left must not be handed to a multi-minute backfill."""
        _connect(test_user["id"], expires_in_sec=60)
        payload = {
            "access_token": "access-new",
            "refresh_token": "refresh-new",
            "expires_at": int((datetime.now(UTC) + timedelta(hours=6)).timestamp()),
        }
        with patch(
            "rivaflow.core.services.strava_service.StravaClient.refresh",
            return_value=payload,
        ) as refresh:
            StravaService.get_access_token(test_user["id"])
            refresh.assert_called_once()

    def test_dead_refresh_token_surfaces_as_auth_expired(self, test_user):
        _connect(test_user["id"], expires_in_sec=-10)
        with patch(
            "rivaflow.core.services.strava_service.StravaClient.refresh",
            side_effect=StravaAuthExpiredError(),
        ):
            with pytest.raises(StravaAuthExpiredError):
                StravaService.get_access_token(test_user["id"])


class TestSync:
    def _run_sync(self, user_id, summaries, **kwargs):
        with (
            patch(
                "rivaflow.core.services.strava_service.StravaClient.list_activities",
                side_effect=lambda *a, **k: summaries if k.get("page", 1) == 1 else [],
            ),
            patch(
                "rivaflow.core.services.strava_service.StravaClient.get_activity",
                side_effect=lambda _t, aid: _detail(int(aid)),
            ),
        ):
            return StravaService.sync(user_id, **kwargs)

    def test_sync_caches_activities(self, test_user):
        _connect(test_user["id"])
        result = self._run_sync(
            test_user["id"], [_summary(111)], days=30, auto_create=False
        )
        assert result["fetched"] == 1
        assert result["created"] == 1

        cached = StravaRepository.get_activity_by_strava_id(test_user["id"], "111")
        assert cached["avg_heart_rate"] == 148
        assert cached["max_heart_rate"] == 181
        assert cached["calories"] == 620

    def test_sync_is_idempotent(self, test_user):
        """Re-running a backfill repairs gaps — it must not duplicate."""
        _connect(test_user["id"])
        self._run_sync(test_user["id"], [_summary(111)], days=30, auto_create=False)
        second = self._run_sync(
            test_user["id"], [_summary(111)], days=30, auto_create=False
        )

        assert second["created"] == 0
        assert second["updated"] == 1
        assert StravaRepository.count_for_user(test_user["id"]) == 1

    def test_resync_does_not_wipe_detail_data(self, test_user):
        """A summary-only re-sync must keep the heart rate the detail call fetched."""
        _connect(test_user["id"])
        self._run_sync(test_user["id"], [_summary(111)], days=30, auto_create=False)

        with patch(
            "rivaflow.core.services.strava_service.StravaClient.list_activities",
            side_effect=lambda *a, **k: (
                [_summary(111)] if k.get("page", 1) == 1 else []
            ),
        ):
            StravaService.sync(test_user["id"], days=30, auto_create=False)

        cached = StravaRepository.get_activity_by_strava_id(test_user["id"], "111")
        assert cached["avg_heart_rate"] == 148

    def test_sync_creates_needs_review_session(self, test_user):
        _connect(test_user["id"])
        result = self._run_sync(
            test_user["id"], [_summary(111)], days=30, auto_create=True
        )
        assert result["sessions_created"] == 1

        sessions = SessionRepository.get_recent(test_user["id"], limit=50)
        assert len(sessions) == 1
        session = sessions[0]
        assert session["source"] == "strava"
        assert session["needs_review"] is True
        assert session["strava_avg_hr"] == 148
        assert session["strava_max_hr"] == 181
        assert session["strava_calories"] == 620
        assert session["strava_activity_id"] == "111"

    def test_sync_does_not_double_create_sessions(self, test_user):
        _connect(test_user["id"])
        self._run_sync(test_user["id"], [_summary(111)], days=30, auto_create=True)
        second = self._run_sync(
            test_user["id"], [_summary(111)], days=30, auto_create=True
        )

        assert second["sessions_created"] == 0
        assert len(SessionRepository.get_recent(test_user["id"], limit=50)) == 1

    def test_auto_create_off_caches_without_sessions(self, test_user):
        _connect(test_user["id"])
        result = self._run_sync(
            test_user["id"], [_summary(111)], days=30, auto_create=False
        )
        assert result["sessions_created"] == 0
        assert StravaRepository.count_for_user(test_user["id"]) == 1
        assert SessionRepository.get_recent(test_user["id"], limit=50) == []

    def test_short_activity_is_cached_but_not_imported(self, test_user):
        _connect(test_user["id"])
        walk = {**_summary(222, name="Walk to station"), "sport_type": "Walk"}
        result = self._run_sync(test_user["id"], [walk], days=30, auto_create=True)

        assert result["sessions_created"] == 0
        assert StravaRepository.count_for_user(test_user["id"]) == 1

    def test_backfill_range_is_honoured(self, test_user):
        """The July repair path — explicit start/end rather than a day count."""
        _connect(test_user["id"])
        july_start = datetime(2026, 7, 1, tzinfo=UTC)
        july_end = datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC)

        result = self._run_sync(
            test_user["id"],
            [_summary(111, start="2026-07-14T20:30:00Z")],
            after=july_start,
            before=july_end,
            auto_create=True,
        )
        assert result["range_start"].startswith("2026-07-01")
        assert result["sessions_created"] == 1

        session = SessionRepository.get_recent(test_user["id"], limit=50)[0]
        assert str(session["session_date"]).startswith("2026-07-14")

    def test_inverted_range_is_rejected(self, test_user):
        from rivaflow.core.exceptions import ValidationError

        _connect(test_user["id"])
        with pytest.raises(ValidationError):
            StravaService.sync(
                test_user["id"],
                after=datetime(2026, 7, 31, tzinfo=UTC),
                before=datetime(2026, 7, 1, tzinfo=UTC),
            )

    def test_detail_fetch_failure_does_not_abort_backfill(self, test_user):
        """One unreadable activity must not cost the whole month."""
        from rivaflow.core.exceptions import ExternalServiceError

        _connect(test_user["id"])
        with (
            patch(
                "rivaflow.core.services.strava_service.StravaClient.list_activities",
                side_effect=lambda *a, **k: (
                    [_summary(111), _summary(222)] if k.get("page", 1) == 1 else []
                ),
            ),
            patch(
                "rivaflow.core.services.strava_service.StravaClient.get_activity",
                side_effect=ExternalServiceError("boom"),
            ),
        ):
            result = StravaService.sync(test_user["id"], days=30, auto_create=False)

        assert result["fetched"] == 2
        assert StravaRepository.count_for_user(test_user["id"]) == 2

    def test_user_isolation(self, test_user, test_user2):
        """One athlete's activities must never surface on another account."""
        _connect(test_user["id"])
        _connect(test_user2["id"])
        self._run_sync(test_user["id"], [_summary(111)], days=30, auto_create=False)

        assert StravaRepository.count_for_user(test_user["id"]) == 1
        assert StravaRepository.count_for_user(test_user2["id"]) == 0
        assert (
            StravaRepository.get_activity_by_strava_id(test_user2["id"], "111") is None
        )


class TestImportAndDismiss:
    def test_importable_lists_unlinked_with_suggestion(self, test_user):
        _connect(test_user["id"])
        StravaRepository.upsert_activity(
            test_user["id"],
            "111",
            name="No-Gi rolls",
            sport_type="Workout",
            start_time=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            start_time_local=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            elapsed_time_sec=3600,
        )
        items = StravaService.list_importable(test_user["id"])
        assert len(items) == 1
        assert items[0]["suggested_class_type"] == "no-gi"
        assert items[0]["importable"] is True

    def test_dismissed_activity_leaves_importable_list(self, test_user):
        _connect(test_user["id"])
        cache_id, _ = StravaRepository.upsert_activity(
            test_user["id"],
            "111",
            name="Commute",
            sport_type="Ride",
            start_time=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
            elapsed_time_sec=3600,
        )
        StravaRepository.dismiss(test_user["id"], cache_id)
        assert StravaService.list_importable(test_user["id"]) == []

    def test_import_links_activity_to_session(self, test_user):
        _connect(test_user["id"])
        cache_id, _ = StravaRepository.upsert_activity(
            test_user["id"],
            "111",
            name="Gi class",
            sport_type="Workout",
            start_time=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            start_time_local=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            elapsed_time_sec=3600,
            avg_heart_rate=150,
        )
        cached = StravaRepository.get_activity(test_user["id"], cache_id)
        session_id = StravaService.import_activity(test_user["id"], cached)

        assert session_id is not None
        assert (
            StravaRepository.get_activity(test_user["id"], cache_id)["session_id"]
            == session_id
        )

    def test_import_is_refused_when_already_linked(self, test_user):
        _connect(test_user["id"])
        cache_id, _ = StravaRepository.upsert_activity(
            test_user["id"],
            "111",
            name="Gi class",
            sport_type="Workout",
            start_time=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            start_time_local=datetime(2026, 7, 14, 20, 30, tzinfo=UTC),
            elapsed_time_sec=3600,
        )
        cached = StravaRepository.get_activity(test_user["id"], cache_id)
        StravaService.import_activity(test_user["id"], cached)

        relinked = StravaRepository.get_activity(test_user["id"], cache_id)
        assert StravaService.import_activity(test_user["id"], relinked) is None


class TestRoutes:
    def test_status_requires_auth(self, client):
        assert client.get("/api/v1/integrations/strava/status").status_code in (
            401,
            403,
        )

    def test_status_returns_disconnected(self, client, auth_headers):
        response = client.get(
            "/api/v1/integrations/strava/status", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["connected"] is False

    def test_backfill_rejects_bad_date(self, client, auth_headers):
        response = client.post(
            "/api/v1/integrations/strava/backfill",
            headers=auth_headers,
            json={"start_date": "not-a-date", "end_date": "2026-07-31"},
        )
        assert response.status_code == 400

    def test_callback_redirects_on_error(self, client):
        response = client.get(
            "/api/v1/integrations/strava/callback?error=access_denied",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "strava=error" in response.headers["location"]
