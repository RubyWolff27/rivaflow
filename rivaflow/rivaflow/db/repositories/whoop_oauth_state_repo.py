"""Repository for short-lived WHOOP OAuth CSRF state tokens."""

from datetime import UTC, datetime

from rivaflow.db.database import convert_query, execute_insert, get_connection


class WhoopOAuthStateRepository:
    """Data access layer for whoop_oauth_states table."""

    @staticmethod
    def create(user_id: int, state_token: str, expires_at: str) -> int:
        """Store a new OAuth state token and return its ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                """
                INSERT INTO whoop_oauth_states (user_id, state_token, expires_at)
                VALUES (?, ?, ?)
                """,
                (user_id, state_token, expires_at),
            )

    @staticmethod
    def validate_and_consume(state_token: str) -> dict | None:
        """Validate a state token: fetch, check expiry, delete, and return.

        Returns the state row dict if valid, None if not found or expired.
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM whoop_oauth_states WHERE state_token = ?"),
                (state_token,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            state = WhoopOAuthStateRepository._row_to_dict(row)

            # Delete the token (single-use)
            cursor.execute(
                convert_query("DELETE FROM whoop_oauth_states WHERE state_token = ?"),
                (state_token,),
            )

            # Check expiry
            expires_at = datetime.fromisoformat(
                state["expires_at"].replace("Z", "+00:00")
                if isinstance(state["expires_at"], str)
                else str(state["expires_at"])
            )
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < datetime.now(UTC):
                return None

            return state

    @staticmethod
    def cleanup_expired() -> int:
        """Delete all expired state tokens. Returns count deleted."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("DELETE FROM whoop_oauth_states WHERE expires_at < ?"),
                (datetime.now(UTC).isoformat(),),
            )
            return cursor.rowcount

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a database row to a dictionary."""
        if hasattr(row, "keys"):
            return dict(row)
        columns = [
            "id",
            "state_token",
            "user_id",
            "expires_at",
            "created_at",
        ]
        return {col: row[i] for i, col in enumerate(columns)}
