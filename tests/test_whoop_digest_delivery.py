"""P2 — WHOOP digest delivery: alert repo + endpoints (Postgres in CI via temp_db)."""

from __future__ import annotations

from rivaflow.db.repositories.whoop_repo import WhoopRepository


class TestWhoopAlertRepo:
    def test_record_and_cooldown_map(self, test_user):
        uid = test_user["id"]
        WhoopRepository.record_alert(
            uid, "2026-06-01", "prevention:amber", "amber", "watch"
        )
        WhoopRepository.record_alert(
            uid, "2026-06-05", "prevention:amber", "amber", "watch again"
        )
        WhoopRepository.record_alert(uid, "2026-06-05", "prevention:red", "red", "rest")
        last = WhoopRepository.last_alert_days(uid)
        assert last["prevention:amber"] == "2026-06-05"  # most recent
        assert last["prevention:red"] == "2026-06-05"

    def test_record_is_idempotent_per_day_key(self, test_user):
        uid = test_user["id"]
        WhoopRepository.record_alert(
            uid, "2026-06-10", "prevention:amber", "amber", "x"
        )
        WhoopRepository.record_alert(
            uid, "2026-06-10", "prevention:amber", "amber", "x"
        )
        rows = [
            r
            for r in WhoopRepository.recent_alerts(uid)
            if r["day"] and str(r["day"]).startswith("2026-06-10")
        ]
        assert len(rows) == 1


class TestWhoopDigestEndpoints:
    def test_digest_preview_and_deliver(self, client, auth_headers):
        # preview compiles (green/building with no data → no safety alert, but 200)
        r = client.get("/api/v1/whoop/digest", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert "items" in r.json() and "delivery" in r.json()
        # deliver runs the cooldown path + returns delivered flag
        r = client.post("/api/v1/whoop/digest/deliver", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert "delivered" in r.json()
        # prevention log is listable
        r = client.get("/api/v1/whoop/prevention-log", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
