"""IDOR (Insecure Direct Object Reference) security tests.

Verifies that User1 cannot access or modify User2's resources.
Each test creates a resource as User2, then attempts to access
it as User1 (via authenticated_client). The expected result is
403 or 404 -- never 200 with User2's data.
"""

from datetime import date, timedelta

import pytest

from rivaflow.core.auth import create_access_token
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories import (
    ActivityPhotoRepository,
    GradingRepository,
    ReadinessRepository,
    SessionRepository,
)
from rivaflow.db.repositories.game_plan_repo import GamePlanRepository
from rivaflow.db.repositories.glossary_repo import GlossaryRepository


@pytest.fixture()
def user2_headers(test_user2):
    """Auth headers for test_user2."""
    token = create_access_token(
        data={"sub": str(test_user2["id"])},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user2_client(client, user2_headers):
    """TestClient authenticated as test_user2."""
    from fastapi.testclient import TestClient

    from rivaflow.api.main import app

    c = TestClient(app)
    c.headers.update(user2_headers)
    return c


def _ensure_profile(user):
    """Create a minimal profile row for a user if it does not exist."""
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


# ============================================================================
# Session IDOR Tests
# ============================================================================


class TestSessionIDOR:
    """User1 must not be able to access User2's sessions."""

    def _create_user2_session(self, user2_id):
        """Create a session owned by user2 directly via repo."""
        repo = SessionRepository()
        return repo.create(
            user_id=user2_id,
            session_date=date.today(),
            class_type="gi",
            gym_name="User2 Gym",
            location="User2 City",
            duration_mins=60,
            intensity=4,
            rolls=3,
            submissions_for=0,
            submissions_against=0,
        )

    def test_get_session_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot GET User2's session."""
        session_id = self._create_user2_session(test_user2["id"])
        response = authenticated_client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_update_session_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot PUT User2's session."""
        session_id = self._create_user2_session(test_user2["id"])
        response = authenticated_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"notes": "HACKED by User1"},
        )
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_delete_session_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot DELETE User2's session."""
        session_id = self._create_user2_session(test_user2["id"])
        response = authenticated_client.delete(f"/api/v1/sessions/{session_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_get_session_score_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot GET score of User2's session."""
        session_id = self._create_user2_session(test_user2["id"])
        response = authenticated_client.get(f"/api/v1/sessions/{session_id}/score")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_list_sessions_isolation(self, authenticated_client, test_user, test_user2):
        """User1's session list must not contain User2's sessions."""
        self._create_user2_session(test_user2["id"])
        response = authenticated_client.get("/api/v1/sessions/")
        assert response.status_code == 200
        data = response.json()
        for s in data:
            assert s.get("user_id", test_user["id"]) == test_user["id"]


# ============================================================================
# Readiness IDOR Tests
# ============================================================================


class TestReadinessIDOR:
    """User1 must not be able to read User2's readiness entries."""

    def _create_user2_readiness(self, user2_id, check_date=None):
        """Create a readiness entry for user2."""
        repo = ReadinessRepository()
        repo.upsert(
            user_id=user2_id,
            check_date=check_date or date.today(),
            sleep=5,
            stress=2,
            soreness=1,
            energy=5,
        )
        return check_date or date.today()

    def test_get_readiness_by_date_idor(
        self, authenticated_client, test_user, test_user2
    ):
        """User1 cannot GET User2's readiness by date."""
        check_date = self._create_user2_readiness(test_user2["id"])
        response = authenticated_client.get(
            f"/api/v1/readiness/{check_date.isoformat()}"
        )
        # Should return 200 with null/own data, or 403/404
        if response.status_code == 200:
            data = response.json()
            if data is not None:
                # If it returns data, it must be user1's, not user2's
                assert (
                    data.get("user_id", test_user["id"]) == test_user["id"]
                ), "Returned readiness belongs to wrong user"
        else:
            assert response.status_code in (403, 404)

    def test_readiness_range_isolation(
        self, authenticated_client, test_user, test_user2
    ):
        """User1's readiness range must not contain User2's entries."""
        self._create_user2_readiness(test_user2["id"])
        start = (date.today() - timedelta(days=7)).isoformat()
        end = date.today().isoformat()
        response = authenticated_client.get(f"/api/v1/readiness/range/{start}/{end}")
        assert response.status_code == 200
        data = response.json()
        if isinstance(data, list):
            for entry in data:
                assert entry.get("user_id", test_user["id"]) == test_user["id"]


# ============================================================================
# Goals IDOR Tests
# ============================================================================


class TestGoalsIDOR:
    """User1 must not see User2's goal progress."""

    def test_goals_summary_isolation(self, authenticated_client, test_user, test_user2):
        """User1's goals summary only reflects their own data."""
        _ensure_profile(test_user)
        _ensure_profile(test_user2)

        # Create sessions for user2 via their client
        repo = SessionRepository()
        repo.create(
            user_id=test_user2["id"],
            session_date=date.today(),
            class_type="gi",
            gym_name="User2 Gym",
            location="City",
            duration_mins=90,
            intensity=5,
            rolls=10,
            submissions_for=0,
            submissions_against=0,
        )

        response = authenticated_client.get("/api/v1/goals/current-week")
        assert response.status_code == 200
        data = response.json()
        # User1 should not see user2's sessions in their actual counts
        actual = data.get("actual", {})
        # User1 has 0 sessions, so sessions actual should be 0
        assert actual.get("sessions", 0) == 0

    def test_goals_targets_isolation(
        self, authenticated_client, test_user, test_user2, client
    ):
        """User2's target changes don't affect User1's goals."""
        _ensure_profile(test_user)
        _ensure_profile(test_user2)

        # User2 updates their targets
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        client.put(
            "/api/v1/goals/targets",
            json={"weekly_sessions_target": 10},
            headers={"Authorization": f"Bearer {token2}"},
        )

        # User1's targets should remain at defaults
        response = authenticated_client.get("/api/v1/goals/current-week")
        assert response.status_code == 200
        data = response.json()
        targets = data.get("targets", {})
        # Default target is typically 3, definitely not 10
        assert targets.get("sessions", 3) != 10


# ============================================================================
# Checkins IDOR Tests
# ============================================================================


class TestCheckinsIDOR:
    """User1 must not see User2's check-ins."""

    def test_today_checkin_isolation(
        self,
        authenticated_client,
        test_user,
        test_user2,
        client,
    ):
        """User1 cannot see User2's check-in data."""
        _ensure_profile(test_user2)
        # User2 creates a midday check-in
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        client.post(
            "/api/v1/checkins/midday",
            json={"energy_level": 5, "midday_note": "User2 secret"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        # User1 checks their own today status
        response = authenticated_client.get("/api/v1/checkins/today")
        assert response.status_code == 200
        data = response.json()
        # User1 should not see user2's midday note
        midday = data.get("midday")
        if midday is not None:
            assert midday.get("midday_note") != "User2 secret"

    def test_week_checkins_isolation(
        self,
        authenticated_client,
        test_user,
        test_user2,
        client,
    ):
        """User1's week check-ins don't contain User2's data."""
        _ensure_profile(test_user2)
        token2 = create_access_token(
            data={"sub": str(test_user2["id"])},
            expires_delta=timedelta(hours=1),
        )
        client.post(
            "/api/v1/checkins/midday",
            json={"energy_level": 4},
            headers={"Authorization": f"Bearer {token2}"},
        )

        response = authenticated_client.get("/api/v1/checkins/week")
        assert response.status_code == 200
        data = response.json()
        # User1 should have zero filled slots
        for day in data.get("checkins", []):
            assert day.get("slots_filled", 0) == 0


# ============================================================================
# Game Plan IDOR Tests
# ============================================================================


class TestGamePlanIDOR:
    """User1 must not access User2's game plans."""

    def _create_user2_plan(self, user2_id):
        """Create a game plan for user2."""
        return GamePlanRepository.create(
            user_id=user2_id,
            belt_level="blue",
            archetype="guard_player",
            title="User2 Secret Plan",
        )

    def test_get_plan_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot GET User2's game plan by ID."""
        plan_id = self._create_user2_plan(test_user2["id"])
        response = authenticated_client.get(f"/api/v1/game-plans/{plan_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_update_plan_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot PATCH User2's game plan."""
        plan_id = self._create_user2_plan(test_user2["id"])
        response = authenticated_client.patch(
            f"/api/v1/game-plans/{plan_id}",
            json={"title": "HACKED by User1"},
        )
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_delete_plan_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot DELETE User2's game plan."""
        plan_id = self._create_user2_plan(test_user2["id"])
        response = authenticated_client.delete(f"/api/v1/game-plans/{plan_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_add_node_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot add nodes to User2's game plan."""
        plan_id = self._create_user2_plan(test_user2["id"])
        response = authenticated_client.post(
            f"/api/v1/game-plans/{plan_id}/nodes",
            json={"name": "Injected Node"},
        )
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_list_plans_isolation(self, authenticated_client, test_user, test_user2):
        """User1's plan list must not include User2's plans."""
        self._create_user2_plan(test_user2["id"])
        response = authenticated_client.get("/api/v1/game-plans/")
        assert response.status_code == 200
        data = response.json()
        # User1 has no plan, so should get plan=None
        if isinstance(data, dict) and "plan" in data:
            assert data["plan"] is None
        elif isinstance(data, dict) and "id" in data:
            assert data.get("user_id", test_user["id"]) == test_user["id"]


# ============================================================================
# Techniques IDOR Tests
# ============================================================================


class TestTechniquesIDOR:
    """User1 must not see User2's private technique training data."""

    def test_techniques_create_requires_auth(self, client, temp_db):
        """Creating a technique requires authentication."""
        response = client.post(
            "/api/v1/techniques/",
            json={"name": "Secret Move", "category": "submission"},
        )
        assert response.status_code == 401

    def test_stale_techniques_isolation(
        self,
        authenticated_client,
        test_user,
        test_user2,
        client,
    ):
        """User1's stale techniques should only reflect their own training."""
        # Note: Custom glossary entries are intentionally global
        # (shared reference data). IDOR protection applies to
        # per-user training data like stale technique analysis.
        response = authenticated_client.get("/api/v1/techniques/stale?days=7")
        assert response.status_code == 200
        data = response.json()
        # Should only contain User1's data (empty if no sessions)
        if isinstance(data, list):
            for t in data:
                assert t.get("user_id", test_user["id"]) == test_user["id"]


# ============================================================================
# Feed IDOR Tests (activity feed isolation)
# ============================================================================


class TestFeedIDOR:
    """User1's activity feed must not leak User2's private data."""

    def test_activity_feed_isolation(self, authenticated_client, test_user, test_user2):
        """User1's activity feed does not contain User2's sessions."""
        repo = SessionRepository()
        repo.create(
            user_id=test_user2["id"],
            session_date=date.today(),
            class_type="no-gi",
            gym_name="User2 Secret Gym",
            location="Nowhere",
            duration_mins=45,
            intensity=3,
            rolls=2,
            submissions_for=0,
            submissions_against=0,
        )

        response = authenticated_client.get("/api/v1/feed/activity")
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        for item in items:
            assert item.get("gym_name") != "User2 Secret Gym"
            assert item.get("user_id", test_user["id"]) == test_user["id"]


# ============================================================================
# Photos IDOR Tests
# ============================================================================


class TestPhotosIDOR:
    """User1 must not be able to access or delete User2's photos."""

    def _create_user2_session_and_photo(self, user2_id):
        """Create a session and photo for user2, return (session_id, photo_id)."""
        repo = SessionRepository()
        session_id = repo.create(
            user_id=user2_id,
            session_date=date.today(),
            class_type="gi",
            gym_name="User2 Photo Gym",
            location="User2 City",
            duration_mins=60,
            intensity=3,
            rolls=2,
            submissions_for=0,
            submissions_against=0,
        )
        photo_repo = ActivityPhotoRepository()
        photo_id = photo_repo.create(
            user_id=user2_id,
            activity_type="session",
            activity_id=session_id,
            activity_date=date.today().isoformat(),
            file_path="/fake/path/photo.jpg",
            file_name="test_photo.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            caption="User2 secret photo",
        )
        return session_id, photo_id

    def test_get_photo_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot GET User2's photo by ID."""
        _, photo_id = self._create_user2_session_and_photo(test_user2["id"])
        response = authenticated_client.get(f"/api/v1/photos/{photo_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_delete_photo_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot DELETE User2's photo."""
        _, photo_id = self._create_user2_session_and_photo(test_user2["id"])
        response = authenticated_client.delete(f"/api/v1/photos/{photo_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_get_activity_photos_idor(
        self, authenticated_client, test_user, test_user2
    ):
        """User1 cannot GET photos for User2's activity."""
        session_id, _ = self._create_user2_session_and_photo(test_user2["id"])
        response = authenticated_client.get(
            f"/api/v1/photos/activity/session/{session_id}"
        )
        assert response.status_code == 200
        data = response.json()
        # Should return empty list — user1 has no photos for this activity
        assert len(data) == 0, "User1 should not see User2's photos"

    def test_update_caption_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot update caption on User2's photo."""
        _, photo_id = self._create_user2_session_and_photo(test_user2["id"])
        response = authenticated_client.put(
            f"/api/v1/photos/{photo_id}/caption",
            data={"caption": "HACKED caption"},
        )
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"


# ============================================================================
# Videos IDOR Tests
# ============================================================================


class TestVideosIDOR:
    """User1 (non-admin) must not be able to delete videos."""

    def _create_movement_and_video(self):
        """Create a glossary movement and a video, return video_id."""
        from rivaflow.db.database import execute_insert, get_connection

        with get_connection() as conn:
            cursor = conn.cursor()
            movement_id = execute_insert(
                cursor,
                """
                INSERT INTO movements_glossary (name, category, description)
                VALUES (?, ?, ?)
                """,
                ("Test Armbar", "submission", "A test armbar movement"),
            )
        video = GlossaryRepository.add_custom_video(
            movement_id=movement_id,
            url="https://example.com/video.mp4",
            title="User2 Secret Video",
            video_type="general",
        )
        return video["id"]

    def test_delete_video_idor(self, authenticated_client, test_user, test_user2):
        """Non-admin User1 cannot DELETE a video."""
        video_id = self._create_movement_and_video()
        response = authenticated_client.delete(f"/api/v1/videos/{video_id}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_get_video_accessible(self, authenticated_client, test_user, test_user2):
        """Videos are global resources — any authenticated user can GET."""
        video_id = self._create_movement_and_video()
        response = authenticated_client.get(f"/api/v1/videos/{video_id}")
        # Videos are shared resources, so GET should succeed
        assert response.status_code == 200

    def test_list_videos_accessible(self, authenticated_client, test_user, test_user2):
        """Any authenticated user can list videos (they are global)."""
        self._create_movement_and_video()
        response = authenticated_client.get("/api/v1/videos/")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data


# ============================================================================
# Gradings IDOR Tests
# ============================================================================


class TestGradingsIDOR:
    """User1 must not be able to access or modify User2's gradings."""

    def _create_user2_grading(self, user2_id):
        """Create a grading for user2, return grading dict."""
        _ensure_profile({"id": user2_id, "first_name": "User", "last_name": "Two"})
        repo = GradingRepository()
        grading = repo.create(
            user_id=user2_id,
            grade="blue",
            date_graded=date.today().isoformat(),
            professor="Prof User2",
            notes="User2 secret grading",
        )
        return grading

    def test_list_gradings_isolation(self, authenticated_client, test_user, test_user2):
        """User1's grading list must not contain User2's gradings."""
        self._create_user2_grading(test_user2["id"])
        response = authenticated_client.get("/api/v1/gradings/")
        assert response.status_code == 200
        data = response.json()
        for g in data:
            assert g.get("user_id", test_user["id"]) == test_user["id"]
            assert g.get("notes") != "User2 secret grading"

    def test_update_grading_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot PUT User2's grading."""
        grading = self._create_user2_grading(test_user2["id"])
        response = authenticated_client.put(
            f"/api/v1/gradings/{grading['id']}",
            json={"grade": "black", "notes": "HACKED by User1"},
        )
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_delete_grading_idor(self, authenticated_client, test_user, test_user2):
        """User1 cannot DELETE User2's grading."""
        grading = self._create_user2_grading(test_user2["id"])
        response = authenticated_client.delete(f"/api/v1/gradings/{grading['id']}")
        assert response.status_code in (
            403,
            404,
        ), f"Expected 403/404, got {response.status_code}"

    def test_latest_grading_isolation(
        self, authenticated_client, test_user, test_user2
    ):
        """User1's latest grading must not return User2's grading."""
        self._create_user2_grading(test_user2["id"])
        response = authenticated_client.get("/api/v1/gradings/latest")
        assert response.status_code == 200
        data = response.json()
        # User1 has no gradings, so result should be null/None
        if data is not None:
            assert data.get("user_id", test_user["id"]) == test_user["id"]
            assert data.get("notes") != "User2 secret grading"
