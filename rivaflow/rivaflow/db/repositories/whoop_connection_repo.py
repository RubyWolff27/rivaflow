"""Repository for WHOOP OAuth connection storage."""

from datetime import UTC, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class WhoopConnectionRepository:
    """Data access layer for whoop_connections table."""

    @staticmethod
    def create(
        user_id: int,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: str,
        whoop_user_id: str | None = None,
        scopes: str | None = None,
    ) -> int:
        """Create a new WHOOP connection and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO whoop_connections (
                    user_id, whoop_user_id, access_token_encrypted,
                    refresh_token_encrypted, token_expires_at, scopes
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    whoop_user_id,
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at,
                    scopes,
                ),
            )

    @staticmethod
    def get_by_user_id(user_id: int) -> dict | None:
        """Get the WHOOP connection for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM whoop_connections WHERE user_id = ?"),
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return WhoopConnectionRepository._row_to_dict(row)

    @staticmethod
    def update_tokens(
        user_id: int,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: str,
    ) -> bool:
        """Update OAuth tokens for a user's connection."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_connections
                    SET access_token_encrypted = ?,
                        refresh_token_encrypted = ?,
                        token_expires_at = ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """),
                (
                    access_token_encrypted,
                    refresh_token_encrypted,
                    token_expires_at,
                    _now_iso(),
                    user_id,
                ),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_last_synced(user_id: int) -> bool:
        """Update the last_synced_at timestamp."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_connections
                    SET last_synced_at = ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """),
                (_now_iso(), _now_iso(), user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def upsert(
        user_id: int,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: str,
        whoop_user_id: str | None = None,
        scopes: str | None = None,
    ) -> int:
        """Create or update a WHOOP connection. Returns the connection ID."""
        existing = WhoopConnectionRepository.get_by_user_id(user_id)
        if existing:
            WhoopConnectionRepository.update_tokens(
                user_id,
                access_token_encrypted,
                refresh_token_encrypted,
                token_expires_at,
            )
            # Also update whoop_user_id and scopes if provided
            if whoop_user_id or scopes:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        convert_query("""
                            UPDATE whoop_connections
                            SET whoop_user_id = COALESCE(?, whoop_user_id),
                                scopes = COALESCE(?, scopes),
                                is_active = 1,
                                updated_at = ?
                            WHERE user_id = ?
                            """),
                        (whoop_user_id, scopes, _now_iso(), user_id),
                    )
            return existing["id"]
        return WhoopConnectionRepository.create(
            user_id,
            access_token_encrypted,
            refresh_token_encrypted,
            token_expires_at,
            whoop_user_id,
            scopes,
        )

    @staticmethod
    def delete(user_id: int) -> bool:
        """Delete a user's WHOOP connection (cascade deletes workout cache)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM whoop_connections WHERE user_id = ?"),
                (user_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_auto_create(user_id: int, enabled: bool) -> bool:
        """Toggle auto_create_sessions preference."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_connections
                    SET auto_create_sessions = ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """),
                (1 if enabled else 0, _now_iso(), user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_auto_fill_readiness(user_id: int, enabled: bool) -> bool:
        """Toggle auto_fill_readiness preference."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE whoop_connections
                    SET auto_fill_readiness = ?,
                        updated_at = ?
                    WHERE user_id = ?
                    """),
                (1 if enabled else 0, _now_iso(), user_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        if hasattr(row, "keys"):
            return dict(row)
        columns = [
            "id",
            "user_id",
            "whoop_user_id",
            "access_token_encrypted",
            "refresh_token_encrypted",
            "token_expires_at",
            "scopes",
            "connected_at",
            "last_synced_at",
            "is_active",
            "created_at",
            "updated_at",
            "auto_create_sessions",
            "auto_fill_readiness",
        ]
        return {col: row[i] for i, col in enumerate(columns)}
