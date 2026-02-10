"""Background scheduler for periodic tasks.

Runs alongside the FastAPI app using APScheduler's AsyncIOScheduler.
All jobs are best-effort — failures are logged but do not crash the app.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


# ---------------------------------------------------------------------------
# Job definitions
# ---------------------------------------------------------------------------


async def _weekly_insights_job() -> None:
    """Generate weekly AI insights for active users (Sunday 18:00 UTC)."""
    try:
        from rivaflow.db.database import convert_query, get_connection

        # Find users with sessions in the last 14 days
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("""
                    SELECT DISTINCT user_id FROM sessions
                    WHERE session_date >= date('now', '-14 days')
                """))
            rows = cursor.fetchall()

        user_ids = [r["user_id"] if hasattr(r, "keys") else r[0] for r in rows]
        logger.info("Weekly insights: %d active users", len(user_ids))

        from rivaflow.core.services.grapple.ai_insight_service import (
            generate_weekly_insight,
        )

        for uid in user_ids:
            try:
                await generate_weekly_insight(uid)
            except Exception:
                logger.debug("Weekly insight failed for user %d", uid, exc_info=True)
    except Exception:
        logger.error("Weekly insights job failed", exc_info=True)


async def _streak_at_risk_job() -> None:
    """Notify users whose streaks are at risk (daily 20:00 UTC)."""
    try:
        from rivaflow.core.services.streak_service import StreakService
        from rivaflow.db.database import convert_query, get_connection

        # Find users with active streaks >= 3
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(convert_query("""
                    SELECT DISTINCT user_id FROM streaks
                    WHERE current_streak >= 3
                """))
            rows = cursor.fetchall()

        user_ids = [r["user_id"] if hasattr(r, "keys") else r[0] for r in rows]
        logger.info("Streak-at-risk check: %d users", len(user_ids))

        streak_svc = StreakService()
        for uid in user_ids:
            try:
                if streak_svc.is_streak_at_risk(uid):
                    from rivaflow.db.repositories.notification_repo import (
                        NotificationRepository,
                    )

                    if not NotificationRepository.check_duplicate(
                        uid, uid, "streak_at_risk", None, None
                    ):
                        NotificationRepository.create(
                            user_id=uid,
                            actor_id=uid,
                            notification_type="streak_at_risk",
                            message="Your streak is at risk! Train today to keep it going.",
                        )
            except Exception:
                logger.debug(
                    "Streak-at-risk check failed for user %d",
                    uid,
                    exc_info=True,
                )
    except Exception:
        logger.error("Streak-at-risk job failed", exc_info=True)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def start_scheduler() -> None:
    """Create and start the background scheduler."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler()

    # Sunday 18:00 UTC — weekly AI insights
    _scheduler.add_job(
        _weekly_insights_job,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=0,
        id="weekly_insights",
        replace_existing=True,
    )

    # Daily 20:00 UTC — streak-at-risk notifications
    _scheduler.add_job(
        _streak_at_risk_job,
        "cron",
        hour=20,
        minute=0,
        id="streak_at_risk",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Background scheduler started with %d jobs", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Shut down the scheduler."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")
