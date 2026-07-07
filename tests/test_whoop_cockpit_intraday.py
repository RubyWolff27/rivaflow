"""P3.5 — intraday/session deep-dive panels: HR ribbon, RR+Poincaré, overnight HRV, sleep HR dip,
respiratory trace, stress ribbon, session deep-dives, and the cold-start progress rings.

Render functions are pure (HTML in, HTML out) so most cases run without Postgres. The data-series
functions (today_hr_ribbon, rr_hrv_detail, ...) need Postgres (temp_db/test_user) — on a fresh user with
no WHOOP rows they must degrade to a clean "building" state, never raise.
"""

from __future__ import annotations


class TestSvgHelpers:
    def test_progress_ring_renders_svg_with_fraction(self):
        from rivaflow.core.whoop_cockpit import svg_progress_ring

        out = svg_progress_ring(3, 14, "Sleep debt")
        assert out.startswith("<svg")
        assert "3/14" in out

    def test_area_line_empty_data_does_not_crash(self):
        from rivaflow.core.whoop_cockpit import svg_area_line

        out = svg_area_line([], [])
        assert out.startswith("<svg")
        assert "no data" in out

    def test_area_line_with_bands(self):
        from rivaflow.core.whoop_cockpit import svg_area_line

        out = svg_area_line([0, 1, 2], [60, 90, 70], bands=[(60, 100, "#34d399")])
        assert "<polyline" in out
        assert "<rect" in out

    def test_poincare_empty_pairs_does_not_crash(self):
        from rivaflow.core.whoop_cockpit import svg_poincare

        out = svg_poincare([], 0.0, 0.0)
        assert out.startswith("<svg")

    def test_poincare_with_pairs_draws_ellipse(self):
        from rivaflow.core.whoop_cockpit import svg_poincare

        pairs = [(800.0 + i, 810.0 + i) for i in range(20)]
        out = svg_poincare(pairs, sd1=20.0, sd2=60.0)
        assert "<ellipse" in out
        assert "<circle" in out


class TestPanelRendersEmptyState:
    """Every new panel must render a clean 'building' state on empty/unavailable data — never crash."""

    def test_hr_ribbon_empty(self):
        from rivaflow.core.whoop_cockpit import render_hr_ribbon

        out = render_hr_ribbon({"available": False, "reason": "no HR yet"})
        assert '<section class="panel">' in out
        assert "Today · HR ribbon" in out
        assert "no HR yet" in out

    def test_rr_hrv_detail_empty(self):
        from rivaflow.core.whoop_cockpit import render_rr_hrv_detail

        out = render_rr_hrv_detail({"available": False, "reason": "not enough RR"})
        assert "RR &amp; HRV detail" in out

    def test_overnight_hrv_empty(self):
        from rivaflow.core.whoop_cockpit import render_overnight_hrv

        out = render_overnight_hrv({"available": False, "reason": "no window"})
        assert "Overnight HRV curve" in out

    def test_sleep_hr_dip_empty(self):
        from rivaflow.core.whoop_cockpit import render_sleep_hr_dip

        out = render_sleep_hr_dip({"available": False, "reason": "no window"})
        assert "Sleep HR &amp; nocturnal dip" in out

    def test_respiratory_empty(self):
        from rivaflow.core.whoop_cockpit import render_respiratory

        out = render_respiratory({"available": False, "reason": "no RR"})
        assert "Respiratory trace" in out

    def test_stress_ribbon_empty(self):
        from rivaflow.core.whoop_cockpit import render_stress_ribbon

        out = render_stress_ribbon({"available": False, "reason": "no baseline"})
        assert "Stress ribbon" in out

    def test_session_deepdives_empty_list(self):
        from rivaflow.core.whoop_cockpit import render_session_deepdives

        out = render_session_deepdives([])
        assert '<section class="panel">' in out
        assert "Session deep-dives" in out

    def test_session_deepdives_unavailable_session_does_not_crash(self):
        from rivaflow.core.whoop_cockpit import render_session_deepdives

        out = render_session_deepdives(
            [
                {
                    "label": "BJJ (gi)",
                    "day": "2026-07-01",
                    "analytics": {"available": False, "reason": "no HR"},
                }
            ]
        )
        assert "BJJ (gi)" in out


