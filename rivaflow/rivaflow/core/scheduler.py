"""Background scheduler for periodic tasks.

Runs alongside the FastAPI app using APScheduler's AsyncIOScheduler.
All jobs are best-effort — failures are logged but do not crash the app.
"""

import logging
from datetime import datetime, timedelta

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
        cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query(
                    "SELECT DISTINCT user_id FROM sessions" " WHERE session_date >= ?"
                ),
                (cutoff,),
            )
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
                    from datetime import date

                    from rivaflow.db.repositories.checkin_repo import (
                        CheckinRepository,
                    )
                    from rivaflow.db.repositories.notification_repo import (
                        NotificationRepository,
                    )

                    # Check yesterday's plan for a personalized nudge
                    checkin_repo = CheckinRepository()
                    yesterday = date.today() - timedelta(days=1)
                    y_slots = checkin_repo.get_day_checkins(uid, yesterday)
                    intention = None
                    for slot in ("evening", "midday", "morning"):
                        s = y_slots.get(slot)
                        if s and s.get("tomorrow_intention"):
                            intention = s["tomorrow_intention"]
                            break

                    if intention:
                        msg = (
                            f'You planned "{intention}" today'
                            f" — don't forget to log it!"
                        )
                    else:
                        msg = "Your streak is at risk!" " Train today to keep it going."

                    if not NotificationRepository.check_duplicate(
                        uid, uid, "streak_at_risk", None, None
                    ):
                        NotificationRepository.create(
                            user_id=uid,
                            actor_id=uid,
                            notification_type="streak_at_risk",
                            message=msg,
                        )
            except Exception:
                logger.debug(
                    "Streak-at-risk check failed for user %d",
                    uid,
                    exc_info=True,
                )
    except Exception:
        logger.error("Streak-at-risk job failed", exc_info=True)


async def _drip_email_job() -> None:
    """Send onboarding drip emails (daily 10:00 UTC).

    Day 1 = day after registration, Day 3 = 3 days after, Day 5 = 5 days after.
    """
    try:
        from rivaflow.core.services.email_service import EmailService
        from rivaflow.db.database import convert_query, get_connection
        from rivaflow.db.repositories.email_drip_repo import (
            EmailDripRepository,
        )

        drips = [
            (1, "drip_day1", "send_drip_day1"),
            (3, "drip_day3", "send_drip_day3"),
            (5, "drip_day5", "send_drip_day5"),
        ]
        email_service = EmailService()
        total_sent = 0

        for days_ago, email_key, method_name in drips:
            target_date = (datetime.now() - timedelta(days=days_ago)).strftime(
                "%Y-%m-%d"
            )
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    convert_query(
                        "SELECT id, email, first_name FROM users"
                        " WHERE is_active = ?"
                        " AND SUBSTR(created_at, 1, 10) = ?"
                    ),
                    (1, target_date),
                )
                rows = cursor.fetchall()

            users = [
                {
                    "id": (r["id"] if hasattr(r, "keys") else r[0]),
                    "email": (r["email"] if hasattr(r, "keys") else r[1]),
                    "first_name": (r["first_name"] if hasattr(r, "keys") else r[2]),
                }
                for r in rows
            ]

            for user in users:
                try:
                    if EmailDripRepository.has_been_sent(user["id"], email_key):
                        continue
                    method = getattr(email_service, method_name)
                    method(
                        email=user["email"],
                        first_name=user.get("first_name"),
                    )
                    EmailDripRepository.mark_sent(user["id"], email_key)
                    total_sent += 1
                except Exception:
                    logger.debug(
                        "Drip %s failed for user %d",
                        email_key,
                        user["id"],
                        exc_info=True,
                    )

        if total_sent:
            logger.info("Drip emails: sent %d emails", total_sent)
    except Exception:
        logger.error("Drip email job failed", exc_info=True)


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

    # Daily 10:00 UTC — onboarding drip emails
    _scheduler.add_job(
        _drip_email_job,
        "cron",
        hour=10,
        minute=0,
        id="drip_emails",
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
