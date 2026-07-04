"""P3.1 — cockpit page renders end-to-end against Postgres (temp_db)."""

from __future__ import annotations


class TestCockpitRender:
    def test_cockpit_page_renders_html(self, test_user):
        from rivaflow.core.whoop_analytics import cockpit_page

        html = cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")
        assert "WHOOP Cockpit" in html
        assert "Recovery &amp; Load" in html  # P3.1 panel present
        assert "auto-refresh" in html

    def test_cockpit_endpoint_requires_key(self, client):
        r = client.get("/api/v1/whoop/cockpit", params={"key": "not-a-key"})
        assert r.status_code == 401
