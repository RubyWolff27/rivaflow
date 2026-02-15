"""Integration tests for goals routes and GoalsService."""

from datetime import date, timedelta

import pytest

from rivaflow.db.database import convert_query, get_connection


@pytest.fixture(autouse=True)
def _ensure_profiles(test_user):
    """Create a profile row for the test user.

    GoalsService.get_current_week_progress() calls
    ProfileRepository.get(user_id) which returns None when no
    profile row exists, causing AttributeError.  The conftest
    test_user fixture only creates a users row, so we insert a
    minimal profile here.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT id FROM profile WHERE user_id = ?"),
            (test_user["id"],),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                convert_query(
                    "INSERT INTO profile "
                    "(user_id, first_name, last_name) "
                    "VALUES (?, ?, ?)"
                ),
                (
                    test_user["id"],
                    test_user.get("first_name", "Test"),
                    test_user.get("last_name", "User"),
                ),
            )


def _ensure_profile_for(user: dict):
    """Create a profile row for an arbitrary user dict."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT id FROM profile WHERE user_id = ?"),
            (user["id"],),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                convert_query(
                    "INSERT INTO profile "
                    "(user_id, first_name, last_name) "
                    "VALUES (?, ?, ?)"
                ),
                (
                    user["id"],
                    user.get("first_name", "Test"),
                    user.get("last_name", "User"),
                ),
            )


