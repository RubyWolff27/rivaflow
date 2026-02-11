"""Tests for WHOOP webhook endpoint."""

import base64
import hashlib
import hmac
import json
from unittest.mock import patch


class TestWhoopWebhook:
    """Tests for POST /api/v1/webhooks/whoop endpoint."""

    def _make_signature(
        self, body: bytes, secret: str, timestamp: str = "1707400000000"
    ) -> str:
        """Generate a valid WHOOP signature: base64(HMAC-SHA256(timestamp + body, secret))."""
        message = timestamp.encode() + body
        return base64.b64encode(
            hmac.new(secret.encode(), message, hashlib.sha256).digest()
        ).decode()

    @patch("rivaflow.api.routes.webhooks.settings")
    @patch("rivaflow.api.routes.webhooks._lookup_user_by_whoop_id")
    @patch("rivaflow.api.routes.webhooks.service")
    def test_valid_workout_webhook(
        self,
        mock_service,
        mock_lookup,
        mock_settings,
        client,
    ):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"
        mock_lookup.return_value = 42

        payload = {
            "type": "workout.updated",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()
        timestamp = "1707400000000"
        signature = self._make_signature(body, "test-secret", timestamp)

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={
                "X-WHOOP-Signature": signature,
                "X-WHOOP-Signature-Timestamp": timestamp,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_service.sync_workouts.assert_called_once_with(42, days_back=1)

    @patch("rivaflow.api.routes.webhooks.settings")
    @patch("rivaflow.api.routes.webhooks._lookup_user_by_whoop_id")
    @patch("rivaflow.api.routes.webhooks.service")
    def test_valid_recovery_webhook(
        self,
        mock_service,
        mock_lookup,
        mock_settings,
        client,
    ):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"
        mock_lookup.return_value = 42

        payload = {
            "type": "recovery.updated",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()
        timestamp = "1707400000000"
        signature = self._make_signature(body, "test-secret", timestamp)

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={
                "X-WHOOP-Signature": signature,
                "X-WHOOP-Signature-Timestamp": timestamp,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        mock_service.sync_recovery.assert_called_once_with(42, days_back=1)

    @patch("rivaflow.api.routes.webhooks.settings")
    def test_invalid_signature_rejected(self, mock_settings, client):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"

        payload = {
            "type": "workout.updated",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={
                "X-WHOOP-Signature": "bad-signature",
                "X-WHOOP-Signature-Timestamp": "1707400000000",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 401

    @patch("rivaflow.api.routes.webhooks.settings")
    def test_missing_signature_rejected(self, mock_settings, client):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"

        payload = {
            "type": "workout.updated",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 401

    @patch("rivaflow.api.routes.webhooks.settings")
    @patch("rivaflow.api.routes.webhooks._lookup_user_by_whoop_id")
    def test_unknown_user_ignored(self, mock_lookup, mock_settings, client):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"
        mock_lookup.return_value = None

        payload = {
            "type": "workout.updated",
            "user_id": "unknown_whoop_user",
        }
        body = json.dumps(payload).encode()
        timestamp = "1707400000000"
        signature = self._make_signature(body, "test-secret", timestamp)

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={
                "X-WHOOP-Signature": signature,
                "X-WHOOP-Signature-Timestamp": timestamp,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    @patch("rivaflow.api.routes.webhooks.settings")
    @patch("rivaflow.api.routes.webhooks._lookup_user_by_whoop_id")
    @patch("rivaflow.api.routes.webhooks.service")
    def test_unknown_event_type(
        self,
        mock_service,
        mock_lookup,
        mock_settings,
        client,
    ):
        mock_settings.WHOOP_CLIENT_SECRET = "test-secret"
        mock_lookup.return_value = 42

        payload = {
            "type": "something.unknown",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()
        timestamp = "1707400000000"
        signature = self._make_signature(body, "test-secret", timestamp)

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={
                "X-WHOOP-Signature": signature,
                "X-WHOOP-Signature-Timestamp": timestamp,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_service.sync_workouts.assert_not_called()
        mock_service.sync_recovery.assert_not_called()

    @patch("rivaflow.api.routes.webhooks.settings")
    @patch("rivaflow.api.routes.webhooks._lookup_user_by_whoop_id")
    @patch("rivaflow.api.routes.webhooks.service")
    def test_no_secret_rejects_webhook(
        self,
        mock_service,
        mock_lookup,
        mock_settings,
        client,
    ):
        """When WHOOP_CLIENT_SECRET is not set, reject the webhook (fail closed)."""
        mock_settings.WHOOP_CLIENT_SECRET = ""
        mock_lookup.return_value = 42

        payload = {
            "type": "workout.updated",
            "user_id": "whoop_user_1",
        }
        body = json.dumps(payload).encode()

        response = client.post(
            "/api/v1/webhooks/whoop",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 503
        mock_service.sync_workouts.assert_not_called()
