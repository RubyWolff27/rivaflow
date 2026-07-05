"""Perf — the cockpit is served from a pre-computed snapshot, not rendered live per request.

`cockpit_page` reads the stored snapshot (instant SELECT) when one exists, and only falls back to a live
render (storing it) on the cold first-ever hit. `_build_cockpit_page` remains the pure full-page renderer
the scheduler calls. Uses the Postgres test_user/temp_db fixtures.
"""

from __future__ import annotations


class TestCockpitSnapshot:
    def test_build_returns_full_page(self, test_user):
        from rivaflow.core.whoop_analytics import _build_cockpit_page

        html = _build_cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")
        assert "WHOOP Cockpit" in html
        assert "recomputes every 4h" in html  # freshness stamp footer

    def test_cockpit_page_serves_stored_snapshot(self, test_user):
        """When a snapshot exists, cockpit_page returns it verbatim — no live re-render."""
        from rivaflow.core.whoop_analytics import cockpit_page
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        marker = "<!doctype html><html><head></head><body>STORED-SNAPSHOT-MARKER</body></html>"
        WhoopRepository.upsert_cockpit_snapshot(test_user["id"], marker)

        assert cockpit_page(test_user["id"]) == marker

    def test_cockpit_page_falls_back_and_stores_when_absent(self, test_user):
        """With no snapshot, cockpit_page renders live, persists it, and subsequent reads hit the store."""
        from rivaflow.core.whoop_analytics import cockpit_page
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        assert WhoopRepository.get_cockpit_snapshot(test_user["id"]) is None

        html = cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")

        snap = WhoopRepository.get_cockpit_snapshot(test_user["id"])
        assert snap is not None
        assert snap["html"] == html
        assert snap["rendered_at"] is not None

    def test_upsert_replaces_existing_snapshot(self, test_user):
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        WhoopRepository.upsert_cockpit_snapshot(test_user["id"], "<p>first</p>")
        WhoopRepository.upsert_cockpit_snapshot(test_user["id"], "<p>second</p>")

        snap = WhoopRepository.get_cockpit_snapshot(test_user["id"])
        assert snap is not None
        assert snap["html"] == "<p>second</p>"

    def test_get_snapshot_none_for_fresh_user(self, test_user):
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        assert WhoopRepository.get_cockpit_snapshot(test_user["id"]) is None
