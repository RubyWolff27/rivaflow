"""One-shot backfill: score every session that has no session_score.

Idempotent — skips sessions that already have a score, so safe to run
on every deploy.  Exits 0 even if individual sessions fail.
"""

import logging

logger = logging.getLogger(__name__)


def backfill_all_users():
    from rivaflow.core.services.session_scoring_service import (
        SessionScoringService,
    )
    from rivaflow.db.database import convert_query, get_connection

    # Get all user IDs that have at least one unscored session
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "SELECT DISTINCT user_id FROM sessions" " WHERE session_score IS NULL"
            )
        )
        rows = cursor.fetchall()

    user_ids = []
    for row in rows:
        uid = row["user_id"] if hasattr(row, "keys") else row[0]
        user_ids.append(uid)

    if not user_ids:
        logger.info("No unscored sessions found — nothing to backfill.")
        return

    logger.info("Backfilling scores for %d user(s)...", len(user_ids))
    scoring = SessionScoringService()
    total_scored = 0

    for uid in user_ids:
        try:
            result = scoring.backfill_user_scores(uid)
            scored = result.get("scored", 0)
            total_scored += scored
            logger.info(
                "  user %s: scored=%d, skipped=%d",
                uid,
                scored,
                result.get("skipped", 0),
            )
        except Exception:
            logger.warning("  user %s: backfill failed", uid, exc_info=True)

    logger.info("Backfill complete: %d sessions scored.", total_scored)
