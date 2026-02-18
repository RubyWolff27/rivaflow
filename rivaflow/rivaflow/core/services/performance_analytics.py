"""Performance analytics service for training sessions.

This module is a facade that delegates to focused sub-modules:
- performance_scoring: Core performance overview, partner analytics, head-to-head
- performance_trends: Duration, time-of-day, gym, class type, belt, instructor
"""

from datetime import date
from typing import Any

from rivaflow.core.services.performance_scoring import (
    compute_head_to_head,
    compute_partner_analytics,
    compute_performance_overview,
    get_session_date,
)
from rivaflow.core.services.performance_trends import (
    compute_class_type_effectiveness,
    compute_duration_analytics,
    compute_gym_comparison,
    compute_instructor_analytics,
    compute_partner_belt_distribution,
    compute_time_of_day_patterns,
)
from rivaflow.db.repositories import (
    FriendRepository,
    GlossaryRepository,
    GradingRepository,
    SessionRepository,
    SessionRollRepository,
)


class PerformanceAnalyticsService:
    """Business logic for performance and partner analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.roll_repo = SessionRollRepository()
        self.friend_repo = FriendRepository()
        self.grading_repo = GradingRepository()
        self.glossary_repo = GlossaryRepository()

    def get_performance_overview(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get performance overview metrics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - submission_success_over_time: Monthly breakdown of subs for/against
            - training_volume_calendar: Daily session data for heatmap
            - top_submissions: Top 5 subs given and received
            - performance_by_belt: Metrics grouped by belt rank periods
        """
        return compute_performance_overview(
            self.session_repo,
            self.roll_repo,
            self.glossary_repo,
            self.grading_repo,
            user_id,
            start_date,
            end_date,
            types,
        )

    def _calculate_period_summary(self, sessions: list[dict]) -> dict[str, Any]:
        """Calculate summary metrics for a period with safe null handling."""
        from rivaflow.core.services.performance_scoring import (
            calculate_period_summary,
        )

        return calculate_period_summary(sessions)

    def _calculate_daily_timeseries(
        self, sessions: list[dict], start_date: date, end_date: date
    ) -> dict[str, list[float]]:
        """Calculate daily aggregated time series data for sparklines."""
        from rivaflow.core.services.performance_scoring import (
            calculate_daily_timeseries,
        )

        return calculate_daily_timeseries(sessions, start_date, end_date)

    def _calculate_partner_session_distribution(
        self, user_id: int, sessions: list[dict]
    ) -> list[dict[str, Any]]:
        """Calculate which partners appear in which sessions."""
        from rivaflow.core.services.performance_scoring import (
            calculate_partner_session_distribution,
        )

        return calculate_partner_session_distribution(
            self.roll_repo, self.friend_repo, user_id, sessions
        )

    def _calculate_performance_by_belt(
        self, sessions: list[dict], gradings: list[dict]
    ) -> list[dict]:
        """Calculate metrics for each belt rank period."""
        from rivaflow.core.services.performance_scoring import (
            calculate_performance_by_belt,
        )

        return calculate_performance_by_belt(sessions, gradings)

    def get_partner_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get partner analytics data.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - partner_matrix: Table of all partners with stats
            - partner_diversity: Unique partners, new vs recurring
        """
        return compute_partner_analytics(
            self.session_repo,
            self.roll_repo,
            self.friend_repo,
            user_id,
            start_date,
            end_date,
            types,
        )

    def get_head_to_head(
        self, user_id: int, partner1_id: int, partner2_id: int
    ) -> dict[str, Any]:
        """Get head-to-head comparison between two partners."""
        return compute_head_to_head(
            self.roll_repo,
            self.friend_repo,
            user_id,
            partner1_id,
            partner2_id,
        )

    def _get_session_date(self, user_id: int, session_id: int) -> date:
        """Helper to get session date."""
        return get_session_date(self.session_repo, user_id, session_id)

    def get_duration_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Average duration trends, duration by class type & gym."""
        return compute_duration_analytics(
            self.session_repo,
            user_id,
            start_date,
            end_date,
            types,
        )

    def get_time_of_day_patterns(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Bucket class_time into morning/afternoon/evening with performance."""
        return compute_time_of_day_patterns(
            self.session_repo,
            user_id,
            start_date,
            end_date,
            types,
        )

    def get_gym_comparison(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Sessions, avg intensity, sub rate per gym."""
        return compute_gym_comparison(
            self.session_repo,
            user_id,
            start_date,
            end_date,
            types,
        )

    def get_class_type_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Sub rate, avg rolls, intensity per class type."""
        return compute_class_type_effectiveness(
            self.session_repo,
            user_id,
            start_date,
            end_date,
        )

    def get_partner_belt_distribution(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """Partner count by belt rank from friends table."""
        return compute_partner_belt_distribution(
            self.friend_repo,
            user_id,
        )

    def get_instructor_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get instructor insights.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - performance_by_instructor: Metrics for each instructor
            - instructor_styles: Teaching style analysis
        """
        return compute_instructor_analytics(
            self.session_repo,
            self.friend_repo,
            user_id,
            start_date,
            end_date,
            types,
        )
