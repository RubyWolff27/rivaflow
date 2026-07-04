"""P4a — whoop_summary exposes the prevention field the slim-app banner reads (Postgres via temp_db)."""

from __future__ import annotations


class TestSummaryPrevention:
    def test_summary_includes_prevention(self, test_user):
        from rivaflow.core.whoop_analytics import whoop_summary

        s = whoop_summary(test_user["id"])
        assert "prevention" in s
        # with no data it's a building/unavailable dict, but the key must exist for the phone.
        assert isinstance(s["prevention"], dict)
        # and the other slim-app fields remain present
        for k in ("readiness", "strain_target", "coverage", "max_hr"):
            assert k in s
