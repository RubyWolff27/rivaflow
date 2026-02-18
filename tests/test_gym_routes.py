"""Tests for gym routes and GymClassRepository (Wave 4 coverage).

Covers:
- GymClassRepository CRUD (create, get, update, delete)
- GymClassRepository.bulk_replace()
- Public API: GET /gyms/{id}/timetable
- Public API: GET /gyms/{id}/timetable/today
- 404 for non-existent gym timetable
"""

from datetime import datetime, timedelta

from rivaflow.core.auth import create_access_token
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.gym_class_repo import (
    GymClassRepository,
)
from rivaflow.db.repositories.gym_repo import GymRepository


def _create_gym(name: str = "Test Gym") -> int:
    """Create a verified gym and return its ID."""
    repo = GymRepository()
    gym = repo.create(
        name=name,
        city="Sydney",
        state="NSW",
        country="Australia",
        verified=True,
    )
    return gym["id"]


def _make_admin(user_id: int) -> None:
    """Promote a user to admin."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE users SET is_admin = ?" " WHERE id = ?"),
            (True, user_id),
        )


def _admin_headers(user_id: int) -> dict:
    token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


# ── GymClassRepository CRUD ───────────────────────────────────


class TestGymClassRepoCRUD:
    """Direct repository tests for gym_classes table."""

    def test_create_and_get(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        class_id = repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="9:00",
            end_time="10:30",
            class_name="Morning Gi",
            class_type="gi",
            level="all",
        )
        assert class_id > 0

        classes = repo.get_by_gym(gym_id)
        assert len(classes) == 1
        c = classes[0]
        assert c["class_name"] == "Morning Gi"
        assert c["class_type"] == "gi"
        assert c["day_of_week"] == 0
        assert c["day_name"] == "Monday"
        assert c["start_time"] == "9:00"
        assert c["end_time"] == "10:30"

    def test_get_by_gym_and_day(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        # Monday classes (use zero-padded times
        # for consistent string ordering)
        repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="09:00",
            end_time="10:00",
            class_name="AM Gi",
        )
        repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="18:00",
            end_time="19:30",
            class_name="PM No-Gi",
        )
        # Tuesday class
        repo.create(
            gym_id=gym_id,
            day_of_week=1,
            start_time="12:00",
            end_time="13:00",
            class_name="Lunch Open Mat",
        )

        monday = repo.get_by_gym_and_day(gym_id, 0)
        assert len(monday) == 2
        names = {c["class_name"] for c in monday}
        assert names == {"AM Gi", "PM No-Gi"}

        tuesday = repo.get_by_gym_and_day(gym_id, 1)
        assert len(tuesday) == 1

    def test_update_class(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        class_id = repo.create(
            gym_id=gym_id,
            day_of_week=2,
            start_time="10:00",
            end_time="11:00",
            class_name="Old Name",
        )

        result = repo.update(
            class_id,
            class_name="New Name",
            class_type="no-gi",
            level="advanced",
        )
        assert result is not None

        # Re-fetch after commit to see the update
        # (update reads back in same txn, may be stale)
        updated = repo._get_by_id(class_id)
        assert updated is not None
        assert updated["class_name"] == "New Name"
        assert updated["class_type"] == "no-gi"
        assert updated["level"] == "advanced"

    def test_update_nonexistent_returns_none(self, temp_db):
        repo = GymClassRepository()
        result = repo.update(99999, class_name="Ghost")
        assert result is None

    def test_delete_class(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        class_id = repo.create(
            gym_id=gym_id,
            day_of_week=3,
            start_time="7:00",
            end_time="8:00",
            class_name="Early Bird",
        )
        assert repo.delete(class_id) is True

        # Should be gone
        classes = repo.get_by_gym(gym_id)
        assert len(classes) == 0

    def test_delete_nonexistent_returns_false(self, temp_db):
        repo = GymClassRepository()
        assert repo.delete(99999) is False

    def test_empty_gym_returns_empty_list(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()
        classes = repo.get_by_gym(gym_id)
        assert classes == []


# ── Bulk replace ───────────────────────────────────────────────


class TestGymClassRepoBulkReplace:
    """bulk_replace deletes old classes and inserts new."""

    def test_bulk_replace_clears_old(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        # Seed two classes
        repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="9:00",
            end_time="10:00",
            class_name="Old Class 1",
        )
        repo.create(
            gym_id=gym_id,
            day_of_week=1,
            start_time="9:00",
            end_time="10:00",
            class_name="Old Class 2",
        )

        # Replace with a single new class
        new_classes = [
            {
                "day_of_week": 4,
                "start_time": "17:00",
                "end_time": "18:30",
                "class_name": "Friday Comp",
                "class_type": "competition",
                "level": "advanced",
            }
        ]
        ids = repo.bulk_replace(gym_id, new_classes)

        assert len(ids) == 1
        assert ids[0] > 0

        remaining = repo.get_by_gym(gym_id)
        assert len(remaining) == 1
        assert remaining[0]["class_name"] == "Friday Comp"

    def test_bulk_replace_empty_clears_all(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="9:00",
            end_time="10:00",
            class_name="Temp",
        )

        ids = repo.bulk_replace(gym_id, [])
        assert ids == []
        assert repo.get_by_gym(gym_id) == []

    def test_bulk_replace_multiple(self, temp_db):
        gym_id = _create_gym()
        repo = GymClassRepository()

        classes = [
            {
                "day_of_week": d,
                "start_time": "9:00",
                "end_time": "10:00",
                "class_name": f"Day {d}",
            }
            for d in range(5)
        ]
        ids = repo.bulk_replace(gym_id, classes)
        assert len(ids) == 5

        all_classes = repo.get_by_gym(gym_id)
        assert len(all_classes) == 5


# ── Public gym timetable API ──────────────────────────────────


class TestGymTimetableAPI:
    """GET /gyms/{id}/timetable and /timetable/today."""

    def test_get_timetable(
        self,
        client,
        test_user,
        auth_headers,
        temp_db,
    ):
        gym_id = _create_gym("API Gym")
        repo = GymClassRepository()
        repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="9:00",
            end_time="10:00",
            class_name="Mon Class",
        )
        repo.create(
            gym_id=gym_id,
            day_of_week=2,
            start_time="18:00",
            end_time="19:00",
            class_name="Wed Class",
        )

        resp = client.get(
            f"/api/v1/gyms/{gym_id}/timetable",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["gym_id"] == gym_id
        assert data["gym_name"] == "API Gym"
        # Timetable is a dict grouped by day name
        assert isinstance(data["timetable"], dict)
        assert "Monday" in data["timetable"]
        assert "Wednesday" in data["timetable"]
        assert len(data["timetable"]["Monday"]) == 1
        assert len(data["timetable"]["Wednesday"]) == 1

    def test_timetable_nonexistent_gym_404(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/gyms/99999/timetable",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_get_todays_classes(
        self,
        client,
        test_user,
        auth_headers,
        temp_db,
    ):
        gym_id = _create_gym("Today Gym")
        today_dow = datetime.now().weekday()
        repo = GymClassRepository()
        repo.create(
            gym_id=gym_id,
            day_of_week=today_dow,
            start_time="10:00",
            end_time="11:30",
            class_name="Today's Class",
            class_type="gi",
        )
        # Also add a class on a different day
        other_day = (today_dow + 1) % 7
        repo.create(
            gym_id=gym_id,
            day_of_week=other_day,
            start_time="10:00",
            end_time="11:30",
            class_name="Other Day",
        )

        resp = client.get(
            f"/api/v1/gyms/{gym_id}/timetable/today",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["gym_id"] == gym_id
        assert isinstance(data["classes"], list)
        # Only today's class should appear
        assert len(data["classes"]) == 1
        assert data["classes"][0]["class_name"] == "Today's Class"

    def test_todays_classes_nonexistent_gym_404(self, client, test_user, auth_headers):
        resp = client.get(
            "/api/v1/gyms/99999/timetable/today",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_timetable_empty_gym(
        self,
        client,
        test_user,
        auth_headers,
        temp_db,
    ):
        """Gym with no classes returns empty timetable."""
        gym_id = _create_gym("Empty Gym")

        resp = client.get(
            f"/api/v1/gyms/{gym_id}/timetable",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Empty gym => empty dict (no days)
        assert data["timetable"] == {}


# ── Admin timetable endpoints ─────────────────────────────────


class TestAdminTimetableAPI:
    """Admin endpoints for managing gym timetables."""

    def test_admin_set_timetable(self, client, test_user, temp_db):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        gym_id = _create_gym("Admin Gym")

        resp = client.post(
            f"/api/v1/admin/gyms/{gym_id}/timetable",
            headers=headers,
            json={
                "classes": [
                    {
                        "day_of_week": 0,
                        "start_time": "6:00",
                        "end_time": "7:30",
                        "class_name": "Dawn Patrol",
                        "class_type": "gi",
                        "level": "all",
                    },
                    {
                        "day_of_week": 2,
                        "start_time": "18:00",
                        "end_time": "19:30",
                        "class_name": "Evening No-Gi",
                        "class_type": "no-gi",
                        "level": "intermediate",
                    },
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["classes_created"] == 2

    def test_admin_add_single_class(self, client, test_user, temp_db):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        gym_id = _create_gym("Single Gym")

        resp = client.post(
            f"/api/v1/admin/gyms/{gym_id}/classes",
            headers=headers,
            json={
                "day_of_week": 5,
                "start_time": "10:00",
                "end_time": "12:00",
                "class_name": "Saturday Open Mat",
                "class_type": "open-mat",
                "level": "all",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["class_id"] > 0

    def test_admin_delete_class(self, client, test_user, temp_db):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])
        gym_id = _create_gym("Delete Gym")

        # Create a class
        repo = GymClassRepository()
        class_id = repo.create(
            gym_id=gym_id,
            day_of_week=0,
            start_time="9:00",
            end_time="10:00",
            class_name="To Delete",
        )

        resp = client.delete(
            f"/api/v1/admin/gyms/{gym_id}" f"/classes/{class_id}",
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify deletion
        assert repo.get_by_gym(gym_id) == []

    def test_admin_timetable_nonexistent_gym_404(self, client, test_user, temp_db):
        _make_admin(test_user["id"])
        headers = _admin_headers(test_user["id"])

        resp = client.post(
            "/api/v1/admin/gyms/99999/timetable",
            headers=headers,
            json={"classes": []},
        )
        assert resp.status_code == 404

    def test_non_admin_cannot_set_timetable(
        self, client, test_user, auth_headers, temp_db
    ):
        gym_id = _create_gym("Blocked Gym")

        resp = client.post(
            f"/api/v1/admin/gyms/{gym_id}/timetable",
            headers=auth_headers,
            json={"classes": []},
        )
        assert resp.status_code == 403
