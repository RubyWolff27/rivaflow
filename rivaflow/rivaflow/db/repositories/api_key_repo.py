"""Repository for API key authentication tokens.

Per `feat/api-keys` PR — user-equivalent API keys for service-to-service use
(Sage MCP integration today; future iOS sync / external webhooks tomorrow).
Keys are stored as SHA-256 hashes; raw key material is only revealed once at
creation time.
"""

from __future__ import annotations

import hashlib
import secrets

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

# Public-facing prefix for all RivaFlow API keys: "rf_pk_" + 32 hex chars.
# `rf` = RivaFlow, `pk` = "personal key" (room to add e.g. `rf_sk_` for service
# keys later without colliding).
KEY_PREFIX_LITERAL = "rf_pk_"
KEY_BODY_LENGTH = 32  # hex characters after the prefix
KEY_DISPLAY_PREFIX_LENGTH = len(KEY_PREFIX_LITERAL) + 6  # "rf_pk_" + first 6 of body


class ApiKeyRepository(BaseRepository):
    """Data access layer for the api_keys table."""

    @staticmethod
    def generate_raw_key() -> str:
        """Generate a fresh API key — returned only once at creation time."""
        return KEY_PREFIX_LITERAL + secrets.token_hex(KEY_BODY_LENGTH // 2)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """SHA-256 hash of a raw key — what we persist + match against."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def display_prefix(raw_key: str) -> str:
        """Short identifier safe to show in lists: first 12 chars."""
        return raw_key[:KEY_DISPLAY_PREFIX_LENGTH]

    @staticmethod
    def create(
        *,
        user_id: int,
        name: str,
        raw_key: str,
    ) -> dict | None:
        """Create a new API key row.

        Args:
            user_id: Owning user.
            name: Human label (e.g. "Sage MCP", "iOS app").
            raw_key: Already-generated raw key (caller hashes via
                `ApiKeyRepository.hash_key` and we store only the hash).

        Returns:
            Created row as dict (without the raw key — caller is responsible
            for returning the raw key to the user exactly once), or None if
            the post-insert SELECT mysteriously returns no row.
        """
        key_hash = ApiKeyRepository.hash_key(raw_key)
        key_prefix = ApiKeyRepository.display_prefix(raw_key)
        with get_connection() as conn:
            cursor = conn.cursor()
            api_key_id = execute_insert(
                cursor,
                """
                INSERT INTO api_keys (user_id, name, key_hash, key_prefix)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, name, key_hash, key_prefix),
            )

            cursor.execute(
                convert_query(
                    """
                    SELECT id, user_id, name, key_prefix, created_at,
                           last_used_at, revoked_at
                    FROM api_keys
                    WHERE id = ?
                    """
                ),
                (api_key_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_by_user(user_id: int) -> list[dict]:
        """Return all API keys belonging to a user (active + revoked).

        Raw key material is NEVER returned — only metadata + the display prefix.
        """
        return BaseRepository._fetchall(
            """
            SELECT id, user_id, name, key_prefix, created_at,
                   last_used_at, revoked_at
            FROM api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

    @staticmethod
    def get_active_by_hash(key_hash: str) -> dict | None:
        """Lookup by hash, only returns non-revoked keys.

        Used by the auth dependency on every request that authenticates with
        an API key. The query is indexed on key_hash for O(1).
        """
        return BaseRepository._fetchone(
            """
            SELECT id, user_id, name, key_prefix, created_at,
                   last_used_at, revoked_at
            FROM api_keys
            WHERE key_hash = ? AND revoked_at IS NULL
            """,
            (key_hash,),
        )

    @staticmethod
    def update_last_used(api_key_id: int) -> None:
        """Bump last_used_at to now. Called from the auth path post-validation."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    """UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?"""
                ),
                (api_key_id,),
            )

    @staticmethod
    def revoke(api_key_id: int, user_id: int) -> bool:
        """Mark the key revoked. Returns True iff a row was updated.

        Guarded by user_id so a user can only revoke their own keys (route layer
        already checks via current_user; double-checking here defends against
        repository misuse).
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE api_keys
                    SET revoked_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ? AND revoked_at IS NULL
                    """),
                (api_key_id, user_id),
            )
            return cursor.rowcount > 0
