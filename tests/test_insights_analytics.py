"""Tests for InsightsAnalyticsService — edge cases and math helpers."""

import pytest

from rivaflow.core.services.insights_analytics import (
    InsightsAnalyticsService,
    _ewma,
    _linear_slope,
    _pearson_r,
    _shannon_entropy,
)

# ── Math helpers ──


class TestPearsonR:
    def test_empty_lists(self):
        assert _pearson_r([], []) == 0.0

    def test_insufficient_data(self):
        assert _pearson_r([1.0, 2.0], [3.0, 4.0]) == 0.0

    def test_perfect_positive(self):
        r = _pearson_r([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
        assert r == 1.0

    def test_perfect_negative(self):
        r = _pearson_r([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0])
        assert r == -1.0

    def test_no_correlation(self):
        r = _pearson_r([1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 1.0, 3.0])
        assert -0.5 < r < 0.5

    def test_constant_values(self):
        """Constant values should return 0 (no variance)."""
        r = _pearson_r([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
        assert r == 0.0

    def test_mismatched_lengths(self):
        assert _pearson_r([1.0, 2.0, 3.0], [1.0, 2.0]) == 0.0


class TestEWMA:
    def test_empty(self):
        assert _ewma([], 7) == []

    def test_single_value(self):
        assert _ewma([10.0], 7) == [10.0]

    def test_constant_values(self):
        result = _ewma([5.0, 5.0, 5.0, 5.0], 7)
        assert all(v == 5.0 for v in result)

    def test_increasing_values(self):
        result = _ewma([0.0, 10.0, 20.0, 30.0], 3)
        assert len(result) == 4
        assert result[0] == 0.0
        # Each subsequent value should be between current and previous EWMA
        for i in range(1, len(result)):
            assert result[i] >= result[i - 1]

    def test_span_affects_smoothing(self):
        values = [0.0, 100.0, 0.0, 100.0, 0.0]
        short_span = _ewma(values, 2)
        long_span = _ewma(values, 10)
        # Long span should be smoother (less variation)
        short_var = max(short_span) - min(short_span)
        long_var = max(long_span) - min(long_span)
        assert long_var < short_var


class TestShannonEntropy:
    def test_empty(self):
        assert _shannon_entropy([]) == 0.0

    def test_single_item(self):
        assert _shannon_entropy([5]) == 0.0

    def test_uniform_distribution(self):
        """Equal distribution should yield max entropy (100)."""
        result = _shannon_entropy([10, 10, 10, 10])
        assert result == 100.0

    def test_concentrated(self):
        """One dominant item should yield low entropy."""
        result = _shannon_entropy([100, 1, 1, 1])
        assert result < 50.0

    def test_zeros_filtered(self):
        """Zeros should not contribute."""
        result = _shannon_entropy([10, 0, 0, 10])
        assert result == 100.0  # Only 2 non-zero, equal


class TestLinearSlope:
    def test_empty(self):
        assert _linear_slope([]) == 0.0

    def test_single_value(self):
        assert _linear_slope([5.0]) == 0.0

    def test_increasing(self):
        slope = _linear_slope([1.0, 2.0, 3.0, 4.0])
        assert slope == pytest.approx(1.0, abs=0.01)

    def test_decreasing(self):
        slope = _linear_slope([4.0, 3.0, 2.0, 1.0])
        assert slope == pytest.approx(-1.0, abs=0.01)

    def test_flat(self):
        slope = _linear_slope([5.0, 5.0, 5.0])
        assert slope == 0.0


# ── Service edge cases (no DB) ──
# These tests verify graceful handling when the service encounters
# empty data. They require DB access so we mark them to skip if
# the database is not available.


@pytest.fixture
def insights_service():
    """Create an InsightsAnalyticsService instance."""
    return InsightsAnalyticsService()


class TestInsightsServiceEdgeCases:
    """Test that service methods handle empty/edge-case data gracefully."""

    # Use a user_id that definitely doesn't exist in the local DB.
    GHOST_USER = 2147483647

    def test_readiness_correlation_no_data(self, insights_service):
        """Should return empty scatter and r=0 for non-existent user."""
        result = insights_service.get_readiness_performance_correlation(
            user_id=self.GHOST_USER
        )
        assert result["r_value"] == 0.0
        assert result["scatter"] == []
        assert result["data_points"] == 0

    def test_training_load_no_sessions(self, insights_service):
        """Should return 0 ACWR for user with no sessions."""
        result = insights_service.get_training_load_management(
            user_id=self.GHOST_USER, days=30
        )
        assert result["current_acwr"] == 0.0
        assert result["current_zone"] == "undertrained"

    def test_technique_effectiveness_no_data(self, insights_service):
        """Should return empty list for user with no technique data."""
        result = insights_service.get_technique_effectiveness(user_id=self.GHOST_USER)
        assert result["techniques"] == []
        assert result["game_breadth"] == 0

    def test_session_quality_no_sessions(self, insights_service):
        """Should return 0 avg quality with no sessions."""
        result = insights_service.get_session_quality_scores(user_id=self.GHOST_USER)
        assert result["sessions"] == []
        assert result["avg_quality"] == 0

    def test_overtraining_risk_no_data(self, insights_service):
        """Should return low risk for user with no data."""
        result = insights_service.get_overtraining_risk(user_id=self.GHOST_USER)
        assert result["risk_score"] == 0
        assert result["level"] == "green"

    def test_recovery_no_data(self, insights_service):
        """Should handle no readiness/session data gracefully."""
        result = insights_service.get_recovery_insights(
            user_id=self.GHOST_USER, days=30
        )
        assert result["sleep_correlation"] == 0.0
        assert result["optimal_rest_days"] == 0

    def test_partner_progression_not_found(self, insights_service):
        """Should handle non-existent partner gracefully."""
        result = insights_service.get_partner_progression(
            user_id=self.GHOST_USER, partner_id=self.GHOST_USER
        )
        assert result["trend"] == "unknown"
        assert result["partner"] is None

    def test_insights_summary_no_data(self, insights_service):
        """Should return summary even with no data."""
        result = insights_service.get_insights_summary(user_id=self.GHOST_USER)
        assert "acwr" in result
        assert "risk_score" in result
        assert "game_breadth" in result
