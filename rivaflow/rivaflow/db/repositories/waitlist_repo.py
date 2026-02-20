"""Repository for waitlist data access."""

import secrets
from datetime import datetime, timedelta

from rivaflow.core.time_utils import utcnow
from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository


class WaitlistRepository(BaseRepository):
    """Data access layer for waitlist entries."""

    @staticmethod
    def create(
        email: str,
        first_name: str | None = None,
        gym_name: str | None = None,
        belt_rank: str | None = None,
        referral_source: str | None = None,
    ) -> dict:
        """
        Create a new waitlist entry and return it.

        Auto-assigns the next position based on MAX(position) + 1.

        Args:
            email: Email address (must be unique)
            first_name: Optional first name
            gym_name: Optional gym name
            belt_rank: Optional belt rank
            referral_source: Optional referral source

        Returns:
            The created waitlist entry as a dict
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get next position
            cursor.execute(
                convert_query(
                    "SELECT COALESCE(MAX(position), 0) + 1 AS next_pos FROM waitlist"
                )
            )
            row = cursor.fetchone()
            next_position = row["next_pos"]

            # Insert the entry
            entry_id = execute_insert(
                cursor,
                """
                INSERT INTO waitlist (
                    email, first_name, gym_name, belt_rank,
                    referral_source, position, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'waiting')
                """,
                (
                    email.lower().strip(),
                    first_name,
                    gym_name,
                    belt_rank,
                    referral_source,
                    next_position,
                ),
            )

        # Return the created entry (always exists after insert)
        return WaitlistRepository.get_by_id(entry_id)  # type: ignore[return-value]

    @staticmethod
    def get_by_id(waitlist_id: int) -> dict | None:
        """
        Get a waitlist entry by ID.

        Args:
            waitlist_id: Waitlist entry ID

        Returns:
            Entry dict or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM waitlist WHERE id = ?"),
                (waitlist_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        """
        Get a waitlist entry by email address.

        Args:
            email: Email address to look up

        Returns:
            Entry dict or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM waitlist WHERE email = ?"),
                (email.lower().strip(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    @staticmethod
    def get_by_invite_token(token: str) -> dict | None:
        """
        Get a waitlist entry by invite token.

        Args:
            token: Invite token string

        Returns:
            Entry dict or None if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("SELECT * FROM waitlist WHERE invite_token = ?"),
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    @staticmethod
    def list_all(
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """
        List waitlist entries with optional filters.

        Args:
            status: Filter by status (waiting, invited, registered, declined)
            search: Search by email or first_name
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entry dicts
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM waitlist WHERE 1=1"
            params: list = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if search:
                query += " AND (email LIKE ? OR first_name LIKE ?)"
                search_pattern = f"%{search}%"
                params.append(search_pattern)
                params.append(search_pattern)

            query += " ORDER BY position ASC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)

            cursor.execute(convert_query(query), params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_count(status: str | None = None) -> int:
        """
        Count waitlist entries, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            Count of matching entries
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    convert_query(
                        "SELECT COUNT(*) AS cnt FROM waitlist WHERE status = ?"
                    ),
                    (status,),
                )
            else:
                cursor.execute(convert_query("SELECT COUNT(*) AS cnt FROM waitlist"))

            row = cursor.fetchone()
            if not row:
                return 0
            return row["cnt"]

    @staticmethod
    def invite(waitlist_id: int, assigned_tier: str = "free") -> str | None:
        """
        Invite a waitlist entry by generating a secure invite token.

        Sets status='invited', assigns tier, and sets token expiry to 7 days.

        Args:
            waitlist_id: Waitlist entry ID
            assigned_tier: Tier to assign (free, premium, lifetime_premium)

        Returns:
            The plain invite token string, or None if entry not found
        """
        token = secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(days=7)
        invited_at = utcnow().isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE waitlist
                    SET status = 'invited',
                        invite_token = ?,
                        invite_token_expires_at = ?,
                        invited_at = ?,
                        assigned_tier = ?
                    WHERE id = ?
                    """),
                (
                    token,
                    expires_at.isoformat(),
                    invited_at,
                    assigned_tier,
                    waitlist_id,
                ),
            )

            if cursor.rowcount == 0:
                return None

        return token

    @staticmethod
    def bulk_invite(
        waitlist_ids: list[int], assigned_tier: str = "free"
    ) -> list[tuple[int, str, str]]:
        """
        Invite multiple waitlist entries.

        Args:
            waitlist_ids: List of waitlist entry IDs to invite
            assigned_tier: Tier to assign to all entries

        Returns:
            List of (id, email, token) tuples for successfully invited entries
        """
        results = []

        for wid in waitlist_ids:
            entry = WaitlistRepository.get_by_id(wid)
            if not entry:
                continue

            token = WaitlistRepository.invite(wid, assigned_tier)
            if token:
                results.append((wid, entry["email"], token))

        return results

    @staticmethod
    def mark_registered(email: str) -> bool:
        """
        Mark a waitlist entry as registered.

        Sets status='registered' and registered_at to current time.

        Args:
            email: Email address of the waitlist entry

        Returns:
            True if updated, False if not found
        """
        registered_at = utcnow().isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("""
                    UPDATE waitlist
                    SET status = 'registered', registered_at = ?
                    WHERE email = ?
                    """),
                (registered_at, email.lower().strip()),
            )
            return cursor.rowcount > 0

    @staticmethod
    def decline(waitlist_id: int) -> bool:
        """
        Decline a waitlist entry.

        Sets status='declined'.

        Args:
            waitlist_id: Waitlist entry ID

        Returns:
            True if updated, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE waitlist SET status = 'declined' WHERE id = ?"),
                (waitlist_id,),
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_notes(waitlist_id: int, notes: str) -> bool:
        """
        Update admin notes for a waitlist entry.

        Args:
            waitlist_id: Waitlist entry ID
            notes: Admin notes text

        Returns:
            True if updated, False if not found
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE waitlist SET notes = ? WHERE id = ?"),
                (notes, waitlist_id),
            )
            return cursor.rowcount > 0

    @staticmethod
    def is_invite_valid(token: str) -> bool:
        """
        Check if an invite token is valid.

        A token is valid if it exists, status is 'invited', and it has not expired.

        Args:
            token: Invite token string

        Returns:
            True if valid, False otherwise
        """
        entry = WaitlistRepository.get_by_invite_token(token)

        if not entry:
            return False

        if entry.get("status") != "invited":
            return False

        # Check expiry
        expires_at = entry.get("invite_token_expires_at")
        if not expires_at:
            return False

        # Handle both PostgreSQL (datetime object) and SQLite (string)
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)

        if utcnow() > expires_at:
            return False

        return True

    @staticmethod
    def get_waiting_count() -> int:
        """
        Get the count of entries with status='waiting'.

        Returns:
            Number of people currently waiting
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT COUNT(*) AS cnt FROM waitlist WHERE status = 'waiting'"
                )
            )
            row = cursor.fetchone()
            if not row:
                return 0
            return row["cnt"]
