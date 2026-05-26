"""Tests for /api/v1/users/me/api-keys endpoints + dual-credential auth.

Per feat/api-keys PR — covers:
  - create returns the raw key exactly once
  - list never includes raw key material
  - revoke makes the key unusable
  - Bearer rf_pk_<...> authenticates an authorized request
  - Bearer <jwt> still authenticates after the auth path changes
  - revoked keys return 401
"""

from rivaflow.db.repositories.api_key_repo import ApiKeyRepository


class TestApiKeyGeneration:
    """Raw-key generation properties."""

    def test_generate_raw_key_has_prefix(self):
        key = ApiKeyRepository.generate_raw_key()
        assert key.startswith("rf_pk_"), f"expected rf_pk_ prefix, got: {key[:8]}"

    def test_generate_raw_key_is_unique(self):
        seen = {ApiKeyRepository.generate_raw_key() for _ in range(200)}
        assert len(seen) == 200, "raw keys must be unique under repeated generation"

    def test_hash_key_is_deterministic(self):
        key = "rf_pk_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        assert ApiKeyRepository.hash_key(key) == ApiKeyRepository.hash_key(key)

    def test_hash_key_differs_per_input(self):
        a = ApiKeyRepository.hash_key("rf_pk_aaaa")
        b = ApiKeyRepository.hash_key("rf_pk_bbbb")
        assert a != b

    def test_display_prefix_length(self):
        key = "rf_pk_a1b2c3d4e5f6g7h8i9j0"
        # "rf_pk_" + 6 chars = 12
        assert ApiKeyRepository.display_prefix(key) == "rf_pk_a1b2c3"


class TestApiKeyEndpoints:
    """Live endpoint flow: create → list → use → revoke."""

    def test_create_returns_raw_key_exactly_once(self, client, auth_headers):
        resp = client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={"name": "Sage MCP"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Sage MCP"
        assert data["raw_key"].startswith("rf_pk_")
        assert data["key_prefix"].startswith("rf_pk_")
        assert data["revoked_at"] is None

    def test_list_never_includes_raw_key(self, client, auth_headers):
        client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={"name": "list-test"},
        )
        resp = client.get("/api/v1/users/me/api-keys", headers=auth_headers)
        assert resp.status_code == 200
        for entry in resp.json():
            assert "raw_key" not in entry, "list endpoint must never include raw_key"
            assert "key_hash" not in entry, "list endpoint must never include key_hash"

    def test_api_key_authenticates_subsequent_request(self, client, auth_headers):
        created = client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={"name": "auth-test"},
        ).json()
        raw_key = created["raw_key"]

        # Use the raw key as a Bearer credential
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 200, resp.text

    def test_revoke_makes_key_unusable(self, client, auth_headers):
        created = client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={"name": "revoke-test"},
        ).json()
        raw_key = created["raw_key"]
        api_key_id = created["id"]

        # Revoke
        del_resp = client.delete(
            f"/api/v1/users/me/api-keys/{api_key_id}",
            headers=auth_headers,
        )
        assert del_resp.status_code == 204

        # Subsequent use returns 401
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 401

    def test_revoke_twice_returns_404(self, client, auth_headers):
        created = client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={"name": "double-revoke-test"},
        ).json()
        api_key_id = created["id"]
        client.delete(f"/api/v1/users/me/api-keys/{api_key_id}", headers=auth_headers)
        second = client.delete(
            f"/api/v1/users/me/api-keys/{api_key_id}",
            headers=auth_headers,
        )
        assert second.status_code == 404

    def test_create_requires_name(self, client, auth_headers):
        resp = client.post(
            "/api/v1/users/me/api-keys",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 422

    def test_jwt_still_works_after_dual_auth_change(self, client, auth_headers):
        """Existing JWT-based clients must keep working after the dual-auth refactor."""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200

    # NB: cross-user revoke isolation is enforced at the SQL layer in
    # ApiKeyRepository.revoke() via `WHERE id = ? AND user_id = ?`. A route-
    # level test would need a `second_user_auth_headers` fixture which doesn't
    # exist in conftest yet — if added later, the test would be:
    #
    #     second user DELETEs first user's api_key_id → expect 404
    #     first user's key still authenticates → 200
