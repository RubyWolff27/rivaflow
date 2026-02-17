"""Integration tests for dashboard routes."""

from datetime import date, timedelta

import pytest

from rivaflow.db.database import convert_query, get_connection


@pytest.fixture(autouse=True)
def _ensure_profiles(test_user):
    """Create a profile row for the test user.

    Dashboard -> GoalsService -> ProfileRepository.get(user_id)
    returns None when no profile exists, causing AttributeError.
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


class TestDashboardSummary:
    """Tests for GET /api/v1/dashboard/summary."""

    def test_summary_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401

    def test_summary_returns_200(self, authenticated_client, test_user):
        """Authenticated request returns 200 with dashboard data."""
        resp = authenticated_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "performance" in data
        assert "streaks" in data
        assert "recent_sessions" in data
        assert "period" in data

    def test_summary_with_date_range(self, authenticated_client, test_user):
        """Accepts custom start_date and end_date params."""
        today = date.today()
        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
        resp = authenticated_client.get(
            f"/api/v1/dashboard/summary?start_date={start}&end_date={end}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"]["start_date"] == start
        assert data["period"]["end_date"] == end

    def test_summary_with_timezone(self, authenticated_client, test_user):
        """Accepts optional tz query parameter."""
        resp = authenticated_client.get("/api/v1/dashboard/summary?tz=Australia/Sydney")
        assert resp.status_code == 200

    def test_summary_with_sessions(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Dashboard includes recent sessions data."""
        session_factory(session_date=date.today(), duration_mins=60)
        resp = authenticated_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recent_sessions"]) >= 1


class TestQuickStats:
    """Tests for GET /api/v1/dashboard/quick-stats."""

    def test_quick_stats_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/dashboard/quick-stats")
        assert resp.status_code == 401

    def test_quick_stats_returns_200(self, authenticated_client, test_user):
        """Returns quick stats with expected fields."""
        resp = authenticated_client.get("/api/v1/dashboard/quick-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data
        assert "total_hours" in data
        assert "current_streak" in data
        assert "next_milestone" in data

    def test_quick_stats_empty_user(self, authenticated_client, test_user):
        """New user gets zero totals."""
        resp = authenticated_client.get("/api/v1/dashboard/quick-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["total_hours"] == 0
        assert data["current_streak"] == 0


class TestWeekSummary:
    """Tests for GET /api/v1/dashboard/week-summary."""

    def test_week_summary_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/dashboard/week-summary")
        assert resp.status_code == 401

    def test_week_summary_current_week(self, authenticated_client, test_user):
        """Returns summary for the current week."""
        resp = authenticated_client.get("/api/v1/dashboard/week-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "week_start" in data
        assert "week_end" in data
        assert data["is_current_week"] is True
        assert "stats" in data
        assert data["stats"]["total_sessions"] == 0

    def test_week_summary_with_offset(self, authenticated_client, test_user):
        """Returns summary for a previous week."""
        resp = authenticated_client.get("/api/v1/dashboard/week-summary?week_offset=-1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_current_week"] is False

    def test_week_summary_invalid_offset(self, authenticated_client, test_user):
        """Rejects offset outside -52..0 range."""
        resp = authenticated_client.get("/api/v1/dashboard/week-summary?week_offset=1")
        assert resp.status_code == 422

    def test_week_summary_with_sessions(
        self,
        authenticated_client,
        test_user,
        session_factory,
    ):
        """Week summary includes session counts."""
        session_factory(
            session_date=date.today(),
            duration_mins=90,
            rolls=6,
        )
        resp = authenticated_client.get("/api/v1/dashboard/week-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_sessions"] >= 1
