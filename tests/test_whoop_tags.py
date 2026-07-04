"""P1 — WHOOP journal tags: capture route + repo (runs against Postgres in CI via temp_db)."""

from __future__ import annotations

from rivaflow.db.repositories.whoop_repo import WhoopRepository


class TestWhoopTagRepo:
    def test_add_and_tagged_days(self, test_user):
        uid = test_user["id"]
        WhoopRepository.add_tag(uid, "2026-06-01", "ill")
        WhoopRepository.add_tag(uid, "2026-06-05", "ill")
        WhoopRepository.add_tag(uid, "2026-06-05", "alcohol")
        assert WhoopRepository.tagged_days(uid, "ill") == {"2026-06-01", "2026-06-05"}
        assert WhoopRepository.tagged_days(uid, "alcohol") == {"2026-06-05"}

    def test_add_is_idempotent(self, test_user):
        uid = test_user["id"]
        WhoopRepository.add_tag(uid, "2026-06-10", "poor-sleep")
        WhoopRepository.add_tag(uid, "2026-06-10", "poor-sleep")
        rows = [r for r in WhoopRepository.list_tags(uid) if r["tag"] == "poor-sleep"]
        assert len(rows) == 1

    def test_remove_tag(self, test_user):
        uid = test_user["id"]
        WhoopRepository.add_tag(uid, "2026-06-12", "travel")
        assert "2026-06-12" in WhoopRepository.tagged_days(uid, "travel")
        WhoopRepository.remove_tag(uid, "2026-06-12", "travel")
        assert "2026-06-12" not in WhoopRepository.tagged_days(uid, "travel")

    def test_list_tags_bounded(self, test_user):
        uid = test_user["id"]
        for d in ("2026-05-01", "2026-06-01", "2026-07-01"):
            WhoopRepository.add_tag(uid, d, "late-training")
        days = {
            r["day"] if isinstance(r["day"], str) else r["day"].isoformat()
            for r in WhoopRepository.list_tags(
                uid, start="2026-06-01", end="2026-06-30"
            )
        }
        assert "2026-06-01" in days
        assert "2026-05-01" not in days and "2026-07-01" not in days


class TestWhoopTagEndpoints:
    def test_post_get_delete_flow(self, client, auth_headers):
        # create
        r = client.post(
            "/api/v1/whoop/tag",
            headers=auth_headers,
            json={"day": "2026-06-20", "tag": "ill"},
        )
        assert r.status_code == 200, r.text
        # list
        r = client.get("/api/v1/whoop/tags", headers=auth_headers)
        assert r.status_code == 200
        assert any(row["tag"] == "ill" for row in r.json())
        # delete
        r = client.request(
            "DELETE",
            "/api/v1/whoop/tag",
            headers=auth_headers,
            params={"day": "2026-06-20", "tag": "ill"},
        )
        assert r.status_code == 200
