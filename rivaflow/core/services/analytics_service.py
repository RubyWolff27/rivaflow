"""Analytics service facade - delegates to focused analytics services.

This facade maintains backward compatibility while organizing analytics logic
into focused services:
- PerformanceAnalyticsService: Performance metrics, partner/instructor stats
- ReadinessAnalyticsService: Readiness trends and WHOOP data
- TechniqueAnalyticsService: Technique tracking and mastery
- StreakAnalyticsService: Training consistency, streaks, and milestones
"""
from datetime import date
from typing import Optional, Dict, Any

from rivaflow.core.services.performance_analytics import PerformanceAnalyticsService
from rivaflow.core.services.readiness_analytics import ReadinessAnalyticsService
from rivaflow.core.services.technique_analytics import TechniqueAnalyticsService
from rivaflow.core.services.streak_analytics import StreakAnalyticsService


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

    # ============================================================================
    # PERFORMANCE ANALYTICS - Delegate to PerformanceAnalyticsService
    # ============================================================================

    def get_performance_overview(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get performance overview metrics."""
        return self.performance.get_performance_overview(user_id, start_date, end_date)

    def get_partner_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get partner analytics data."""
        return self.performance.get_partner_analytics(user_id, start_date, end_date)

    def get_head_to_head(
        self, user_id: int, partner1_id: int, partner2_id: int
    ) -> Dict[str, Any]:
        """Get head-to-head comparison between two partners."""
        return self.performance.get_head_to_head(user_id, partner1_id, partner2_id)

    def get_instructor_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get instructor insights."""
        return self.performance.get_instructor_analytics(user_id, start_date, end_date)

    # ============================================================================
    # READINESS ANALYTICS - Delegate to ReadinessAnalyticsService
    # ============================================================================

    def get_readiness_trends(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get readiness and recovery analytics."""
        return self.readiness.get_readiness_trends(user_id, start_date, end_date)

    def get_whoop_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get Whoop fitness tracker analytics."""
        return self.readiness.get_whoop_analytics(user_id, start_date, end_date)

    # ============================================================================
    # TECHNIQUE ANALYTICS - Delegate to TechniqueAnalyticsService
    # ============================================================================

    def get_technique_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get technique mastery analytics."""
        return self.technique.get_technique_analytics(user_id, start_date, end_date)

    # ============================================================================
    # STREAK/CONSISTENCY ANALYTICS - Delegate to StreakAnalyticsService
    # ============================================================================

    def get_consistency_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get training consistency analytics."""
        return self.streak.get_consistency_analytics(user_id, start_date, end_date)

    def get_milestones(self, user_id: int) -> Dict[str, Any]:
        """Get progression and milestone data."""
        return self.streak.get_milestones(user_id)
