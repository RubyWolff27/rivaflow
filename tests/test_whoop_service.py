"""Tests for WhoopService -- OAuth, connection status, and settings."""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from rivaflow.core.services.whoop_service import WhoopService

# Ensure encryption key is available for tests
os.environ.setdefault(
    "WHOOP_ENCRYPTION_KEY",
    "dGVzdC1lbmNyeXB0aW9uLWtleS0xMjM0NTY3ODkwYWJjZA==",
)

# Generate a valid Fernet key for test encryption
from cryptography.fernet import Fernet

_TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def _set_whoop_env(monkeypatch):
    """Set required WHOOP environment variables for all tests."""
    monkeypatch.setenv("WHOOP_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("WHOOP_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("WHOOP_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.setenv("WHOOP_ENCRYPTION_KEY", _TEST_FERNET_KEY)

    # Patch the already-initialised settings singleton so that
    # WhoopClient picks up the test values.
    from rivaflow.core.settings import settings

    monkeypatch.setattr(settings, "WHOOP_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "WHOOP_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(
        settings,
        "WHOOP_REDIRECT_URI",
        "http://localhost/callback",
    )


# ------------------------------------------------------------------ #
# initiate_oauth
# ------------------------------------------------------------------ #


def test_initiate_oauth_returns_url(temp_db, test_user):
    """initiate_oauth stores state and returns an authorization URL."""
    svc = WhoopService()
    url = svc.initiate_oauth(test_user["id"])

    assert isinstance(url, str)
    assert "oauth2/auth" in url
    assert "state=" in url
    assert "client_id=" in url


def test_initiate_oauth_stores_state(temp_db, test_user):
    """initiate_oauth persists an OAuth state row for the user."""
    svc = WhoopService()
    svc.initiate_oauth(test_user["id"])

    # Verify a state row was written
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "SELECT COUNT(*) as cnt" " FROM whoop_oauth_states WHERE user_id = ?"
            ),
            (test_user["id"],),
        )
        row = cursor.fetchone()
        assert row["cnt"] >= 1


# ------------------------------------------------------------------ #
# get_connection_status
# ------------------------------------------------------------------ #


def test_get_connection_status_disconnected(temp_db, test_user):
    """get_connection_status returns connected=False for new user."""
    svc = WhoopService()
    status = svc.get_connection_status(test_user["id"])

    assert isinstance(status, dict)
    assert status["connected"] is False


def test_get_connection_status_connected(temp_db, test_user):
    """get_connection_status returns full payload when connected."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    # Manually insert a connection row
    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake-access"),
        refresh_token_encrypted=encrypt_token("fake-refresh"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        whoop_user_id="whoop-123",
        scopes="read:workout read:recovery",
    )

    # Mark active (upsert sets is_active via the UPDATE path)
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE whoop_connections" " SET is_active = 1 WHERE user_id = ?"
            ),
            (test_user["id"],),
        )
        conn.commit()

    status = svc.get_connection_status(test_user["id"])
    assert status["connected"] is True
    assert status["whoop_user_id"] == "whoop-123"
    assert "auto_create_sessions" in status
    assert "auto_fill_readiness" in status


# ------------------------------------------------------------------ #
# disconnect
# ------------------------------------------------------------------ #


def test_disconnect_cleans_up(temp_db, test_user):
    """disconnect removes connection, caches, and WHOOP session fields."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    # Create a connection
    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake-access"),
        refresh_token_encrypted=encrypt_token("fake-refresh"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        whoop_user_id="whoop-456",
    )

    # Mock revoke_access to avoid HTTP call
    svc.client.revoke_access = MagicMock(return_value=True)

    result = svc.disconnect(test_user["id"])
    assert result is True

    # Connection should be gone
    conn = svc.connection_repo.get_by_user_id(test_user["id"])
    assert conn is None


def test_disconnect_no_connection(temp_db, test_user):
    """disconnect succeeds gracefully when no connection exists."""
    svc = WhoopService()
    result = svc.disconnect(test_user["id"])
    assert result is True


# ------------------------------------------------------------------ #
# set_auto_fill_readiness
# ------------------------------------------------------------------ #


def test_set_auto_fill_readiness_enable(temp_db, test_user):
    """set_auto_fill_readiness returns the toggled value."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    # Need an existing connection to update
    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )

    result = svc.set_auto_fill_readiness(test_user["id"], True)
    assert result == {"auto_fill_readiness": True}


def test_set_auto_fill_readiness_disable(temp_db, test_user):
    """set_auto_fill_readiness can disable the toggle."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )

    svc.set_auto_fill_readiness(test_user["id"], True)
    result = svc.set_auto_fill_readiness(test_user["id"], False)
    assert result == {"auto_fill_readiness": False}


# ------------------------------------------------------------------ #
# set_auto_create_sessions
# ------------------------------------------------------------------ #


def test_set_auto_create_sessions_enable(temp_db, test_user):
    """set_auto_create_sessions triggers backfill when enabling."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )

    # Mock auto_create to avoid needing cached workouts
    with patch.object(
        svc,
        "auto_create_sessions_for_workouts",
        return_value=[],
    ):
        result = svc.set_auto_create_sessions(test_user["id"], True)

    assert result["auto_create_sessions"] is True
    assert result["backfilled"] == 0


def test_set_auto_create_sessions_disable(temp_db, test_user):
    """set_auto_create_sessions disabling skips backfill."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )

    result = svc.set_auto_create_sessions(test_user["id"], False)
    assert result["auto_create_sessions"] is False
    assert result["backfilled"] == 0


# ------------------------------------------------------------------ #
# check_scope_compatibility
# ------------------------------------------------------------------ #


def test_check_scope_compatibility_no_connection(temp_db, test_user):
    """check_scope_compatibility flags needs_reauth when disconnected."""
    svc = WhoopService()
    result = svc.check_scope_compatibility(test_user["id"])

    assert result["needs_reauth"] is True
    assert len(result["missing_scopes"]) > 0
    assert result["current_scopes"] == []


def test_check_scope_compatibility_all_scopes(temp_db, test_user):
    """check_scope_compatibility returns no missing when fully scoped."""
    from rivaflow.core.services.whoop_client import WHOOP_SCOPES
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        scopes=WHOOP_SCOPES,
    )

    result = svc.check_scope_compatibility(test_user["id"])
    assert result["needs_reauth"] is False
    assert result["missing_scopes"] == []


