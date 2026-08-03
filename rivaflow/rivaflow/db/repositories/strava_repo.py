"""Repository for the Strava OAuth integration (connections + activity cache).

Strava is the replacement capture path for RivaFlow biometrics: a Wahoo (or any
other device that auto-uploads to Strava) lands the workout in Strava, and the
sync pulls it here. Tokens are stored Fernet-encrypted — this repository deals in
ciphertext only and never decrypts. Decryption lives in the service layer.

Writes are idempotent: the activity cache is keyed on (user_id, strava_activity_id)
so re-running a sync over a range already synced updates in place instead of
duplicating. That is what makes a backfill safe to re-run.
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

# How long an OAuth state token stays valid. Long enough to survive a slow
# consent screen, short enough that a leaked redirect URL is useless later.
_STATE_TTL_MINUTES = 15

_CONNECTION_COLS = (
    "id, user_id, athlete_id, access_token_encrypted, refresh_token_encrypted, "
    "token_expires_at, scopes, connected_at, last_synced_at, auto_create_sessions, "
    "is_active"
)

# Nullable data fields. On conflict these COALESCE, so a summary-only re-sync
# (which carries no heart rate) never wipes what an earlier detail fetch stored.
_NULLABLE_ACTIVITY_FIELDS = [
    "external_id",
    "name",
    "activity_type",
    "sport_type",
    "start_time",
    "start_time_local",
    "timezone",
    "elapsed_time_sec",
    "moving_time_sec",
    "distance_m",
    "avg_heart_rate",
    "max_heart_rate",
    "calories",
    "kilojoules",
    "suffer_score",
    "device_name",
    "raw_data",
]

# NOT NULL booleans describing the activity itself. These come from Strava on
# every payload, so a plain overwrite is correct — an activity edited from
# trainer=true to trainer=false should follow. None coerces to False rather than
# violating the NOT NULL constraint.
_BOOL_ACTIVITY_FIELDS = ["has_heartrate", "trainer", "manual"]

# Our own bookkeeping, not Strava's: once a detail fetch has succeeded the flag
# must stay set, otherwise every subsequent sync re-spends a detail call on an
# activity it already enriched.
_STICKY_BOOL_ACTIVITY_FIELDS = ["detail_fetched"]

_ACTIVITY_FIELDS = (
    _NULLABLE_ACTIVITY_FIELDS + _BOOL_ACTIVITY_FIELDS + _STICKY_BOOL_ACTIVITY_FIELDS
)


class StravaRepository(BaseRepository):
    """Data access for strava_connections, strava_activity_cache, strava_oauth_states."""

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    @staticmethod
    def get_connection_row(user_id: int) -> dict | None:
        """The user's active Strava connection, or None if not connected."""
        return BaseRepository._fetchone(
            convert_query(
                f"SELECT {_CONNECTION_COLS} FROM strava_connections "
                "WHERE user_id = ? AND is_active = TRUE"
            ),
            (user_id,),
        )

    @staticmethod
    def upsert_connection(
        user_id: int,
        athlete_id: str | None,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: datetime,
        scopes: str | None,
    ) -> None:
        """Store (or replace) a user's Strava tokens.

        Reconnecting reactivates the row and resets the tokens, but deliberately
        preserves last_synced_at and auto_create_sessions so a re-auth after an
        expired refresh token does not silently re-import everything or flip the
        user's auto-create preference back to the default.
        """
        query = convert_query(
            "INSERT INTO strava_connections "
            "(user_id, athlete_id, access_token_encrypted, refresh_token_encrypted, "
            " token_expires_at, scopes, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, TRUE) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "  athlete_id = excluded.athlete_id, "
            "  access_token_encrypted = excluded.access_token_encrypted, "
            "  refresh_token_encrypted = excluded.refresh_token_encrypted, "
            "  token_expires_at = excluded.token_expires_at, "
            "  scopes = excluded.scopes, "
            "  is_active = TRUE, "
            "  updated_at = CURRENT_TIMESTAMP"
        )
        with get_connection() as conn:
            conn.cursor().execute(
                query,
                (
                    user_id,
                    athlete_id,
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at,
                    scopes,
                ),
            )

    @staticmethod
    def update_tokens(
        user_id: int,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: datetime,
    ) -> None:
        """Persist rotated tokens after a refresh.

        Strava rotates the refresh token on every refresh, so failing to persist
        the new one here bricks the connection on the following sync.
        """
        with get_connection() as conn:
            conn.cursor().execute(
                convert_query(
                    "UPDATE strava_connections SET "
                    "access_token_encrypted = ?, refresh_token_encrypted = ?, "
                    "token_expires_at = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE user_id = ?"
                ),
                (
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at,
                    user_id,
                ),
            )

    @staticmethod
    def set_last_synced(user_id: int, when: datetime | None = None) -> None:
        """Stamp the connection with the end of a successful sync."""
        with get_connection() as conn:
            conn.cursor().execute(
                convert_query(
                    "UPDATE strava_connections SET last_synced_at = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
                ),
                (when or datetime.now(UTC), user_id),
            )

    @staticmethod
    def set_auto_create(user_id: int, enabled: bool) -> None:
        """Toggle whether syncs may auto-create sessions for this user."""
        with get_connection() as conn:
            conn.cursor().execute(
                convert_query(
                    "UPDATE strava_connections SET auto_create_sessions = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
                ),
                (bool(enabled), user_id),
            )

    @staticmethod
    def disconnect(user_id: int) -> bool:
        """Deactivate the connection and drop the stored tokens.

        The activity cache is left in place so previously imported sessions keep
        their provenance link and are not re-imported on reconnect.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE strava_connections SET is_active = FALSE, "
                    "access_token_encrypted = '', refresh_token_encrypted = '', "
                    "updated_at = CURRENT_TIMESTAMP "
                    "WHERE user_id = ? AND is_active = TRUE"
                ),
                (user_id,),
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # OAuth CSRF state
    # ------------------------------------------------------------------

    @staticmethod
    def create_state(user_id: int) -> str:
        """Mint a single-use CSRF state token for the authorize redirect."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(minutes=_STATE_TTL_MINUTES)
        with get_connection() as conn:
            conn.cursor().execute(
                convert_query(
                    "INSERT INTO strava_oauth_states (state_token, user_id, expires_at) "
                    "VALUES (?, ?, ?)"
                ),
                (token, user_id, expires_at),
            )
        return token

    @staticmethod
    def consume_state(state_token: str) -> int | None:
        """Redeem a state token, returning its user_id (None if invalid/expired).

        Deletes the row as it reads it, so a replayed callback fails.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "DELETE FROM strava_oauth_states WHERE state_token = ? "
                    "RETURNING user_id, expires_at"
                ),
                (state_token,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            row = dict(row)
            expires_at = row["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < datetime.now(UTC):
                return None
            return row["user_id"]

    @staticmethod
    def purge_expired_states() -> int:
        """Delete state tokens that were never redeemed."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM strava_oauth_states WHERE expires_at < ?"),
                (datetime.now(UTC),),
            )
            return cursor.rowcount or 0

    # ------------------------------------------------------------------
    # Activity cache
    # ------------------------------------------------------------------

    @staticmethod
    def upsert_activity(
        user_id: int, strava_activity_id: str, **fields: Any
    ) -> tuple[int, bool]:
        """Insert or update one cached activity.

        Returns ``(cache_id, created)``. Three different merge rules apply:

        - nullable data fields COALESCE, so a summary-only re-sync never wipes
          the heart rate and calories an earlier detail fetch stored
        - the NOT NULL activity booleans overwrite, and coerce None to False
        - ``detail_fetched`` is sticky-OR — once enriched, always enriched

        session_id and dismissed are intentionally not touched here: a re-sync
        must never unlink an imported session or un-dismiss a hidden activity.
        """
        raw = fields.get("raw_data")
        if raw is not None and not isinstance(raw, str):
            fields["raw_data"] = json.dumps(raw)

        cols = ["user_id", "strava_activity_id"] + _ACTIVITY_FIELDS
        placeholders = ", ".join(["?"] * len(cols))
        values: list[Any] = [user_id, strava_activity_id]
        values += [fields.get(f) for f in _NULLABLE_ACTIVITY_FIELDS]
        # NOT NULL columns — an omitted flag means "not set", not "null".
        values += [
            bool(fields.get(f))
            for f in _BOOL_ACTIVITY_FIELDS + _STICKY_BOOL_ACTIVITY_FIELDS
        ]

        set_parts = [
            f"{f} = COALESCE(excluded.{f}, strava_activity_cache.{f})"
            for f in _NULLABLE_ACTIVITY_FIELDS
        ]
        set_parts += [f"{f} = excluded.{f}" for f in _BOOL_ACTIVITY_FIELDS]
        set_parts += [
            f"{f} = (strava_activity_cache.{f} OR excluded.{f})"
            for f in _STICKY_BOOL_ACTIVITY_FIELDS
        ]
        set_clause = ", ".join(set_parts)
        query = convert_query(
            f"INSERT INTO strava_activity_cache ({', '.join(cols)}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT(user_id, strava_activity_id) DO UPDATE SET "
            f"{set_clause}, synced_at = CURRENT_TIMESTAMP "
            f"RETURNING id, (xmax = 0) AS created"
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            row = dict(cursor.fetchone())
            return row["id"], bool(row["created"])

    @staticmethod
    def get_activity(user_id: int, cache_id: int) -> dict | None:
        """One cached activity by its cache row id."""
        return BaseRepository._fetchone(
            convert_query(
                "SELECT * FROM strava_activity_cache WHERE id = ? AND user_id = ?"
            ),
            (cache_id, user_id),
        )

    @staticmethod
    def get_activity_by_strava_id(user_id: int, strava_activity_id: str) -> dict | None:
        """One cached activity by Strava's activity id."""
        return BaseRepository._fetchone(
            convert_query(
                "SELECT * FROM strava_activity_cache "
                "WHERE user_id = ? AND strava_activity_id = ?"
            ),
            (user_id, str(strava_activity_id)),
        )

    @staticmethod
    def list_activities(
        user_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
        include_dismissed: bool = False,
    ) -> list[dict]:
        """Cached activities in a window, newest first."""
        query = "SELECT * FROM strava_activity_cache WHERE user_id = ?"
        params: list[Any] = [user_id]
        if start is not None:
            query += " AND start_time >= ?"
            params.append(start)
        if end is not None:
            query += " AND start_time <= ?"
            params.append(end)
        if not include_dismissed:
            query += " AND dismissed = FALSE"
        query += " ORDER BY start_time DESC"
        return BaseRepository._fetchall(convert_query(query), tuple(params))

    @staticmethod
    def list_unlinked(user_id: int, limit: int = 100) -> list[dict]:
        """Cached activities not yet attached to a session and not dismissed."""
        return BaseRepository._fetchall(
            convert_query(
                "SELECT * FROM strava_activity_cache "
                "WHERE user_id = ? AND session_id IS NULL AND dismissed = FALSE "
                "ORDER BY start_time DESC LIMIT ?"
            ),
            (user_id, limit),
        )

    @staticmethod
    def link_session(user_id: int, cache_id: int, session_id: int) -> bool:
        """Attach a cached activity to a RivaFlow session."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE strava_activity_cache SET session_id = ? "
                    "WHERE id = ? AND user_id = ?"
                ),
                (session_id, cache_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def dismiss(user_id: int, cache_id: int, dismissed: bool = True) -> bool:
        """Hide (or unhide) an activity from the import list."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "UPDATE strava_activity_cache SET dismissed = ? "
                    "WHERE id = ? AND user_id = ?"
                ),
                (bool(dismissed), cache_id, user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def count_for_user(user_id: int) -> int:
        """Total cached activities — drives the status endpoint's summary."""
        row = BaseRepository._fetchone(
            convert_query(
                "SELECT COUNT(*) AS n FROM strava_activity_cache WHERE user_id = ?"
            ),
            (user_id,),
        )
        return int(row["n"]) if row else 0