class TestPanelRendersPopulatedState:
    def test_hr_ribbon_populated(self):
        from rivaflow.core.whoop_cockpit import render_hr_ribbon

        out = render_hr_ribbon(
            {
                "available": True,
                # dense samples (gaps < max_gap=0.34h) so the connected polyline
                # renders; sparse points now honestly draw as dots (gap-honesty, #88)
                "times": [0, 0.1, 0.2],
                "values": [60, 90, 70],
                "avg_hr": 73,
                "max_bpm": 150,
                "max_hr": 190,
            }
        )
        assert "<svg" in out and "<polyline" in out

    def test_rr_hrv_detail_populated(self):
        from rivaflow.core.whoop_cockpit import render_rr_hrv_detail

        pairs = [(800.0 + i, 810.0 + i) for i in range(10)]
        out = render_rr_hrv_detail(
            {
                "available": True,
                "times": [0, 1, 2],
                "rr_values": [800, 820, 810],
                "pairs": pairs,
                "sd1": 22.0,
                "sd2": 55.0,
                "mean_hr": 68,
            }
        )
        assert "<ellipse" in out

    def test_session_deepdives_populated(self):
        from rivaflow.core.whoop_cockpit import render_session_deepdives

        sessions = [
            {
                "label": "BJJ (gi)",
                "day": "2026-07-01",
                "analytics": {
                    "available": True,
                    "avg_hr": 150,
                    "max_hr": 180,
                    "duration_sec": 3600,
                    "hr_zone_secs": {1: 100, 2: 200, 3: 1000, 4: 1800, 5: 500},
                    "times": [0, 1, 2],
                    "values": [140, 160, 150],
                    "hrr": 22,
                },
            }
        ]
        out = render_session_deepdives(sessions)
        assert "BJJ (gi)" in out
        # HRR renders as a stat card since the cockpit overhaul (#86)
        assert "22 bpm recovery in 60s" in out


class TestProgressWiring:
    """Existing longitudinal panels show a progress ring — not bare text — when cold-starting."""

    def test_recovery_load_shows_acwr_ring_when_not_available(self):
        from rivaflow.core.whoop_cockpit import render_recovery_load

        out = render_recovery_load(
            readiness={"state": "Building"},
            strain={"available": False},
            acwr={"available": False},
            cardio_trend=[],
            recovery_cost={"available": False},
            acwr_progress={"have": 5, "need": 28},
        )
        assert "5/28" in out

    def test_hrv_lab_shows_ring_when_not_available(self):
        from rivaflow.core.whoop_cockpit import render_hrv_lab

        out = render_hrv_lab(
            {"available": False, "reason": "no window"},
            {"available": False, "reason": "no segment"},
            progress={"have": 2, "need": 5},
        )
        assert "2/5" in out

    def test_sleep_shows_ring_when_debt_not_available(self):
        from rivaflow.core.whoop_cockpit import render_sleep

        out = render_sleep(
            {"debt": {"available": False}, "regularity": {"available": False}},
            debt_progress={"have": 4, "need": 14},
        )
        assert "4/14" in out

    def test_trends_shows_ring_when_resilience_not_available(self):
        from rivaflow.core.whoop_cockpit import render_trends

        out = render_trends(
            longevity={},
            resilience={"resilience": {"available": False}},
            circadian={},
            assessment={},
            resilience_progress={"have": 6, "need": 14},
        )
        assert "6/14" in out


class TestDataSeriesGracefulOnFreshUser:
    """No WHOOP rows at all for a brand-new user — every new series fn must degrade cleanly, never raise."""

    def test_today_hr_ribbon_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import today_hr_ribbon

        out = today_hr_ribbon(test_user["id"])
        assert out["available"] is False

    def test_rr_hrv_detail_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import rr_hrv_detail

        out = rr_hrv_detail(test_user["id"])
        assert out["available"] is False

    def test_overnight_hrv_curve_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import overnight_hrv_curve

        out = overnight_hrv_curve(test_user["id"])
        assert out["available"] is False

    def test_sleep_hr_dip_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import sleep_hr_dip

        out = sleep_hr_dip(test_user["id"])
        assert out["available"] is False

    def test_respiratory_trace_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import respiratory_trace

        out = respiratory_trace(test_user["id"])
        assert out["available"] is False

    def test_stress_ribbon_series_unavailable(self, test_user):
        from rivaflow.core.whoop_analytics import stress_ribbon_series

        out = stress_ribbon_series(test_user["id"])
        assert out["available"] is False

    def test_session_deepdives_empty(self, test_user):
        from rivaflow.core.whoop_analytics import session_deepdives

        assert session_deepdives(test_user["id"]) == []

    def test_history_progress_all_zero(self, test_user):
        from rivaflow.core.whoop_analytics import _history_progress

        progress = _history_progress(test_user["id"])
        assert progress["hrv"]["have"] == 0
        assert progress["acwr"]["have"] == 0
        assert progress["sleep_debt"]["have"] == 0
        assert progress["resilience"]["have"] == 0

    def test_cockpit_page_end_to_end_on_fresh_user(self, test_user):
        """Full assembly with zero data: every P3.5 panel present, no traceback."""
        from rivaflow.core.whoop_analytics import cockpit_page

        html = cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")
        for panel in (
            "Today · HR ribbon",
            "RR &amp; HRV detail",
            "Overnight HRV curve",
            "Sleep HR &amp; nocturnal dip",
            "Respiratory trace",
            "Stress ribbon",
            "Session deep-dives",
        ):
            assert panel in html, f"missing panel: {panel}"
