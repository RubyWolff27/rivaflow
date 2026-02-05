#!/usr/bin/env python3
"""Background job to regenerate friend suggestions for all active users.

This script should be run periodically (e.g., daily via cron) to keep friend suggestions fresh.

Usage:
    python scripts/regenerate_friend_suggestions.py [--limit LIMIT] [--min-sessions MIN]

Options:
    --limit LIMIT           Limit the number of users to process (default: all)
    --min-sessions MIN      Minimum sessions required to generate suggestions (default: 3)
    --dry-run               Print what would be done without making changes
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path so we can import rivaflow
sys.path.insert(0, str(Path(__file__).parent.parent))

from rivaflow.core.services.friend_suggestions_service import FriendSuggestionsService
from rivaflow.db.database import close_connection_pool, get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_active_users(min_sessions: int = 3, limit: int = None):
    """
    Get list of active users who should receive friend suggestions.

    Args:
        min_sessions: Minimum number of sessions to be considered active
        limit: Maximum number of users to return

    Returns:
        List of user dicts with id and session count
    """
    query = """
        SELECT u.id, u.email, u.first_name, u.last_name, COUNT(s.id) as session_count
        FROM users u
        LEFT JOIN sessions s ON u.id = s.user_id
        WHERE u.is_active = 1
        GROUP BY u.id
        HAVING session_count >= ?
        ORDER BY session_count DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (min_sessions,))

        users = []
        for row in cursor.fetchall():
            if hasattr(row, "keys"):
                users.append(dict(row))
            else:
                users.append(
                    {
                        "id": row[0],
                        "email": row[1],
                        "first_name": row[2],
                        "last_name": row[3],
                        "session_count": row[4],
                    }
                )

        return users


def regenerate_suggestions_for_user(user_id: int, dry_run: bool = False) -> dict:
    """
    Regenerate friend suggestions for a single user.

    Args:
        user_id: User ID to generate suggestions for
        dry_run: If True, don't actually save the suggestions

    Returns:
        Dict with count of suggestions generated
    """
    service = FriendSuggestionsService()

    if dry_run:
        logger.info(f"[DRY RUN] Would regenerate suggestions for user {user_id}")
        return {"user_id": user_id, "suggestions_created": 0, "dry_run": True}

    # Clear old suggestions first
    service.regenerate_suggestions(user_id)

    # Generate new suggestions (this happens automatically in regenerate_suggestions)
    suggestions = service.get_suggestions(user_id, limit=10)

    return {
        "user_id": user_id,
        "suggestions_created": len(suggestions.get("suggestions", [])),
        "dry_run": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Regenerate friend suggestions for active users")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of users to process (default: all)",
    )
    parser.add_argument(
        "--min-sessions",
        type=int,
        default=3,
        help="Minimum sessions required to generate suggestions (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )

    args = parser.parse_args()

    try:
        logger.info("Starting friend suggestions regeneration job")
        logger.info(
            f"Parameters: min_sessions={args.min_sessions}, limit={args.limit}, dry_run={args.dry_run}"
        )

        # Get active users
        users = get_active_users(min_sessions=args.min_sessions, limit=args.limit)
        logger.info(f"Found {len(users)} active users to process")

        if not users:
            logger.info("No users found matching criteria. Exiting.")
            return 0

        # Process each user
        total_suggestions = 0
        successful = 0
        failed = 0

        for user in users:
            try:
                result = regenerate_suggestions_for_user(user["id"], dry_run=args.dry_run)
                total_suggestions += result["suggestions_created"]
                successful += 1

                logger.info(
                    f"✓ User {user['id']} ({user['first_name']} {user['last_name']}): "
                    f"{result['suggestions_created']} suggestions generated"
                )
            except Exception as e:
                failed += 1
                logger.error(f"✗ Failed to process user {user['id']}: {str(e)}")

        # Summary
        logger.info("=" * 60)
        logger.info("Friend Suggestions Regeneration Summary")
        logger.info("=" * 60)
        logger.info(f"Total users processed:      {len(users)}")
        logger.info(f"Successful:                 {successful}")
        logger.info(f"Failed:                     {failed}")
        logger.info(f"Total suggestions created:  {total_suggestions}")
        logger.info(f"Avg per user:               {total_suggestions / max(successful, 1):.1f}")

        if args.dry_run:
            logger.info("\n[DRY RUN] No changes were made to the database")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1
    finally:
        close_connection_pool()


if __name__ == "__main__":
    sys.exit(main())