def test_check_scope_partial(temp_db, test_user):
    """check_scope_compatibility detects missing scopes."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("fake"),
        refresh_token_encrypted=encrypt_token("fake"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        scopes="read:workout",
    )

    result = svc.check_scope_compatibility(test_user["id"])
    assert result["needs_reauth"] is True
    assert "read:recovery" in result["missing_scopes"]


# ------------------------------------------------------------------ #
# handle_callback (mocked external calls)
# ------------------------------------------------------------------ #


def test_handle_callback_success(temp_db, test_user):
    """handle_callback exchanges code, stores connection, returns dict."""
    svc = WhoopService()

    # Create a valid state token
    state_token = "test-state-abc"
    expires = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
    svc.state_repo.create(test_user["id"], state_token, expires)

    # Mock external HTTP calls
    svc.client.exchange_code = MagicMock(
        return_value={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
            "scope": "read:workout read:recovery",
        }
    )
    svc.client.get_profile = MagicMock(return_value={"user_id": "whoop-789"})

    result = svc.handle_callback("auth-code-xyz", state_token)

    assert result["connected"] is True
    assert result["user_id"] == test_user["id"]
    assert result["whoop_user_id"] == "whoop-789"

    # Verify connection stored
    conn = svc.connection_repo.get_by_user_id(test_user["id"])
    assert conn is not None


def test_handle_callback_invalid_state(temp_db, test_user):
    """handle_callback raises ValidationError for bad state token."""
    from rivaflow.core.exceptions import ValidationError

    svc = WhoopService()

    with pytest.raises(ValidationError):
        svc.handle_callback("code", "invalid-state")


# ------------------------------------------------------------------ #
# get_valid_access_token (mocked)
# ------------------------------------------------------------------ #


def test_get_valid_access_token_fresh(temp_db, test_user):
    """get_valid_access_token returns token directly if not expired."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    # Store a connection with a future expiry
    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("my-access-token"),
        refresh_token_encrypted=encrypt_token("my-refresh"),
        token_expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    )

    token = svc.get_valid_access_token(test_user["id"])
    assert token == "my-access-token"


def test_get_valid_access_token_expired_refreshes(temp_db, test_user):
    """get_valid_access_token refreshes when token is about to expire."""
    from rivaflow.core.utils.encryption import encrypt_token

    svc = WhoopService()

    # Store a connection that expires soon (within 5-min buffer)
    svc.connection_repo.upsert(
        user_id=test_user["id"],
        access_token_encrypted=encrypt_token("old-access"),
        refresh_token_encrypted=encrypt_token("old-refresh"),
        token_expires_at=(datetime.now(UTC) + timedelta(minutes=2)).isoformat(),
    )

    # Mock the refresh call
    svc.client.refresh_tokens = MagicMock(
        return_value={
            "access_token": "refreshed-access",
            "refresh_token": "refreshed-refresh",
            "expires_in": 7200,
        }
    )

    token = svc.get_valid_access_token(test_user["id"])
    assert token == "refreshed-access"
    svc.client.refresh_tokens.assert_called_once()


def test_get_valid_access_token_not_connected(temp_db, test_user):
    """get_valid_access_token raises NotFoundError when disconnected."""
    from rivaflow.core.exceptions import NotFoundError

    svc = WhoopService()
    with pytest.raises(NotFoundError):
        svc.get_valid_access_token(test_user["id"])
