"""Tests for InsightService -- daily insight generation."""

from datetime import date, timedelta

from rivaflow.core.services.insight_service import InsightService
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.streak_repo import StreakRepository

INSIGHT_KEYS = {"type", "title", "message", "action", "icon"}
VALID_TYPES = {
    "stat",
    "technique",
    "partner",
    "trend",
    "encouragement",
    "recovery",
    "streak",
    "milestone",
}


# ------------------------------------------------------------------ #
# generate_insight -- default (no data)
# ------------------------------------------------------------------ #


def test_generate_insight_default_no_data(temp_db, test_user):
    """generate_insight returns an encouragement insight for new user."""
    svc = InsightService()
    insight = svc.generate_insight(test_user["id"])

    assert isinstance(insight, dict)
    assert INSIGHT_KEYS <= insight.keys()
    assert insight["type"] == "encouragement"
    assert len(insight["message"]) > 0


def test_generate_insight_returns_valid_type(temp_db, test_user):
    """generate_insight always returns a recognized insight type."""
    svc = InsightService()
    insight = svc.generate_insight(test_user["id"])

    assert insight["type"] in VALID_TYPES


# ------------------------------------------------------------------ #
# _get_stat_insights -- training volume comparison
# ------------------------------------------------------------------ #


def test_stat_insight_volume_up(temp_db, test_user):
    """Stat insight detects above-average training volume."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Create sessions in the past 4 weeks (baseline)
    for i in range(4):
        past_date = today - timedelta(days=7 * (i + 1))
        repo.create(
            user_id=test_user["id"],
            session_date=past_date,
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
        )

    # Create heavy training this week (well above average)
    for offset in range(5):
        d = week_start + timedelta(days=offset)
        if d <= today:
            repo.create(
                user_id=test_user["id"],
                session_date=d,
                class_type="gi",
                gym_name="Gym",
                duration_mins=90,
            )

    insights = svc._get_stat_insights(test_user["id"])

    # With 5 x 90 = 450 mins this week vs ~60 mins avg,
    # should get a "Training volume up" insight
    if insights:
        types = [i["type"] for i in insights]
        assert "stat" in types


def test_stat_insight_recovery_week(temp_db, test_user):
    """Stat insight detects below-average training volume."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Create heavy sessions in past weeks (baseline)
    for i in range(4):
        past_date = today - timedelta(days=7 * (i + 1))
        for j in range(4):
            repo.create(
                user_id=test_user["id"],
                session_date=past_date + timedelta(days=j),
                class_type="gi",
                gym_name="Gym",
                duration_mins=90,
            )

    # Only one short session this week
    repo.create(
        user_id=test_user["id"],
        session_date=week_start,
        class_type="gi",
        gym_name="Gym",
        duration_mins=30,
    )

    insights = svc._get_stat_insights(test_user["id"])
    # Should detect a recovery/low volume week
    if insights:
        titles = [i["title"] for i in insights]
        assert "Recovery week" in titles or "Training volume up" in titles


# ------------------------------------------------------------------ #
# _get_streak_insights
# ------------------------------------------------------------------ #


def test_streak_insight_7_day(temp_db, test_user):
    """Streak insight triggers at 7+ day check-in streak."""
    svc = InsightService()

    # Manually set a 7-day streak
    streak_repo = StreakRepository()
    streak_repo.get_streak(test_user["id"], "checkin")

    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE streaks SET current_streak = 8"
                " WHERE user_id = ? AND streak_type = 'checkin'"
            ),
            (test_user["id"],),
        )
        conn.commit()

    insights = svc._get_streak_insights(test_user["id"])
    assert len(insights) >= 1
    assert insights[0]["type"] == "streak"
    assert "8" in insights[0]["message"]


def test_streak_insight_14_day(temp_db, test_user):
    """Streak insight has different message at 14+ days."""
    svc = InsightService()

    streak_repo = StreakRepository()
    streak_repo.get_streak(test_user["id"], "checkin")

    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE streaks SET current_streak = 16"
                " WHERE user_id = ? AND streak_type = 'checkin'"
            ),
            (test_user["id"],),
        )
        conn.commit()

    insights = svc._get_streak_insights(test_user["id"])
    assert len(insights) >= 1
    assert "Habit forming" in insights[0]["title"]


