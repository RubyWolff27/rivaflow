"""Analytics service facade - delegates to focused analytics services.

This facade maintains backward compatibility while organizing analytics logic
into focused services:
- PerformanceAnalyticsService: Performance metrics, partner/instructor stats
- ReadinessAnalyticsService: Readiness trends and WHOOP data
- TechniqueAnalyticsService: Technique tracking and mastery
- StreakAnalyticsService: Training consistency, streaks, and milestones
"""

from datetime import date
from typing import Any

from rivaflow.core.services.insights_analytics import InsightsAnalyticsService
from rivaflow.core.services.performance_analytics import PerformanceAnalyticsService
from rivaflow.core.services.readiness_analytics import ReadinessAnalyticsService
from rivaflow.core.services.streak_analytics import StreakAnalyticsService
from rivaflow.core.services.technique_analytics import TechniqueAnalyticsService


class AnalyticsService:
    """
    Facade for analytics services.

    Delegates to focused services while maintaining backward compatibility.
    """

    def __init__(self):
        self.performance = PerformanceAnalyticsService()
        self.readiness = ReadinessAnalyticsService()
        self.technique = TechniqueAnalyticsService()
        self.streak = StreakAnalyticsService()
        self.insights = InsightsAnalyticsService()

    # ============================================================================
    # PERFORMANCE ANALYTICS - Delegate to PerformanceAnalyticsService
    # ============================================================================

    def get_performance_overview(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get performance overview metrics."""
        return self.performance.get_performance_overview(user_id, start_date, end_date, types)

    def get_partner_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get partner analytics data."""
        return self.performance.get_partner_analytics(user_id, start_date, end_date, types)

    def get_head_to_head(self, user_id: int, partner1_id: int, partner2_id: int) -> dict[str, Any]:
        """Get head-to-head comparison between two partners."""
        return self.performance.get_head_to_head(user_id, partner1_id, partner2_id)

    def get_instructor_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get instructor insights."""
        return self.performance.get_instructor_analytics(user_id, start_date, end_date, types)

    # ============================================================================
    # READINESS ANALYTICS - Delegate to ReadinessAnalyticsService
    # ============================================================================

    def get_readiness_trends(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get readiness and recovery analytics."""
        return self.readiness.get_readiness_trends(user_id, start_date, end_date, types)

    def get_whoop_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get Whoop fitness tracker analytics."""
        return self.readiness.get_whoop_analytics(user_id, start_date, end_date, types)

    # ============================================================================
    # TECHNIQUE ANALYTICS - Delegate to TechniqueAnalyticsService
    # ============================================================================

    def get_technique_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get technique mastery analytics."""
        return self.technique.get_technique_analytics(user_id, start_date, end_date, types)

    # ============================================================================
    # STREAK/CONSISTENCY ANALYTICS - Delegate to StreakAnalyticsService
    # ============================================================================

    def get_consistency_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list | None = None,
    ) -> dict[str, Any]:
        """Get training consistency analytics."""
        return self.streak.get_consistency_analytics(user_id, start_date, end_date, types)

    def get_milestones(self, user_id: int) -> dict[str, Any]:
        """Get progression and milestone data."""
        return self.streak.get_milestones(user_id)

    # ============================================================================
    # ENHANCED ANALYTICS (Phase 1) - New delegation methods
    # ============================================================================

    def get_duration_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get duration analytics."""
        return self.performance.get_duration_analytics(user_id, start_date, end_date, types)

    def get_time_of_day_patterns(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get time of day performance patterns."""
        return self.performance.get_time_of_day_patterns(user_id, start_date, end_date, types)

    def get_gym_comparison(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get gym comparison metrics."""
        return self.performance.get_gym_comparison(user_id, start_date, end_date, types)

    def get_class_type_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get class type effectiveness metrics."""
        return self.performance.get_class_type_effectiveness(user_id, start_date, end_date)

    def get_partner_belt_distribution(self, user_id: int) -> dict[str, Any]:
        """Get partner belt distribution."""
        return self.performance.get_partner_belt_distribution(user_id)

    def get_weight_trend(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get weight trend with SMA."""
        return self.readiness.get_weight_trend(user_id, start_date, end_date)

    def get_training_frequency_heatmap(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get training frequency heatmap data."""
        return self.streak.get_training_frequency_heatmap(user_id, start_date, end_date, types)

    # ============================================================================
    # INSIGHTS ENGINE (Phase 2) - Delegate to InsightsAnalyticsService
    # ============================================================================

    def get_insights_summary(self, user_id: int) -> dict[str, Any]:
        """Get insights dashboard summary."""
        return self.insights.get_insights_summary(user_id)

    def get_readiness_performance_correlation(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get readiness × performance correlation."""
        return self.insights.get_readiness_performance_correlation(user_id, start_date, end_date)

    def get_training_load_management(self, user_id: int, days: int = 90) -> dict[str, Any]:
        """Get ACWR training load management data."""
        return self.insights.get_training_load_management(user_id, days)

    def get_technique_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get technique effectiveness with quadrant analysis."""
        return self.insights.get_technique_effectiveness(user_id, start_date, end_date)

    def get_partner_progression(self, user_id: int, partner_id: int) -> dict[str, Any]:
        """Get rolling progression against a specific partner."""
        return self.insights.get_partner_progression(user_id, partner_id)

    def get_session_quality_scores(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Get session quality scores."""
        return self.insights.get_session_quality_scores(user_id, start_date, end_date)

    def get_overtraining_risk(self, user_id: int) -> dict[str, Any]:
        """Get overtraining risk assessment."""
        return self.insights.get_overtraining_risk(user_id)

    def get_recovery_insights(self, user_id: int, days: int = 90) -> dict[str, Any]:
        """Get recovery insights."""
        return self.insights.get_recovery_insights(user_id, days)

    def get_checkin_trends(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """Get daily check-in trends: energy, quality, rest patterns."""
        return self.insights.get_checkin_trends(user_id, days)
