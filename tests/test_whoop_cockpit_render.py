"""P3 — full cockpit renders end-to-end against Postgres (temp_db)."""

from __future__ import annotations


class TestCockpitRender:
    def test_cockpit_page_renders_all_panels(self, test_user):
        from rivaflow.core.whoop_analytics import cockpit_page

        html = cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")
        assert "WHOOP Cockpit" in html
        for panel in (
            "Recovery &amp; Load",  # P3.1
            "Today · HR ribbon",  # P3.5
            "RR &amp; HRV detail",  # P3.5 MUST-HAVE
            "HRV Lab",  # P3.2
            "Overnight HRV curve",  # P3.5
            "Data integrity",  # P3.2
            "Sleep HR &amp; nocturnal dip",  # P3.5
            "Respiratory trace",  # P3.5
            "Stress ribbon",  # P3.5
            "Sleep",  # P3.3
            "Trends &amp; Longevity",  # P3.3
            "Session deep-dives",  # P3.5 MUST-HAVE
            "Baseline-Deviation log",  # P3.4
            "Behaviour correlations",  # P3.4
        ):
            assert panel in html, f"missing panel: {panel}"

    def test_cockpit_endpoint_requires_key(self, client):
        r = client.get("/api/v1/whoop/cockpit", params={"key": "not-a-key"})
        assert r.status_code == 401