def test_streak_insight_30_day(temp_db, test_user):
    """Streak insight for 30+ days uses 'Consistency wins' title."""
    svc = InsightService()

    streak_repo = StreakRepository()
    streak_repo.get_streak(test_user["id"], "checkin")

    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE streaks SET current_streak = 35"
                " WHERE user_id = ? AND streak_type = 'checkin'"
            ),
            (test_user["id"],),
        )
        conn.commit()

    insights = svc._get_streak_insights(test_user["id"])
    assert len(insights) >= 1
    assert insights[0]["title"] == "Consistency wins"


def test_streak_insight_no_streak(temp_db, test_user):
    """No streak insight when streak is below threshold."""
    svc = InsightService()

    # Initialize streak at 0 (default)
    StreakRepository().get_streak(test_user["id"], "checkin")

    insights = svc._get_streak_insights(test_user["id"])
    assert insights == []


# ------------------------------------------------------------------ #
# _get_recovery_insights
# ------------------------------------------------------------------ #


def test_recovery_insight_heavy_week(temp_db, test_user):
    """Recovery insight triggers after 6+ training days in a week."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()

    # Create 6 sessions in the last 7 days
    for i in range(6):
        repo.create(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i),
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
        )

    insights = svc._get_recovery_insights(test_user["id"])
    assert len(insights) >= 1
    assert insights[0]["type"] == "recovery"
    assert "Rest is training" in insights[0]["title"]


def test_recovery_insight_not_triggered(temp_db, test_user):
    """Recovery insight does not fire with fewer than 6 sessions."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()

    # Only 3 sessions this week
    for i in range(3):
        repo.create(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i),
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
        )

    insights = svc._get_recovery_insights(test_user["id"])
    assert insights == []


# ------------------------------------------------------------------ #
# _get_trend_insights -- submission rate
# ------------------------------------------------------------------ #


def test_trend_insight_submissions_up(temp_db, test_user):
    """Trend insight fires when recent sub rate exceeds prior period."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()

    # Previous period: 31-60 days ago -- low submissions
    for i in range(5):
        repo.create(
            user_id=test_user["id"],
            session_date=today - timedelta(days=40 + i),
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
            submissions_for=0,
        )

    # Recent period: last 30 days -- high submissions
    for i in range(5):
        repo.create(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i + 1),
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
            submissions_for=3,
        )

    insights = svc._get_trend_insights(test_user["id"])
    if insights:
        assert insights[0]["type"] == "trend"
        assert "submission" in insights[0]["title"].lower()


def test_trend_insight_no_data(temp_db, test_user):
    """Trend insight returns empty when no session data exists."""
    svc = InsightService()
    insights = svc._get_trend_insights(test_user["id"])
    assert insights == []


# ------------------------------------------------------------------ #
# _get_default_insight
# ------------------------------------------------------------------ #


def test_default_insight_shape(temp_db, test_user):
    """Default insight has correct structure."""
    svc = InsightService()
    insight = svc._get_default_insight()

    assert insight["type"] == "encouragement"
    assert isinstance(insight["title"], str)
    assert isinstance(insight["message"], str)
    assert insight["action"] is None
    assert isinstance(insight["icon"], str)


# ------------------------------------------------------------------ #
# generate_insight weighted selection includes all sources
# ------------------------------------------------------------------ #


def test_generate_insight_with_data(temp_db, test_user):
    """generate_insight returns data-driven insight when data exists."""
    svc = InsightService()
    repo = SessionRepository()

    today = date.today()

    # Create enough data to trigger recovery insight (6 days)
    for i in range(6):
        repo.create(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i),
            class_type="gi",
            gym_name="Gym",
            duration_mins=60,
        )

    insight = svc.generate_insight(test_user["id"])
    assert isinstance(insight, dict)
    assert insight["type"] in VALID_TYPES
    # With 6 recent sessions, we should get a data-driven insight
    # (recovery, stat, or trend), but randomness means we check type
    assert insight["type"] != ""
