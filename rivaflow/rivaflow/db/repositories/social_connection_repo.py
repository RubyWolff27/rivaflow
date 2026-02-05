"""Repository for friend connections (requests, friendships, blocking)."""

from typing import Any

from rivaflow.db.database import convert_query, execute_insert, get_connection


class SocialConnectionRepository:
    """Data access layer for friend connections."""

    @staticmethod
    def send_friend_request(
        requester_id: int,
        recipient_id: int,
        connection_source: str | None = None,
        request_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a friend request.

        Args:
            requester_id: User sending the request
            recipient_id: User receiving the request
            connection_source: How they found each other (gym, mutual, search, etc.)
            request_message: Optional message with request

        Returns:
            Created connection record

        Raises:
            ValueError: If users are already connected or request already pending
        """
        if requester_id == recipient_id:
            raise ValueError("Cannot send friend request to yourself")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if already connected or pending
            cursor.execute(
                convert_query(
                    """
                    SELECT id, status FROM friend_connections
                    WHERE (requester_id = ? AND recipient_id = ?)
                       OR (requester_id = ? AND recipient_id = ?)
                """
                ),
                (requester_id, recipient_id, recipient_id, requester_id),
            )
            existing = cursor.fetchone()

            if existing:
                status = dict(existing)["status"]
                if status == "accepted":
                    raise ValueError("Already friends")
                elif status == "pending":
                    raise ValueError("Friend request already pending")
                elif status == "blocked":
                    raise ValueError("Cannot send friend request")

            # Check if either user has blocked the other
            cursor.execute(
                convert_query(
                    """
                    SELECT 1 FROM blocked_users
                    WHERE (blocker_id = ? AND blocked_id = ?)
                       OR (blocker_id = ? AND blocked_id = ?)
                """
                ),
                (requester_id, recipient_id, recipient_id, requester_id),
            )
            if cursor.fetchone():
                raise ValueError("Cannot send friend request")

            # Create friend request
            connection_id = execute_insert(
                cursor,
                """
                INSERT INTO friend_connections
                (requester_id, recipient_id, status, connection_source, request_message)
                VALUES (?, ?, 'pending', ?, ?)
                """,
                (requester_id, recipient_id, connection_source, request_message),
            )

            cursor.execute(
                convert_query("SELECT * FROM friend_connections WHERE id = ?"),
                (connection_id,),
            )
            row = cursor.fetchone()
            return SocialConnectionRepository._row_to_dict(row)

    @staticmethod
    def accept_friend_request(connection_id: int, recipient_id: int) -> dict[str, Any]:
        """
        Accept a friend request (must be the recipient).

        Args:
            connection_id: ID of the friend request
            recipient_id: User accepting (must be recipient)

        Returns:
            Updated connection record

        Raises:
            ValueError: If not found or not authorized
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify user is recipient and status is pending
            cursor.execute(
                convert_query(
                    """
                    SELECT * FROM friend_connections
                    WHERE id = ? AND recipient_id = ? AND status = 'pending'
                """
                ),
                (connection_id, recipient_id),
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError("Friend request not found or already responded")

            # Update to accepted
            cursor.execute(
                convert_query(
                    """
                    UPDATE friend_connections
                    SET status = 'accepted', responded_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                ),
                (connection_id,),
            )

            # Return updated record
            cursor.execute(
                convert_query("SELECT * FROM friend_connections WHERE id = ?"),
                (connection_id,),
            )
            row = cursor.fetchone()
            return SocialConnectionRepository._row_to_dict(row)

    @staticmethod
    def decline_friend_request(connection_id: int, recipient_id: int) -> dict[str, Any]:
        """
        Decline a friend request (must be the recipient).

        Args:
            connection_id: ID of the friend request
            recipient_id: User declining (must be recipient)

        Returns:
            Updated connection record
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verify user is recipient and status is pending
            cursor.execute(
                convert_query(
                    """
                    SELECT * FROM friend_connections
                    WHERE id = ? AND recipient_id = ? AND status = 'pending'
                """
                ),
                (connection_id, recipient_id),
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError("Friend request not found or already responded")

            # Update to declined
            cursor.execute(
                convert_query(
                    """
                    UPDATE friend_connections
                    SET status = 'declined', responded_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                ),
                (connection_id,),
            )

            cursor.execute(
                convert_query("SELECT * FROM friend_connections WHERE id = ?"),
                (connection_id,),
            )
            row = cursor.fetchone()
            return SocialConnectionRepository._row_to_dict(row)

    @staticmethod
    def cancel_friend_request(connection_id: int, requester_id: int) -> bool:
        """
        Cancel a sent friend request (must be the requester).

        Args:
            connection_id: ID of the friend request
            requester_id: User canceling (must be requester)

        Returns:
            True if cancelled successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    UPDATE friend_connections
                    SET status = 'cancelled'
                    WHERE id = ? AND requester_id = ? AND status = 'pending'
                """
                ),
                (connection_id, requester_id),
            )

            return cursor.rowcount > 0

    @staticmethod
    def unfriend(user_id: int, friend_user_id: int) -> bool:
        """
        Remove a friend connection.

        Args:
            user_id: User removing the friend
            friend_user_id: User being removed

        Returns:
            True if removed successfully
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    DELETE FROM friend_connections
                    WHERE status = 'accepted'
                      AND ((requester_id = ? AND recipient_id = ?)
                        OR (requester_id = ? AND recipient_id = ?))
                """
                ),
                (user_id, friend_user_id, friend_user_id, user_id),
            )

            return cursor.rowcount > 0

    @staticmethod
    def get_friends(user_id: int, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """
        Get list of accepted friends for a user.

        Args:
            user_id: User ID
            limit: Max results
            offset: Offset for pagination

        Returns:
            List of friend user records with connection info
        """
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT
                        u.id, u.username, u.display_name, u.belt_rank, u.belt_stripes,
                        u.profile_photo_url, u.primary_gym_id, u.location_city, u.location_state,
                        fc.created_at as friends_since, fc.connection_source
                    FROM friend_connections fc
                    JOIN users u ON (
                        CASE
                            WHEN fc.requester_id = ? THEN u.id = fc.recipient_id
                            WHEN fc.recipient_id = ? THEN u.id = fc.requester_id
                        END
                    )
                    WHERE fc.status = 'accepted'
                      AND (fc.requester_id = ? OR fc.recipient_id = ?)
                    ORDER BY u.display_name
                    LIMIT ? OFFSET ?
                """
                ),
                (user_id, user_id, user_id, user_id, limit, offset),
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_pending_requests_received(user_id: int) -> list[dict[str, Any]]:
        """Get pending friend requests received by user."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT
                        fc.*,
                        u.username as requester_username,
                        u.display_name as requester_display_name,
                        u.belt_rank as requester_belt_rank,
                        u.profile_photo_url as requester_photo_url
                    FROM friend_connections fc
                    JOIN users u ON u.id = fc.requester_id
                    WHERE fc.recipient_id = ? AND fc.status = 'pending'
                    ORDER BY fc.requested_at DESC
                """
                ),
                (user_id,),
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_pending_requests_sent(user_id: int) -> list[dict[str, Any]]:
        """Get pending friend requests sent by user."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT
                        fc.*,
                        u.username as recipient_username,
                        u.display_name as recipient_display_name,
                        u.belt_rank as recipient_belt_rank,
                        u.profile_photo_url as recipient_photo_url
                    FROM friend_connections fc
                    JOIN users u ON u.id = fc.recipient_id
                    WHERE fc.requester_id = ? AND fc.status = 'pending'
                    ORDER BY fc.requested_at DESC
                """
                ),
                (user_id,),
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_mutual_friends_count(user_id: int, other_user_id: int) -> int:
        """Get count of mutual friends between two users."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT COUNT(*) as count
                    FROM friend_connections fc1
                    JOIN friend_connections fc2 ON (
                        (fc1.requester_id = fc2.requester_id OR fc1.requester_id = fc2.recipient_id
                         OR fc1.recipient_id = fc2.requester_id OR fc1.recipient_id = fc2.recipient_id)
                        AND fc1.id != fc2.id
                    )
                    WHERE fc1.status = 'accepted' AND fc2.status = 'accepted'
                      AND ((fc1.requester_id = ? AND fc1.recipient_id != ?)
                        OR (fc1.recipient_id = ? AND fc1.requester_id != ?))
                      AND ((fc2.requester_id = ? AND fc2.recipient_id != ?)
                        OR (fc2.recipient_id = ? AND fc2.requester_id != ?))
                """
                ),
                (
                    user_id,
                    other_user_id,
                    user_id,
                    other_user_id,
                    other_user_id,
                    user_id,
                    other_user_id,
                    user_id,
                ),
            )

            row = cursor.fetchone()
            return dict(row)["count"] if row else 0

    @staticmethod
    def are_friends(user_id: int, other_user_id: int) -> bool:
        """Check if two users are friends."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT 1 FROM friend_connections
                    WHERE status = 'accepted'
                      AND ((requester_id = ? AND recipient_id = ?)
                        OR (requester_id = ? AND recipient_id = ?))
                """
                ),
                (user_id, other_user_id, other_user_id, user_id),
            )

            return cursor.fetchone() is not None

    @staticmethod
    def block_user(blocker_id: int, blocked_id: int, reason: str | None = None) -> dict[str, Any]:
        """Block a user."""
        if blocker_id == blocked_id:
            raise ValueError("Cannot block yourself")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Remove any existing friend connection
            cursor.execute(
                convert_query(
                    """
                    DELETE FROM friend_connections
                    WHERE (requester_id = ? AND recipient_id = ?)
                       OR (requester_id = ? AND recipient_id = ?)
                """
                ),
                (blocker_id, blocked_id, blocked_id, blocker_id),
            )

            # Add to blocked list
            block_id = execute_insert(
                cursor,
                """
                INSERT INTO blocked_users (blocker_id, blocked_id, reason)
                VALUES (?, ?, ?)
                ON CONFLICT (blocker_id, blocked_id) DO NOTHING
                """,
                (blocker_id, blocked_id, reason),
            )

            cursor.execute(convert_query("SELECT * FROM blocked_users WHERE id = ?"), (block_id,))
            row = cursor.fetchone()
            return SocialConnectionRepository._row_to_dict(row)

    @staticmethod
    def unblock_user(blocker_id: int, blocked_id: int) -> bool:
        """Unblock a user."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    DELETE FROM blocked_users
                    WHERE blocker_id = ? AND blocked_id = ?
                """
                ),
                (blocker_id, blocked_id),
            )

            return cursor.rowcount > 0

    @staticmethod
    def get_blocked_users(blocker_id: int) -> list[dict[str, Any]]:
        """Get list of users blocked by this user."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT
                        bu.*,
                        u.username, u.display_name, u.profile_photo_url
                    FROM blocked_users bu
                    JOIN users u ON u.id = bu.blocked_id
                    WHERE bu.blocker_id = ?
                    ORDER BY bu.blocked_at DESC
                """
                ),
                (blocker_id,),
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def is_blocked(user_id: int, other_user_id: int) -> bool:
        """Check if one user has blocked the other (either direction)."""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                convert_query(
                    """
                    SELECT 1 FROM blocked_users
                    WHERE (blocker_id = ? AND blocked_id = ?)
                       OR (blocker_id = ? AND blocked_id = ?)
                """
                ),
                (user_id, other_user_id, other_user_id, user_id),
            )

            return cursor.fetchone() is not None

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        """Convert database row to dictionary."""
        if not row:
            return {}
        return dict(row)
