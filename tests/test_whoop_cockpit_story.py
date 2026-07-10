"""P6 "Story over Lab" — the glanceable Tier-1 band, the Workouts drill-down, per-panel takeaways, and the
collapsed Tier-2 Lab. Pure render helpers run without a DB; the end-to-end assembly uses the Postgres
test_user/temp_db fixtures and must stay graceful on a fresh (dataless) user.
"""

from __future__ import annotations


class TestStoryHelpers:
    def test_classify_hardness_labels(self):
        """Zone-weight load math now lives in one place (rivaflow.core.cardio_load, Wave 3.2) — the
        renderer no longer derives its own hardness label from hr_zone_secs. classify_hardness() takes a
        raw Banister TRIMP load + cutoffs (hardness_cutoffs([]) is the <8-samples fallback band).
        """
        from rivaflow.core.cardio_load import classify_hardness, hardness_cutoffs

        cutoffs = hardness_cutoffs(
            []
        )  # fallback cutoffs (fewer than 8 recent sessions)
        assert (
            classify_hardness(300.0, cutoffs) == "HARD"
        )  # heavy session, well above HARD_CUTOFF
        assert classify_hardness(0.0, cutoffs) == "EASY"  # no load at all
        assert (
            classify_hardness(100.0, cutoffs) == "MODERATE"
        )  # between the two cutoffs

    def test_inject_takeaway_slots_under_heading(self):
        from rivaflow.core.whoop_cockpit import inject_takeaway

        panel = '<section class="panel"><h2>X</h2><div>body</div></section>'
        out = inject_takeaway(panel, "plain english")
        assert (
            '<h2>X</h2><div class="takeaway">plain english</div><div>body</div>' in out
        )
        assert inject_takeaway(panel, "") == panel  # empty text is a no-op

    def test_inject_takeaway_escapes(self):
        from rivaflow.core.whoop_cockpit import inject_takeaway

        out = inject_takeaway("<h2>X</h2>", "<script>")
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_lab_section_is_collapsed_details(self):
        from rivaflow.core.whoop_cockpit import render_lab_section

        out = render_lab_section('<section class="panel"><h2>P</h2></section>')
        assert out.startswith('<details class="lab">')
        assert "<summary>" in out and "Show the full lab" in out


class TestTodayStory:
    def _ready(self):
        return {
            "state": "Strained",
            "headline": "Below baseline — technical over hard rolls today.",
            "caveat": None,
        }

    def test_story_populated_has_hero_narrative_and_three_cards(self):
        from rivaflow.core.whoop_cockpit import render_today_story

        night = {"available": True, "duration_hours": 6.0, "avg_sleeping_hr": 52}
        dip = {"available": True, "onset": "23:10", "offset": "05:40", "dip_pct": 18.5}
        last = {
            "label": "BJJ (gi)",
            "day": "2026-07-04",
            "analytics": {
                "available": True,
                "avg_hr": 150,
                "max_hr": 182,
                "duration_sec": 3600,
                "hr_zone_secs": {3: 600, 4: 1800, 5: 1200},
                "times": [0, 1, 2],
                "values": [140, 160, 150],
                "hrr": 20,
                # Load/hardness are computed once in whoop_analytics.session_deepdives (Wave 3.2) and
                # carried in the analytics dict — the renderer only displays them now, it doesn't
                # re-derive from hr_zone_secs.
                "raw_load": 242.6,
                "load": 15.9,
                "hardness": "HARD",
            },
        }
        strain = {"available": True, "target_load": 9.0, "chronic_load": 11.0}
        out = render_today_story(
            self._ready(),
            "HRV below baseline, but you slept 3.0h under your 9h need — ease into today.",
            night,
            dip,
            9,
            last,
            strain,
            is_sabbath=False,
        )
        assert 'class="panel hero"' in out
        assert '<div class="narrative">' in out
        assert "Strained" in out
        assert "6.0h" in out and "23:10" in out  # last-night card
        assert "HARD" in out  # last-workout hardness badge
        assert '<details class="card">' in out  # last-workout expands inline
        assert "9.0/21" in out  # today's guidance target

    def test_story_empty_state_is_clean(self):
        from rivaflow.core.whoop_cockpit import render_today_story

        out = render_today_story(
            {"state": "Building", "headline": "Building your HRV baseline"},
            "Still building your baseline.",
            {"available": False},
            {"available": False},
            9,
            None,
            {"available": False, "reason": "building your baseline"},
            is_sabbath=False,
        )
        assert 'class="panel hero"' in out
        assert "Building" in out
        assert "no recent session captured" in out  # last-workout empty card

    def test_story_sabbath_shows_rest_not_push(self):
        from rivaflow.core.whoop_cockpit import render_today_story

        out = render_today_story(
            self._ready(),
            "Sabbath — rest is prescribed today.",
            {"available": False},
            {"available": False},
            9,
            None,
            {"available": False, "reason": "Sabbath — rest is prescribed."},
            is_sabbath=True,
        )
        assert "Sabbath" in out and "Rest" in out


