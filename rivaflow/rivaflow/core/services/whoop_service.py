"""Business logic for WHOOP integration -- OAuth, sync, and matching."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from datetime import timezone as tz

from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.whoop_client import (
    WHOOP_SCOPES,
    WhoopClient,
)
from rivaflow.core.services.whoop_sync_service import (
    apply_recovery_to_readiness,
    auto_fill_readiness_from_recovery,
    backfill_session_timezones,
    get_latest_recovery,
    sync_recovery,
    sync_workouts,
)
from rivaflow.core.services.whoop_workout_service import (
    apply_workout_to_session,
    auto_create_sessions_for_workouts,
    find_matching_workouts,
    find_matching_workouts_by_params,
)
from rivaflow.core.utils.encryption import (
    decrypt_token,
    encrypt_token,
)
from rivaflow.db.repositories.profile_repo import (
    ProfileRepository,
)
from rivaflow.db.repositories.session_repo import (
    SessionRepository,
)
from rivaflow.db.repositories.whoop_connection_repo import (
    WhoopConnectionRepository,
)
from rivaflow.db.repositories.whoop_oauth_state_repo import (
    WhoopOAuthStateRepository,
)
from rivaflow.db.repositories.whoop_recovery_cache_repo import (
    WhoopRecoveryCacheRepository,
)
from rivaflow.db.repositories.whoop_workout_cache_repo import (
    WhoopWorkoutCacheRepository,
)

logger = logging.getLogger(__name__)


def _parse_tz_offset(offset_str: str | None) -> tz | None:
    """Parse a timezone offset string like '+11:00' into a timezone."""
    if not offset_str:
        return None
    try:
        sign = 1 if offset_str.startswith("+") else -1
        parts = offset_str.lstrip("+-").split(":")
        hours = int(parts[0])
        mins = int(parts[1]) if len(parts) > 1 else 0
        return tz(timedelta(hours=sign * hours, minutes=sign * mins))
    except (ValueError, IndexError):
        return None


class WhoopService:
    """Central service for WHOOP integration logic."""

    # ------------------------------------------------------------------
    # Sync methods (delegated to whoop_sync_service)
    # ------------------------------------------------------------------
    sync_workouts = sync_workouts
    sync_recovery = sync_recovery
    get_latest_recovery = get_latest_recovery
    apply_recovery_to_readiness = apply_recovery_to_readiness
    auto_fill_readiness_from_recovery = auto_fill_readiness_from_recovery
    backfill_session_timezones = backfill_session_timezones

    # ------------------------------------------------------------------
    # Workout methods (delegated to whoop_workout_service)
    # ------------------------------------------------------------------
    find_matching_workouts = find_matching_workouts
    find_matching_workouts_by_params = find_matching_workouts_by_params
    apply_workout_to_session = apply_workout_to_session
    auto_create_sessions_for_workouts = auto_create_sessions_for_workouts

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def __init__(self):
        self.connection_repo = WhoopConnectionRepository()
        self.state_repo = WhoopOAuthStateRepository()
        self.workout_cache_repo = WhoopWorkoutCacheRepository()
        self.recovery_cache_repo = WhoopRecoveryCacheRepository()
        self.session_repo = SessionRepository()
        self.profile_repo = ProfileRepository()
        self.client = WhoopClient()

    # =================================================================
    # OAuth
    # =================================================================

    def initiate_oauth(self, user_id: int) -> str:
        """Generate a state token, persist it, and return the auth URL."""
        state_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()

        self.state_repo.create(user_id, state_token, expires_at)
        self.state_repo.cleanup_expired()

        return self.client.get_authorization_url(state_token)

    def handle_callback(self, code: str, state: str) -> dict:
        """Process the OAuth callback: validate state, exchange code, store."""
        state_row = self.state_repo.validate_and_consume(state)
        if not state_row:
            raise ValidationError("Invalid or expired OAuth state token")

        user_id = state_row["user_id"]

        # Exchange code for tokens
        token_data = self.client.exchange_code(code)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_in)
        ).isoformat()
        scopes = token_data.get("scope", "")

        # Get WHOOP user profile
        profile = self.client.get_profile(access_token)
        whoop_user_id = str(profile.get("user_id", ""))

        # Encrypt and store
        self.connection_repo.upsert(
            user_id=user_id,
            access_token_encrypted=encrypt_token(access_token),
            refresh_token_encrypted=encrypt_token(refresh_token),
            token_expires_at=token_expires_at,
            whoop_user_id=whoop_user_id,
            scopes=scopes,
        )

        return {
            "user_id": user_id,
            "whoop_user_id": whoop_user_id,
            "connected": True,
        }

    def get_valid_access_token(self, user_id: int) -> str:
        """Return a valid (possibly refreshed) access token for the user."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn:
            raise NotFoundError("WHOOP not connected")

        access_token = decrypt_token(conn["access_token_encrypted"])
        expires_at_str = conn["token_expires_at"]

        # Parse expiry
        if isinstance(expires_at_str, str):
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        else:
            expires_at = expires_at_str

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        # Refresh if within 5-minute buffer
        if expires_at < datetime.now(UTC) + timedelta(minutes=5):
            refresh_token = decrypt_token(conn["refresh_token_encrypted"])
            token_data = self.client.refresh_tokens(refresh_token)

            new_access = token_data["access_token"]
            new_refresh = token_data.get("refresh_token", refresh_token)
            new_expires = (
                datetime.now(UTC)
                + timedelta(seconds=token_data.get("expires_in", 3600))
            ).isoformat()

            self.connection_repo.update_tokens(
                user_id,
                encrypt_token(new_access),
                encrypt_token(new_refresh),
                new_expires,
            )
            return new_access

        return access_token

    # =================================================================
    # Scope checks
    # =================================================================

    def check_scope_compatibility(self, user_id: int) -> dict:
        """Compare stored scopes with current required scopes."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn:
            return {
                "current_scopes": [],
                "required_scopes": WHOOP_SCOPES.split(),
                "needs_reauth": True,
                "missing_scopes": WHOOP_SCOPES.split(),
            }

        current_str = conn.get("scopes", "") or ""
        current = set(current_str.split())
        required = set(WHOOP_SCOPES.split())
        missing = required - current

        return {
            "current_scopes": sorted(current),
            "required_scopes": sorted(required),
            "needs_reauth": len(missing) > 0,
            "missing_scopes": sorted(missing),
        }

    # =================================================================
    # Settings toggles
    # =================================================================

    def set_auto_fill_readiness(self, user_id: int, enabled: bool) -> dict:
        """Toggle auto-fill readiness preference."""
        self.connection_repo.update_auto_fill_readiness(user_id, enabled)
        return {"auto_fill_readiness": enabled}

    def set_auto_create_sessions(self, user_id: int, enabled: bool) -> dict:
        """Toggle auto-create and backfill if enabling."""
        self.connection_repo.update_auto_create(user_id, enabled)

        backfilled = 0
        if enabled:
            created_ids = self.auto_create_sessions_for_workouts(user_id)
            backfilled = len(created_ids)

        return {
            "auto_create_sessions": enabled,
            "backfilled": backfilled,
        }

    # =================================================================
    # Connection management
    # =================================================================

    def get_connection_status(self, user_id: int) -> dict:
        """Return connection status with metadata."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if not conn or not conn.get("is_active"):
            return {"connected": False}

        return {
            "connected": True,
            "whoop_user_id": conn.get("whoop_user_id"),
            "connected_at": conn.get("connected_at"),
            "last_synced_at": conn.get("last_synced_at"),
            "auto_create_sessions": bool(conn.get("auto_create_sessions")),
            "auto_fill_readiness": bool(conn.get("auto_fill_readiness")),
        }

    def disconnect(self, user_id: int) -> bool:
        """Disconnect WHOOP: revoke tokens, delete connection + cache."""
        conn = self.connection_repo.get_by_user_id(user_id)
        if conn:
            # Best-effort token revocation
            try:
                access_token = decrypt_token(conn["access_token_encrypted"])
                self.client.revoke_access(access_token)
            except Exception:
                logger.warning("Token revocation failed (best-effort)")

        # Delete cached workouts and recovery data
        self.workout_cache_repo.delete_by_user(user_id)
        self.recovery_cache_repo.delete_by_user(user_id)

        # Delete connection
        self.connection_repo.delete(user_id)

        # Clear WHOOP fields from linked sessions
        SessionRepository.clear_whoop_fields(user_id)

        return True