class TestGetCurrentWeekProgress:
    """Tests for GET /api/v1/goals/current-week."""

    def test_current_week_progress_empty(self, authenticated_client, test_user):
        """Returns progress with zero actuals when no sessions."""
        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        data = resp.json()

        assert "week_start" in data
        assert "week_end" in data
        assert "targets" in data
        assert "actual" in data
        assert "progress" in data
        assert "completed" in data
        assert "days_remaining" in data

        # No sessions logged — actuals should be zero
        assert data["actual"]["sessions"] == 0
        assert data["actual"]["hours"] == 0
        assert data["actual"]["rolls"] == 0
        assert data["completed"] is False

    def test_current_week_progress_with_sessions(
        self, authenticated_client, test_user, session_factory
    ):
        """Shows accurate progress when sessions exist."""
        today = date.today()
        session_factory(
            session_date=today,
            class_type="gi",
            duration_mins=90,
            rolls=6,
        )
        session_factory(
            session_date=today,
            class_type="no-gi",
            duration_mins=60,
            rolls=4,
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        data = resp.json()

        assert data["actual"]["sessions"] == 2
        assert data["actual"]["hours"] == 2.5  # (90+60)/60
        assert data["actual"]["rolls"] == 10

    def test_current_week_with_timezone(self, authenticated_client, test_user):
        """Accepts optional tz query parameter."""
        resp = authenticated_client.get(
            "/api/v1/goals/current-week?tz=Australia/Sydney"
        )
        assert resp.status_code == 200
        assert "week_start" in resp.json()

    def test_current_week_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/goals/current-week")
        assert resp.status_code == 401

    def test_current_week_completed(
        self, authenticated_client, test_user, session_factory
    ):
        """Marks completed=True when all targets are met."""
        today = date.today()
        # Default targets: sessions=3, hours=4.5, rolls=15
        for _ in range(3):
            session_factory(
                session_date=today,
                class_type="gi",
                duration_mins=90,
                rolls=5,
            )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        data = resp.json()

        assert data["actual"]["sessions"] >= 3
        assert data["actual"]["hours"] >= 4.5
        assert data["actual"]["rolls"] >= 15
        assert data["completed"] is True


class TestGetGoalsSummary:
    """Tests for GET /api/v1/goals/summary."""

    def test_summary_returns_all_sections(self, authenticated_client, test_user):
        """Summary has current_week, streaks, and trend."""
        resp = authenticated_client.get("/api/v1/goals/summary")
        assert resp.status_code == 200
        data = resp.json()

        assert "current_week" in data
        assert "training_streaks" in data
        assert "goal_streaks" in data
        assert "recent_trend" in data

    def test_summary_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/goals/summary")
        assert resp.status_code == 401


class TestGetTrainingStreaks:
    """Tests for GET /api/v1/goals/streaks/training."""

    def test_training_streaks_empty(self, authenticated_client, test_user):
        """Returns zero streaks when no sessions exist."""
        resp = authenticated_client.get("/api/v1/goals/streaks/training")
        assert resp.status_code == 200
        data = resp.json()

        assert "current_streak" in data
        assert "longest_streak" in data
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0

    def test_training_streaks_with_sessions(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Returns streak counts with consecutive sessions."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        session_factory(session_date=today)
        session_factory(session_date=yesterday)

        resp = authenticated_client.get("/api/v1/goals/streaks/training")
        assert resp.status_code == 200
        data = resp.json()

        assert data["current_streak"] >= 2
        assert data["longest_streak"] >= 2

    def test_training_streaks_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/goals/streaks/training")
        assert resp.status_code == 401


class TestGetGoalCompletionStreaks:
    """Tests for GET /api/v1/goals/streaks/goals."""

    def test_goal_streaks_empty(self, authenticated_client, test_user):
        """Returns zero streaks with no goal progress."""
        resp = authenticated_client.get("/api/v1/goals/streaks/goals")
        assert resp.status_code == 200
        data = resp.json()

        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0

    def test_goal_streaks_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/goals/streaks/goals")
        assert resp.status_code == 401


class TestGetRecentTrend:
    """Tests for GET /api/v1/goals/trend."""

    def test_trend_empty(self, authenticated_client, test_user):
        """Returns empty list with no goal history."""
        resp = authenticated_client.get("/api/v1/goals/trend")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_trend_custom_weeks(self, authenticated_client, test_user):
        """Accepts weeks query parameter."""
        resp = authenticated_client.get("/api/v1/goals/trend?weeks=4")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trend_invalid_weeks(self, authenticated_client, test_user):
        """Rejects weeks outside 1-52 range."""
        resp = authenticated_client.get("/api/v1/goals/trend?weeks=0")
        assert resp.status_code in (400, 422)

        resp = authenticated_client.get("/api/v1/goals/trend?weeks=53")
        assert resp.status_code in (400, 422)

    def test_trend_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/goals/trend")
        assert resp.status_code == 401


class TestUpdateGoalTargets:
    """Tests for PUT /api/v1/goals/targets."""

    def test_update_sessions_target(self, authenticated_client, test_user):
        """Can update weekly_sessions_target."""
        resp = authenticated_client.put(
            "/api/v1/goals/targets",
            json={"weekly_sessions_target": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["weekly_sessions_target"] == 5

    def test_update_hours_target(self, authenticated_client, test_user):
        """Can update weekly_hours_target."""
        resp = authenticated_client.put(
            "/api/v1/goals/targets",
            json={"weekly_hours_target": 6.0},
        )
        assert resp.status_code == 200
        assert resp.json()["weekly_hours_target"] == 6.0

    def test_update_rolls_target(self, authenticated_client, test_user):
        """Can update weekly_rolls_target."""
        resp = authenticated_client.put(
            "/api/v1/goals/targets",
            json={"weekly_rolls_target": 20},
        )
        assert resp.status_code == 200
        assert resp.json()["weekly_rolls_target"] == 20

    def test_update_multiple_targets(self, authenticated_client, test_user):
        """Can update all three targets at once."""
        resp = authenticated_client.put(
            "/api/v1/goals/targets",
            json={
                "weekly_sessions_target": 4,
                "weekly_hours_target": 5.0,
                "weekly_rolls_target": 18,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["weekly_sessions_target"] == 4
        assert data["weekly_hours_target"] == 5.0
        assert data["weekly_rolls_target"] == 18

    def test_update_no_changes(self, authenticated_client, test_user):
        """Empty body returns current profile unchanged."""
        resp = authenticated_client.put(
            "/api/v1/goals/targets",
            json={},
        )
        assert resp.status_code == 200

    def test_update_targets_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.put(
            "/api/v1/goals/targets",
            json={"weekly_sessions_target": 5},
        )
        assert resp.status_code == 401

    def test_update_targets_persists(self, authenticated_client, test_user):
        """Updated targets reflected in current-week progress."""
        authenticated_client.put(
            "/api/v1/goals/targets",
            json={"weekly_sessions_target": 7},
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        assert resp.json()["targets"]["sessions"] == 7


class TestGoalsServiceUnit:
    """Unit tests for GoalsService via the API."""

    def test_weekly_progress_structure(self, authenticated_client, test_user):
        """Progress response has correct structure."""
        resp = authenticated_client.get("/api/v1/goals/current-week")
        data = resp.json()

        targets = data["targets"]
        assert "sessions" in targets
        assert "hours" in targets
        assert "rolls" in targets

        actual = data["actual"]
        assert "sessions" in actual
        assert "hours" in actual
        assert "rolls" in actual

        progress = data["progress"]
        assert "sessions_pct" in progress
        assert "hours_pct" in progress
        assert "rolls_pct" in progress
        assert "overall_pct" in progress

    def test_progress_percentages_correct(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Percentages are calculated correctly."""
        today = date.today()
        # Default target: 3 sessions -- log 1 session
        session_factory(
            session_date=today,
            class_type="gi",
            duration_mins=60,
            rolls=5,
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        data = resp.json()

        pct = data["progress"]["sessions_pct"]
        # 1 out of 3 default target = 33.3%
        assert 33.0 <= pct <= 34.0

    def test_days_remaining_non_negative(self, authenticated_client, test_user):
        """Days remaining is never negative."""
        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.json()["days_remaining"] >= 0

    def test_activity_type_breakdown(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Actual includes BJJ, S&C, and mobility counts."""
        today = date.today()
        session_factory(
            session_date=today,
            class_type="gi",
            duration_mins=60,
            rolls=3,
        )
        session_factory(
            session_date=today,
            class_type="s&c",
            duration_mins=45,
            rolls=0,
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        actual = resp.json()["actual"]
        assert actual["bjj_sessions"] == 1
        assert actual["sc_sessions"] == 1
        assert actual["sessions"] == 2


class TestGoalsIsolation:
    """Test that users cannot see other users' data."""

    def test_user_isolation(
        self,
        client,
        temp_db,
        test_user,
        test_user2,
    ):
        """Each user only sees their own weekly progress."""
        from rivaflow.core.auth import create_access_token
        from rivaflow.db.repositories import SessionRepository

        # Ensure both users have profiles
        _ensure_profile_for(test_user)
        _ensure_profile_for(test_user2)

        # Create session for user 1
        SessionRepository.create(
            user_id=test_user["id"],
            session_date=date.today(),
            class_type="gi",
            gym_name="Gym A",
            duration_mins=60,
            intensity=4,
            rolls=5,
            submissions_for=0,
            submissions_against=0,
        )

        # Create session for user 2
        SessionRepository.create(
            user_id=test_user2["id"],
            session_date=date.today(),
            class_type="no-gi",
            gym_name="Gym B",
            duration_mins=90,
            intensity=3,
            rolls=8,
            submissions_for=0,
            submissions_against=0,
        )

        # Get progress for user 1
        token1 = create_access_token(
            data={"sub": str(test_user["id"])},
            expires_delta=timedelta(hours=1),
        )
        resp1 = client.get(
            "/api/v1/goals/current-week",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()

        # Get progress for user 2
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        resp2 = client.get(
            "/api/v1/goals/current-week",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()

        # Each user sees only their own session
        assert data1["actual"]["sessions"] == 1
        assert data2["actual"]["sessions"] == 1
        assert data1["actual"]["rolls"] == 5
        assert data2["actual"]["rolls"] == 8


class TestGoalsEdgeCases:
    """Edge cases for goals functionality."""

    def test_session_outside_current_week(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Sessions from prior weeks excluded from current."""
        two_weeks_ago = date.today() - timedelta(days=14)
        session_factory(
            session_date=two_weeks_ago,
            class_type="gi",
            duration_mins=60,
            rolls=5,
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        assert resp.json()["actual"]["sessions"] == 0

    def test_zero_target_no_division_error(self, authenticated_client, test_user):
        """Zero targets produce 0% progress, not error."""
        authenticated_client.put(
            "/api/v1/goals/targets",
            json={
                "weekly_sessions_target": 0,
                "weekly_hours_target": 0,
                "weekly_rolls_target": 0,
            },
        )

        resp = authenticated_client.get("/api/v1/goals/current-week")
        assert resp.status_code == 200
        data = resp.json()

        assert data["progress"]["sessions_pct"] == 0
        assert data["progress"]["hours_pct"] == 0
        assert data["progress"]["rolls_pct"] == 0

    def test_trend_after_progress_created(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Trend includes weeks with progress records."""
        today = date.today()
        session_factory(
            session_date=today,
            class_type="gi",
            duration_mins=60,
            rolls=5,
        )

        # Calling current-week creates a goal_progress record
        authenticated_client.get("/api/v1/goals/current-week")

        # Trend should now have at least one entry
        resp = authenticated_client.get("/api/v1/goals/trend")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert "week_start" in data[0]
        assert "completion_pct" in data[0]
