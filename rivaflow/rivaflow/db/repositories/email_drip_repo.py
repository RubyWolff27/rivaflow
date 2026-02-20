"""Repository for email drip log tracking."""

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class EmailDripRepository(BaseRepository):
    """Track which drip emails have been sent to which users."""

    @staticmethod
    def has_been_sent(user_id: int, email_key: str) -> bool:
        """Check if a drip email has already been sent to a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT 1 FROM email_drip_log"
                    " WHERE user_id = ? AND email_key = ?"
                ),
                (user_id, email_key),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def mark_sent(user_id: int, email_key: str) -> None:
        """Record that a drip email was sent."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "INSERT OR IGNORE INTO email_drip_log"
                    " (user_id, email_key) VALUES (?, ?)"
                ),
                (user_id, email_key),
            )
