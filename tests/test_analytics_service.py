"""Unit tests for AnalyticsService — facade delegating to sub-services."""

from datetime import date
from unittest.mock import patch

from rivaflow.core.services.analytics_service import AnalyticsService


def _build_service():
    """Build an AnalyticsService with all sub-services mocked."""
    with (
        patch(
            "rivaflow.core.services.analytics_service.PerformanceAnalyticsService"
        ) as MockPerf,
        patch(
            "rivaflow.core.services.analytics_service.ReadinessAnalyticsService"
        ) as MockRead,
        patch(
            "rivaflow.core.services.analytics_service.TechniqueAnalyticsService"
        ) as MockTech,
        patch(
            "rivaflow.core.services.analytics_service.StreakAnalyticsService"
        ) as MockStreak,
        patch(
            "rivaflow.core.services.analytics_service.InsightsAnalyticsService"
        ) as MockInsights,
    ):
        service = AnalyticsService()
        return (
            service,
            MockPerf.return_value,
            MockRead.return_value,
            MockTech.return_value,
            MockStreak.return_value,
            MockInsights.return_value,
        )


class TestPerformanceDelegation:
    """Tests for performance analytics delegation."""

    def test_get_performance_overview(self):
        """Should delegate to PerformanceAnalyticsService."""
        service, mock_perf, *_ = _build_service()
        mock_perf.get_performance_overview.return_value = {"summary": {}}

        result = service.get_performance_overview(
            user_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )

        assert result == {"summary": {}}
        mock_perf.get_performance_overview.assert_called_once_with(
            1, date(2025, 1, 1), date(2025, 3, 31), None
        )

    def test_get_partner_analytics(self):
        """Should delegate partner analytics to performance service."""
        service, mock_perf, *_ = _build_service()
        mock_perf.get_partner_analytics.return_value = {"partner_matrix": []}

        result = service.get_partner_analytics(user_id=1)

        assert result == {"partner_matrix": []}
        mock_perf.get_partner_analytics.assert_called_once()

    def test_get_head_to_head(self):
        """Should delegate head-to-head to performance service."""
        service, mock_perf, *_ = _build_service()
        mock_perf.get_head_to_head.return_value = {"partner1": {}, "partner2": {}}

        result = service.get_head_to_head(user_id=1, partner1_id=2, partner2_id=3)

        assert "partner1" in result
        mock_perf.get_head_to_head.assert_called_once_with(1, 2, 3)

    def test_get_instructor_analytics(self):
        """Should delegate instructor analytics to performance service."""
        service, mock_perf, *_ = _build_service()
        mock_perf.get_instructor_analytics.return_value = {"instructors": []}

        result = service.get_instructor_analytics(user_id=1)

        assert result == {"instructors": []}


class TestReadinessDelegation:
    """Tests for readiness analytics delegation."""

    def test_get_readiness_trends(self):
        """Should delegate to ReadinessAnalyticsService."""
        service, _, mock_read, *_ = _build_service()
        mock_read.get_readiness_trends.return_value = {"trends": []}

        result = service.get_readiness_trends(user_id=1)

        assert result == {"trends": []}
        mock_read.get_readiness_trends.assert_called_once()

    def test_get_whoop_analytics(self):
        """Should delegate WHOOP analytics to readiness service."""
        service, _, mock_read, *_ = _build_service()
        mock_read.get_whoop_analytics.return_value = {"strain": []}

        result = service.get_whoop_analytics(user_id=1)

        assert result == {"strain": []}

    def test_get_weight_trend(self):
        """Should delegate weight trend to readiness service."""
        service, _, mock_read, *_ = _build_service()
        mock_read.get_weight_trend.return_value = {"data": []}

        result = service.get_weight_trend(user_id=1)

        assert result == {"data": []}
        mock_read.get_weight_trend.assert_called_once_with(1, None, None)


class TestTechniqueDelegation:
    """Tests for technique analytics delegation."""

    def test_get_technique_analytics(self):
        """Should delegate to TechniqueAnalyticsService."""
        service, _, _, mock_tech, *_ = _build_service()
        mock_tech.get_technique_analytics.return_value = {"techniques": []}

        result = service.get_technique_analytics(user_id=1)

        assert result == {"techniques": []}
        mock_tech.get_technique_analytics.assert_called_once()


class TestStreakDelegation:
    """Tests for streak analytics delegation."""

    def test_get_consistency_analytics(self):
        """Should delegate to StreakAnalyticsService."""
        service, _, _, _, mock_streak, _ = _build_service()
        mock_streak.get_consistency_analytics.return_value = {"streaks": {}}

        result = service.get_consistency_analytics(user_id=1)

        assert result == {"streaks": {}}
        mock_streak.get_consistency_analytics.assert_called_once()

    def test_get_milestones(self):
        """Should delegate milestones to streak service."""
        service, _, _, _, mock_streak, _ = _build_service()
        mock_streak.get_milestones.return_value = {"belt_progression": []}

        result = service.get_milestones(user_id=1)

        assert result == {"belt_progression": []}
        mock_streak.get_milestones.assert_called_once_with(1)

    def test_get_training_frequency_heatmap(self):
        """Should delegate heatmap to streak service."""
        service, _, _, _, mock_streak, _ = _build_service()
        mock_streak.get_training_frequency_heatmap.return_value = {"calendar": []}

        result = service.get_training_frequency_heatmap(user_id=1)

        assert result == {"calendar": []}


class TestInsightsDelegation:
    """Tests for insights analytics delegation."""

    def test_get_insights_summary(self):
        """Should delegate to InsightsAnalyticsService."""
        service, _, _, _, _, mock_insights = _build_service()
        mock_insights.get_insights_summary.return_value = {"score": 8.5}

        result = service.get_insights_summary(user_id=1)

        assert result == {"score": 8.5}
        mock_insights.get_insights_summary.assert_called_once_with(1)

    def test_get_overtraining_risk(self):
        """Should delegate overtraining risk to insights service."""
        service, _, _, _, _, mock_insights = _build_service()
        mock_insights.get_overtraining_risk.return_value = {"risk": "low"}

        result = service.get_overtraining_risk(user_id=1)

        assert result == {"risk": "low"}

    def test_get_checkin_trends(self):
        """Should delegate checkin trends to insights service."""
        service, _, _, _, _, mock_insights = _build_service()
        mock_insights.get_checkin_trends.return_value = {"energy": []}

        result = service.get_checkin_trends(user_id=1, days=30)

        assert result == {"energy": []}
        mock_insights.get_checkin_trends.assert_called_once_with(1, 30)
