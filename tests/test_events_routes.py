"""Integration tests for events and competition prep routes."""

from datetime import date, timedelta


class TestCreateEvent:
    """Tests for POST /api/v1/events/."""

    def test_create_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.post(
            "/api/v1/events/",
            json={
                "name": "Test Comp",
                "event_date": "2025-06-15",
            },
        )
        assert resp.status_code == 401

    def test_create_event_success(self, authenticated_client, test_user):
        """Creates an event and returns 201 with event data."""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        resp = authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "IBJJF Open",
                "event_type": "competition",
                "event_date": future_date,
                "location": "Sydney",
                "weight_class": "Medium Heavy",
                "division": "Adult Blue",
                "notes": "First competition",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "IBJJF Open"
        assert data["event_date"] == future_date
        assert data["location"] == "Sydney"

    def test_create_event_minimal(self, authenticated_client, test_user):
        """Creates an event with only required fields."""
        resp = authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Local Comp",
                "event_date": "2025-08-01",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Local Comp"
        assert data["status"] == "upcoming"


class TestListEvents:
    """Tests for GET /api/v1/events/."""

    def test_list_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/events/")
        assert resp.status_code == 401

    def test_list_empty(self, authenticated_client, test_user):
        """Returns empty list when no events exist."""
        resp = authenticated_client.get("/api/v1/events/")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data
        assert data["total"] == 0
        assert data["events"] == []

    def test_list_after_create(self, authenticated_client, test_user):
        """Returns created events in list."""
        authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Comp A",
                "event_date": "2025-07-01",
            },
        )
        authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Comp B",
                "event_date": "2025-08-01",
            },
        )
        resp = authenticated_client.get("/api/v1/events/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    def test_list_filter_by_status(self, authenticated_client, test_user):
        """Can filter events by status."""
        authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Upcoming",
                "event_date": "2025-07-01",
                "status": "upcoming",
            },
        )
        resp = authenticated_client.get("/api/v1/events/?status=upcoming")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for event in data["events"]:
            assert event["status"] == "upcoming"


class TestGetEvent:
    """Tests for GET /api/v1/events/{event_id}."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/events/1")
        assert resp.status_code == 401

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Returns 404 for event that doesn't exist."""
        resp = authenticated_client.get("/api/v1/events/999999")
        assert resp.status_code == 404

    def test_get_created_event(self, authenticated_client, test_user):
        """Can retrieve a created event by ID."""
        create_resp = authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Fetch Me",
                "event_date": "2025-09-01",
            },
        )
        event_id = create_resp.json()["id"]
        resp = authenticated_client.get(f"/api/v1/events/{event_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch Me"


class TestUpdateEvent:
    """Tests for PUT /api/v1/events/{event_id}."""

    def test_update_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.put(
            "/api/v1/events/1",
            json={"name": "Updated"},
        )
        assert resp.status_code == 401

    def test_update_nonexistent_returns_404(self, authenticated_client, test_user):
        """Returns 404 when updating non-existent event."""
        resp = authenticated_client.put(
            "/api/v1/events/999999",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404

    def test_update_event_name(self, authenticated_client, test_user):
        """Can update event name."""
        create_resp = authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "Original",
                "event_date": "2025-10-01",
            },
        )
        event_id = create_resp.json()["id"]
        resp = authenticated_client.put(
            f"/api/v1/events/{event_id}",
            json={"name": "Renamed"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"


class TestDeleteEvent:
    """Tests for DELETE /api/v1/events/{event_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.delete("/api/v1/events/1")
        assert resp.status_code == 401

    def test_delete_nonexistent_returns_404(self, authenticated_client, test_user):
        """Returns 404 when deleting non-existent event."""
        resp = authenticated_client.delete("/api/v1/events/999999")
        assert resp.status_code == 404

    def test_delete_event_success(self, authenticated_client, test_user):
        """Deleting an event returns 204."""
        create_resp = authenticated_client.post(
            "/api/v1/events/",
            json={
                "name": "To Delete",
                "event_date": "2025-11-01",
            },
        )
        event_id = create_resp.json()["id"]
        resp = authenticated_client.delete(f"/api/v1/events/{event_id}")
        assert resp.status_code == 204

        # Verify it's gone
        get_resp = authenticated_client.get(f"/api/v1/events/{event_id}")
        assert get_resp.status_code == 404


class TestNextEvent:
    """Tests for GET /api/v1/events/next."""

    def test_next_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/events/next")
        assert resp.status_code == 401

    def test_next_no_events(self, authenticated_client, test_user):
        """Returns null event when no upcoming events."""
        resp = authenticated_client.get("/api/v1/events/next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"] is None
        assert data["days_until"] is None