class TestWorkoutsList:
    def test_empty_state(self):
        from rivaflow.core.whoop_cockpit import render_workouts_list

        out = render_workouts_list([])
        assert "<h2>Workouts</h2>" in out
        assert "No recent sessions" in out

    def test_rows_are_expandable_details(self):
        from rivaflow.core.whoop_cockpit import render_workouts_list

        sessions = [
            {
                "label": "BJJ (gi)",
                "day": "2026-07-04",
                "analytics": {
                    "available": True,
                    "avg_hr": 150,
                    "max_hr": 182,
                    "duration_sec": 3600,
                    "hr_zone_secs": {4: 1800, 5: 1200},
                    "times": [0, 1, 2],
                    "values": [140, 160, 150],
                    "hrr": 20,
                    "raw_load": 242.6,
                    "load": 15.9,
                    "hardness": "HARD",
                },
            },
            {
                "label": "CrossFit",
                "day": "2026-07-02",
                "analytics": {"available": False, "reason": "no HR"},
            },
        ]
        out = render_workouts_list(sessions)
        assert out.count('<details class="workout-row">') == 2
        assert "BJJ (gi)" in out and "CrossFit" in out
        assert "load" in out  # hardness/load in the summary row


class TestNarrative:
    """daily_narrative composes an honest, non-overclaiming line and silences the push on the Sabbath."""

    def test_strained_with_hard_workout_and_short_sleep(self):
        import datetime as dt
        from unittest import mock

        import rivaflow.core.whoop_analytics as wa

        with mock.patch.object(wa, "datetime") as m:
            m.now.return_value = dt.datetime(2026, 7, 6, 8, 0)  # Monday — not Sabbath
            out = wa.daily_narrative(
                1,
                readiness={"state": "Strained"},
                night={"available": True, "duration_hours": 6.0},
                last_workout={
                    "label": "BJJ (gi)",
                    "analytics": {
                        "available": True,
                        "hr_zone_secs": {4: 1800, 5: 1200},
                        "raw_load": 242.6,
                        "load": 15.9,
                        "hardness": "HARD",
                    },
                },
            )
        assert "below your baseline" in out
        assert "hard bjj (gi)" in out
        assert "3.0h under your 9h need" in out
        assert "ease into today" in out

    def test_building_returns_clean_line(self):
        import datetime as dt
        from unittest import mock

        import rivaflow.core.whoop_analytics as wa

        with mock.patch.object(wa, "datetime") as m:
            m.now.return_value = dt.datetime(2026, 7, 6, 8, 0)
            out = wa.daily_narrative(
                1,
                readiness={"state": "Building"},
                night={"available": False},
                last_workout=None,
            )
        assert "building your hrv baseline" in out.lower()

    def test_sabbath_silences_performance_nudge(self):
        import datetime as dt
        from unittest import mock

        import rivaflow.core.whoop_analytics as wa

        with mock.patch.object(wa, "datetime") as m:
            m.now.return_value = dt.datetime(2026, 7, 5, 8, 0)  # Sunday — Sabbath
            out = wa.daily_narrative(
                1,
                readiness={"state": "Strained"},
                night={"available": True, "duration_hours": 6.0},
                last_workout=None,
            )
        assert out.startswith("Sabbath — rest is prescribed")
        assert "ease into today" not in out and "green light" not in out


class TestEndToEndFreshUser:
    def test_build_cockpit_page_renders_story_and_lab_on_dataless_user(self, test_user):
        from rivaflow.core.whoop_analytics import _build_cockpit_page

        html = _build_cockpit_page(test_user["id"])
        assert html.startswith("<!doctype html>")
        # Tier-1 present
        assert 'class="panel hero"' in html
        assert '<div class="narrative">' in html
        assert "<h2>Workouts</h2>" in html
        # Tier-2 lab collapsed + still carries all 15 panels + takeaways
        assert 'class="lab"' in html and "Show the full lab" in html
        assert '<div class="takeaway">' in html
        for panel in (
            "Recovery &amp; Load",
            "HRV Lab",
            "Data integrity",
            "Session deep-dives",
            "Baseline-Deviation log",
            "Behaviour correlations",
        ):
            assert panel in html, f"missing lab panel: {panel}"

    def test_daily_narrative_standalone_on_fresh_user(self, test_user):
        from rivaflow.core.whoop_analytics import daily_narrative

        out = daily_narrative(test_user["id"])
        assert isinstance(out, str) and out.strip()
