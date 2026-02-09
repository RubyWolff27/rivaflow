"""Tests for WHOOP-related suggestion rules."""

from rivaflow.core.rules import RULES, format_explanation


class TestWhoopRules:
    """Test the three WHOOP-specific suggestion rules."""

    def _get_rule(self, name: str):
        for rule in RULES:
            if rule.name == name:
                return rule
        raise ValueError(f"Rule '{name}' not found")

    # --- whoop_low_recovery ---

    def test_whoop_low_recovery_fires(self):
        rule = self._get_rule("whoop_low_recovery")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
            "whoop_recovery_score": 25,
        }
        session_ctx = {}
        assert rule.condition(readiness, session_ctx) is True

    def test_whoop_low_recovery_skipped_high_score(self):
        rule = self._get_rule("whoop_low_recovery")
        readiness = {
            "sleep": 4,
            "stress": 2,
            "soreness": 1,
            "energy": 4,
            "whoop_recovery_score": 70,
        }
        assert rule.condition(readiness, {}) is False

    def test_whoop_low_recovery_skipped_no_whoop_data(self):
        rule = self._get_rule("whoop_low_recovery")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        # No whoop_recovery_score in readiness
        assert rule.condition(readiness, {}) is False

    def test_whoop_low_recovery_skipped_null_readiness(self):
        rule = self._get_rule("whoop_low_recovery")
        # Lambda returns None (falsy) when r is None — just check falsy
        assert not rule.condition(None, {})

    # --- whoop_hrv_drop ---

    def test_whoop_hrv_drop_fires(self):
        """hrv_drop_pct lives in session_context, not readiness."""
        rule = self._get_rule("whoop_hrv_drop")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        session_ctx = {"hrv_drop_pct": 33}  # 33% drop, >20% threshold
        assert rule.condition(readiness, session_ctx) is True

    def test_whoop_hrv_drop_skipped_normal(self):
        rule = self._get_rule("whoop_hrv_drop")
        readiness = {
            "sleep": 4,
            "stress": 2,
            "soreness": 1,
            "energy": 4,
        }
        session_ctx = {"hrv_drop_pct": 5}  # Only 5% drop
        assert rule.condition(readiness, session_ctx) is False

    def test_whoop_hrv_drop_skipped_no_hrv(self):
        rule = self._get_rule("whoop_hrv_drop")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        assert rule.condition(readiness, {}) is False

    # --- whoop_green_recovery ---

    def test_whoop_green_recovery_fires(self):
        rule = self._get_rule("whoop_green_recovery")
        readiness = {
            "sleep": 5,
            "stress": 1,
            "soreness": 1,
            "energy": 5,
            "whoop_recovery_score": 95,
        }
        assert rule.condition(readiness, {}) is True

    def test_whoop_green_recovery_skipped_below_90(self):
        rule = self._get_rule("whoop_green_recovery")
        readiness = {
            "sleep": 4,
            "stress": 2,
            "soreness": 1,
            "energy": 4,
            "whoop_recovery_score": 85,
        }
        assert rule.condition(readiness, {}) is False

    def test_whoop_green_recovery_skipped_no_whoop(self):
        rule = self._get_rule("whoop_green_recovery")
        readiness = {
            "sleep": 5,
            "stress": 1,
            "soreness": 1,
            "energy": 5,
        }
        assert rule.condition(readiness, {}) is False

    # --- format_explanation ---

    def test_format_explanation_with_whoop_fields(self):
        readiness = {
            "sleep": 3,
            "stress": 4,
            "soreness": 2,
            "energy": 3,
            "composite_score": 14,
            "whoop_recovery_score": 28,
        }
        session_ctx = {}
        explanation = "WHOOP recovery score is {whoop_recovery}%"
        result = format_explanation(explanation, readiness, session_ctx)
        assert "28" in result

    def test_format_explanation_without_whoop_fields(self):
        readiness = {
            "sleep": 3,
            "stress": 4,
            "soreness": 2,
            "energy": 3,
            "composite_score": 14,
        }
        session_ctx = {}
        explanation = "High stress ({stress}/5)"
        result = format_explanation(explanation, readiness, session_ctx)
        assert "4" in result

    # --- whoop_hrv_sustained_decline ---

    def test_whoop_hrv_sustained_decline_fires(self):
        rule = self._get_rule("whoop_hrv_sustained_decline")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        session_ctx = {"hrv_slope_5d": -0.8}
        assert rule.condition(readiness, session_ctx) is True

    def test_whoop_hrv_sustained_decline_skipped(self):
        rule = self._get_rule("whoop_hrv_sustained_decline")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        session_ctx = {"hrv_slope_5d": 0.2}  # Improving, not declining
        assert rule.condition(readiness, session_ctx) is False

    def test_whoop_hrv_sustained_decline_no_data(self):
        rule = self._get_rule("whoop_hrv_sustained_decline")
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
        }
        session_ctx = {}  # No hrv_slope_5d
        assert rule.condition(readiness, session_ctx) is False

    def test_format_explanation_hrv_slope(self):
        readiness = {
            "sleep": 3,
            "stress": 3,
            "soreness": 2,
            "energy": 3,
            "composite_score": 14,
        }
        session_ctx = {"hrv_slope_5d": -0.75}
        explanation = "HRV slope over last 5+ days is {hrv_slope_5d}"
        result = format_explanation(explanation, readiness, session_ctx)
        assert "-0.75" in result
