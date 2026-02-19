"""Unit tests for EventsService -- events and competition prep."""

from unittest.mock import patch

from rivaflow.core.services.events_service import EventsService


class TestCreateEvent:
    """Tests for create_event."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_creates_event_and_returns_id(self, MockEventRepo, MockWeightRepo):
        """Should create an event and return its ID."""
        MockEventRepo.return_value.create.return_value = 42

        service = EventsService()
        result = service.create_event(
            user_id=1, data={"name": "IBJJF Worlds", "event_date": "2025-06-01"}
        )

        assert result == 42
        MockEventRepo.return_value.create.assert_called_once_with(
            user_id=1,
            data={"name": "IBJJF Worlds", "event_date": "2025-06-01"},
        )


class TestGetEventById:
    """Tests for get_event_by_id."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_event(self, MockEventRepo, MockWeightRepo):
        """Should return event dict when found."""
        mock_event = {"id": 1, "name": "Local Comp", "status": "upcoming"}
        MockEventRepo.return_value.get_by_id.return_value = mock_event

        service = EventsService()
        result = service.get_event_by_id(user_id=1, event_id=1)

        assert result == mock_event

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_none_when_not_found(self, MockEventRepo, MockWeightRepo):
        """Should return None when event does not exist."""
        MockEventRepo.return_value.get_by_id.return_value = None

        service = EventsService()
        result = service.get_event_by_id(user_id=1, event_id=999)

        assert result is None


class TestListEvents:
    """Tests for list_events."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_lists_all_events(self, MockEventRepo, MockWeightRepo):
        """Should return all events for a user."""
        mock_events = [
            {"id": 1, "name": "Comp A"},
            {"id": 2, "name": "Comp B"},
        ]
        MockEventRepo.return_value.list_by_user.return_value = mock_events

        service = EventsService()
        result = service.list_events(user_id=1)

        assert len(result) == 2
        MockEventRepo.return_value.list_by_user.assert_called_once_with(
            user_id=1, status=None
        )

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_filters_by_status(self, MockEventRepo, MockWeightRepo):
        """Should pass status filter to repository."""
        MockEventRepo.return_value.list_by_user.return_value = []

        service = EventsService()
        service.list_events(user_id=1, status="upcoming")

        MockEventRepo.return_value.list_by_user.assert_called_once_with(
            user_id=1, status="upcoming"
        )

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_empty_list(self, MockEventRepo, MockWeightRepo):
        """Should return empty list when no events exist."""
        MockEventRepo.return_value.list_by_user.return_value = []

        service = EventsService()
        result = service.list_events(user_id=1)

        assert result == []


class TestUpdateEvent:
    """Tests for update_event."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_updates_event(self, MockEventRepo, MockWeightRepo):
        """Should return True when update succeeds."""
        MockEventRepo.return_value.update.return_value = True

        service = EventsService()
        result = service.update_event(
            user_id=1, event_id=1, data={"name": "Updated Name"}
        )

        assert result is True

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_false_when_not_found(self, MockEventRepo, MockWeightRepo):
        """Should return False when event does not exist."""
        MockEventRepo.return_value.update.return_value = False

        service = EventsService()
        result = service.update_event(user_id=1, event_id=999, data={"name": "X"})

        assert result is False


class TestDeleteEvent:
    """Tests for delete_event."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_deletes_event(self, MockEventRepo, MockWeightRepo):
        """Should return True when event is deleted."""
        MockEventRepo.return_value.delete.return_value = True

        service = EventsService()
        result = service.delete_event(user_id=1, event_id=1)

        assert result is True

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_false_when_not_found(self, MockEventRepo, MockWeightRepo):
        """Should return False when event does not exist."""
        MockEventRepo.return_value.delete.return_value = False

        service = EventsService()
        result = service.delete_event(user_id=1, event_id=999)

        assert result is False


class TestGetNextUpcoming:
    """Tests for get_next_upcoming."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_next_event(self, MockEventRepo, MockWeightRepo):
        """Should return the next upcoming event."""
        mock_event = {"id": 3, "name": "Next Comp", "event_date": "2025-03-15"}
        MockEventRepo.return_value.get_next_upcoming.return_value = mock_event

        service = EventsService()
        result = service.get_next_upcoming(user_id=1)

        assert result == mock_event

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_returns_none_when_no_upcoming(self, MockEventRepo, MockWeightRepo):
        """Should return None when no upcoming events exist."""
        MockEventRepo.return_value.get_next_upcoming.return_value = None

        service = EventsService()
        result = service.get_next_upcoming(user_id=1)

        assert result is None


class TestWeightLogs:
    """Tests for weight log methods."""

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_create_weight_log(self, MockEventRepo, MockWeightRepo):
        """Should create a weight log and return its ID."""
        MockWeightRepo.return_value.create.return_value = 7

        service = EventsService()
        result = service.create_weight_log(
            user_id=1, data={"weight_kg": 77.5, "log_date": "2025-01-20"}
        )

        assert result == 7

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_list_weight_logs(self, MockEventRepo, MockWeightRepo):
        """Should return weight logs within date range."""
        mock_logs = [{"id": 1, "weight_kg": 77.5}]
        MockWeightRepo.return_value.list_by_user.return_value = mock_logs

        service = EventsService()
        result = service.list_weight_logs(
            user_id=1, start_date="2025-01-01", end_date="2025-01-31"
        )

        assert len(result) == 1
        MockWeightRepo.return_value.list_by_user.assert_called_once_with(
            user_id=1, start_date="2025-01-01", end_date="2025-01-31"
        )

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_get_latest_weight(self, MockEventRepo, MockWeightRepo):
        """Should return latest weight entry."""
        mock_entry = {"id": 5, "weight_kg": 78.0}
        MockWeightRepo.return_value.get_latest.return_value = mock_entry

        service = EventsService()
        result = service.get_latest_weight(user_id=1)

        assert result == mock_entry

    @patch("rivaflow.core.services.events_service.WeightLogRepository")
    @patch("rivaflow.core.services.events_service.EventRepository")
    def test_get_weight_averages(self, MockEventRepo, MockWeightRepo):
        """Should return weight averages for the specified period."""
        mock_avgs = [{"week": "2025-W3", "avg_kg": 77.2}]
        MockWeightRepo.return_value.get_averages.return_value = mock_avgs

        service = EventsService()
        result = service.get_weight_averages(user_id=1, period="weekly")

        assert result == mock_avgs
        MockWeightRepo.return_value.get_averages.assert_called_once_with(
            user_id=1, period="weekly"
        )
