"""Wave 0 security regression tests for the WHOOP platform.

Covers the fixes from the 2026-07-09 Bitter-Lesson audit:
  - IDOR: PATCH /whoop/session/{id}/end is scoped to the owning user
  - Read-only 'rf_vk_' API keys are rejected on every write/admin route
    but accepted on reads and on the bookmarkable dashboard URLs
  - The dead WHOOP-cloud webhook is not registered by default

Requires PostgreSQL (see conftest). These run in CI where DATABASE_URL is set.
"""

from rivaflow.core.auth import create_access_token
from rivaflow.db.repositories.api_key_repo import ApiKeyRepository
from rivaflow.db.repositories.whoop_repo import WhoopRepository


def _headers_for(user_id: int) -> dict:
    return {
        "Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"
    }


def _mint_key(client, auth_headers, *, read_only: bool) -> str:
    resp = client.post(
        "/api/v1/users/me/api-keys",
        headers=auth_headers,
        json={"name": "view" if read_only else "full", "read_only": read_only},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["raw_key"]


class TestSessionEndIDOR:
    def test_cannot_end_another_users_session(
        self, client, test_user, test_user2, auth_headers
    ):
        # user A (auth_headers == test_user) opens a session
        created = client.post(
            "/api/v1/whoop/session",
            headers=auth_headers,
            json={"activity": "bjj", "started_at": "2026-07-09T12:00:00+10:00"},
        )
        assert created.status_code == 200, created.text
        session_id = created.json()["id"]

        # user B tries to close it → 404, and the row must be untouched
        attack = client.patch(
            f"/api/v1/whoop/session/{session_id}/end",
            headers=_headers_for(test_user2["id"]),
            json={"ended_at": "2026-07-09T13:00:00+10:00"},
        )
        assert attack.status_code == 404, attack.text
        rows = WhoopRepository.list_whoop_sessions(test_user["id"])
        assert (
            rows[0]["ended_at"] is None
        ), "session must remain open after IDOR attempt"

        # the owner can close it
        ok = client.patch(
            f"/api/v1/whoop/session/{session_id}/end",
            headers=auth_headers,
            json={"ended_at": "2026-07-09T13:00:00+10:00"},
        )
        assert ok.status_code == 200, ok.text


class TestReadOnlyKeyScope:
    def test_read_only_key_has_view_prefix_and_scope(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        assert raw.startswith("rf_vk_"), raw[:8]
        row = ApiKeyRepository.get_active_by_hash(ApiKeyRepository.hash_key(raw))
        assert row["scopes"] == "read"

    def test_read_only_key_can_read(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        resp = client.get(
            "/api/v1/whoop/summary", headers={"Authorization": f"Bearer {raw}"}
        )
        # Authenticated + not scope-blocked (data may be empty, but never 401/403).
        assert resp.status_code not in (401, 403), resp.text

    def test_read_only_key_rejected_on_ingest(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        resp = client.post(
            "/api/v1/whoop/ingest",
            headers={"Authorization": f"Bearer {raw}"},
            json={},
        )
        assert resp.status_code == 403, resp.text

    def test_read_only_key_rejected_on_session_create(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        resp = client.post(
            "/api/v1/whoop/session",
            headers={"Authorization": f"Bearer {raw}"},
            json={"activity": "bjj", "started_at": "2026-07-09T12:00:00+10:00"},
        )
        assert resp.status_code == 403, resp.text

    def test_read_only_key_cannot_mint_keys(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        resp = client.post(
            "/api/v1/users/me/api-keys",
            headers={"Authorization": f"Bearer {raw}"},
            json={"name": "escalate"},
        )
        assert resp.status_code == 403, resp.text

    def test_full_key_can_write(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=False)
        assert raw.startswith("rf_pk_")
        resp = client.post(
            "/api/v1/whoop/ingest",
            headers={"Authorization": f"Bearer {raw}"},
            json={},
        )
        assert resp.status_code != 403, resp.text


class TestDashboardAcceptsViewKey:
    def test_cockpit_accepts_read_only_key(self, client, auth_headers):
        raw = _mint_key(client, auth_headers, read_only=True)
        resp = client.get("/api/v1/whoop/cockpit", params={"key": raw})
        assert resp.status_code != 401, resp.text

    def test_cockpit_rejects_bogus_key(self, client):
        resp = client.get("/api/v1/whoop/cockpit", params={"key": "rf_vk_bogus"})
        assert resp.status_code == 401


class TestDeadWebhookGated:
    def test_whoop_webhook_404s_when_integration_disabled(self, client):
        # Default ENABLE_WHOOP_INTEGRATION=false → the dead-era webhook 404s and
        # exposes no unauthenticated surface.
        resp = client.post("/api/v1/webhooks/whoop", json={})
        assert resp.status_code == 404, resp.text
