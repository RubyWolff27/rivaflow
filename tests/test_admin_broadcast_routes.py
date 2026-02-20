"""Tests for admin email broadcast routes."""


class TestBroadcastAccessControl:
    """Non-admin users are rejected."""

    def test_unauthenticated_gets_401(self, client, temp_db):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            json={
                "subject": "Hello",
                "html_body": "<p>Hi</p>",
            },
        )
        assert resp.status_code in (401, 403)

    def test_non_admin_gets_403(self, client, test_user, auth_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=auth_headers,
            json={
                "subject": "Hello",
                "html_body": "<p>Hi</p>",
            },
        )
        assert resp.status_code == 403


class TestBroadcastHappyPath:
    """Admin can send broadcast emails."""

    def test_broadcast_queued(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Weekly Update",
                "html_body": "<p>Hello {{first_name}}</p>",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "recipient_count" in data
        assert isinstance(data["recipient_count"], int)

    def test_broadcast_with_text_body(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Plain text too",
                "html_body": "<p>HTML version</p>",
                "text_body": "Plain text version",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recipient_count"] >= 0


class TestBroadcastValidation:
    """Broadcast validates input correctly."""

    def test_missing_subject_returns_422(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "html_body": "<p>No subject</p>",
            },
        )
        assert resp.status_code == 422

    def test_missing_html_body_returns_422(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Has subject but no body",
            },
        )
        assert resp.status_code == 422

    def test_empty_subject_returns_422(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "",
                "html_body": "<p>Body</p>",
            },
        )
        assert resp.status_code == 422

    def test_script_tag_rejected(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "XSS attempt",
                "html_body": "<script>alert('xss')</script>",
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "disallowed" in data["error"]["message"].lower()

    def test_iframe_tag_rejected(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Iframe attempt",
                "html_body": '<iframe src="http://evil.com"></iframe>',
            },
        )
        assert resp.status_code == 400

    def test_event_handler_rejected(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Event handler",
                "html_body": "<div onclick=alert(1)>click</div>",
            },
        )
        assert resp.status_code == 400

    def test_safe_html_accepted(self, client, admin_user, admin_headers):
        resp = client.post(
            "/api/v1/admin/email/broadcast",
            headers=admin_headers,
            json={
                "subject": "Safe HTML",
                "html_body": (
                    "<h1>Welcome</h1>"
                    "<p>Hello <strong>{{first_name}}</strong></p>"
                    '<a href="https://rivaflow.app">Visit</a>'
                ),
            },
        )
        assert resp.status_code == 200
