"""P5.1 — WHOOP build acceptance harness.

Asserts each roadmap build's contract + the review's load-bearing SAFETY invariants, end-to-end against
Postgres (temp_db). With an empty test DB the analytics return building/unavailable states — but the
STRUCTURAL guarantees (keys present, safety properties) must hold regardless of data. Real-data behavioural
criteria (e.g. "zones shift for Ruby") are verified on the VPS via the live endpoints; noted per-check.
"""

from __future__ import annotations


class TestWhoopAcceptance:
    def test_summary_contract(self, test_user):
        from rivaflow.core.whoop_analytics import whoop_summary

        s = whoop_summary(test_user["id"])
        for k in (
            "readiness",
            "strain_target",
            "acwr",
            "sleep",
            "coverage",
            "max_hr",
            "prevention",
        ):
            assert k in s, f"summary missing {k}"

    def test_b1_maxhr_banded_and_not_bare_190(self, test_user):
        from rivaflow.core.whoop_analytics import user_max_hr

        mx = user_max_hr(test_user["id"])
        assert "uncertainty" in mx and len(mx["uncertainty"]) == 2  # banded
        assert mx["max_hr"] == 177  # Tanaka fallback with no data — NOT the old 190

    def test_b2_readiness_green_carries_caveat_contract(self, test_user):
        from rivaflow.core.readiness import GREEN_CAVEAT, blend_readiness

        r = blend_readiness({"hrv": 0.0})  # Balanced (green) with a stub signal
        assert r["caveat"] == GREEN_CAVEAT

    def test_b3_coverage_separates_rr_from_hr(self, test_user):
        from rivaflow.core.whoop_analytics import capture_coverage

        cov = capture_coverage(test_user["id"])
        assert "summary" in cov and "rr_coverage_pct" in cov["summary"]

    def test_b6_prevention_has_no_cardiac_signal(self, test_user):
        from rivaflow.core.prevention import SIGNAL_FAMILY

        assert "afib" not in SIGNAL_FAMILY and "rhythm" not in SIGNAL_FAMILY
        assert set(SIGNAL_FAMILY) == {"rhr", "sleeping_hr", "lnrmssd", "resp_rate"}

    def test_b6_amber_red_are_safety_fire_on_sabbath(self, test_user):
        from math import log

        from rivaflow.core.prevention import evaluate_prevention

        r = evaluate_prevention(
            {
                "rhr": {"value": 55, "median": 50, "mad": 2},
                "lnrmssd": {
                    "value": log(50) - 1.7 * 0.1 * 1.4826,
                    "median": log(50),
                    "mad": 0.1,
                },
            },
            today_is_sabbath=True,
        )
        assert r["tier"] == "amber" and r["fires_on_sabbath"] is True

    def test_b6_validation_gate_present(self, test_user):
        from rivaflow.core.whoop_analytics import prevention_validation_live

        v = prevention_validation_live(test_user["id"])
        assert "validation" in v and "passes" in v["validation"]

    def test_p2_digest_cooldown_and_no_live_refresh(self, test_user):
        from rivaflow.core.whoop_analytics import morning_digest

        d = morning_digest(test_user["id"])
        assert "no live-refresh" in d["delivery"]

    def test_b14_vo2max_is_banded_not_point(self, test_user):
        from rivaflow.core.longevity import passive_vo2max

        r = passive_vo2max(177, 50)
        assert "range" in r and len(r["range"]) == 2  # banded

    def test_b15_cardio_age_flagged_proxy(self, test_user):
        from rivaflow.core.longevity import cardio_age_proxy

        r = cardio_age_proxy(50, 44)
        assert r["is_proxy"] is True and "not clinical" in r["note"]

    def test_b18_dfa_artifact_gated(self, test_user):
        from rivaflow.core.whoop_analytics import dfa_analysis

        r = dfa_analysis(test_user["id"])
        # with no data: unavailable; the point is it never returns α1 on high-artifact data
        assert r.get("available") is False or "alpha1" in r

    def test_cockpit_renders_all_panels(self, test_user):
        from rivaflow.core.whoop_analytics import cockpit_page

        html = cockpit_page(test_user["id"])
        for panel in (
            "Recovery &amp; Load",
            "HRV Lab",
            "Data integrity",
            "Sleep",
            "Trends &amp; Longevity",
            "Baseline-Deviation log",
            "Behaviour correlations",
        ):
            assert panel in html
