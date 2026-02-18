"""Advanced insights analytics engine — correlation, trends, and predictions.

Pure Python math (no numpy). Uses Pearson r, EWMA, Shannon entropy.

This module is a facade that delegates to focused sub-modules:
- insights_math: Pure math helpers (_pearson_r, _ewma, etc.)
- insights_data: Data aggregation (correlation, training load, techniques, etc.)
- insights_summary: Risk assessment, recovery, and digest summary
"""

from datetime import date
from typing import Any

from rivaflow.core.services.insights_data import (
    compute_checkin_trends,
    compute_partner_progression,
    compute_readiness_performance_correlation,
    compute_session_quality_scores,
    compute_technique_effectiveness,
    compute_training_load_management,
)

# Re-export math helpers so existing imports keep working
from rivaflow.core.services.insights_math import (  # noqa: F401
    _ewma,
    _linear_slope,
    _pearson_r,
    _shannon_entropy,
)
from rivaflow.core.services.insights_summary import (
    compute_insights_summary,
    compute_overtraining_risk,
    compute_recovery_insights,
)
from rivaflow.db.repositories import (
    FriendRepository,
    GlossaryRepository,
    ReadinessRepository,
    SessionRepository,
    SessionRollRepository,
)
from rivaflow.db.repositories.session_technique_repo import (
    SessionTechniqueRepository,
)


class InsightsAnalyticsService:
    """Data-science-driven insights engine."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()
        self.roll_repo = SessionRollRepository()
        self.friend_repo = FriendRepository()
        self.glossary_repo = GlossaryRepository()
        self.technique_repo = SessionTechniqueRepository()

    # ------------------------------------------------------------------
    # 1. Readiness x Performance correlation
    # ------------------------------------------------------------------

    def get_readiness_performance_correlation(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Match readiness to same-day sessions, compute Pearson r."""
        return compute_readiness_performance_correlation(
            self.session_repo,
            self.readiness_repo,
            user_id,
            start_date,
            end_date,
        )

    # ------------------------------------------------------------------
    # 2. Training load management (ACWR)
    # ------------------------------------------------------------------

    def get_training_load_management(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """EWMA acute (7d) vs chronic (28d) training load."""
        return compute_training_load_management(
            self.session_repo,
            user_id,
            days,
        )

    # ------------------------------------------------------------------
    # 3. Technique effectiveness
    # ------------------------------------------------------------------

    def get_technique_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Cross-ref submissions with technique training frequency."""
        return compute_technique_effectiveness(
            self.session_repo,
            self.roll_repo,
            self.glossary_repo,
            self.technique_repo,
            user_id,
            start_date,
            end_date,
        )

    # ------------------------------------------------------------------
    # 4. Partner progression
    # ------------------------------------------------------------------

    def get_partner_progression(
        self,
        user_id: int,
        partner_id: int,
    ) -> dict[str, Any]:
        """Rolling 5-roll window sub rate against a specific partner."""
        return compute_partner_progression(
            self.session_repo,
            self.roll_repo,
            self.friend_repo,
            user_id,
            partner_id,
        )

    # ------------------------------------------------------------------
    # 5. Session quality scores
    # ------------------------------------------------------------------

    def get_session_quality_scores(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Composite per-session quality score (0-100)."""
        return compute_session_quality_scores(
            self.session_repo,
            self.technique_repo,
            user_id,
            start_date,
            end_date,
        )

    # ------------------------------------------------------------------
    # 6. Overtraining risk
    # ------------------------------------------------------------------

    def get_overtraining_risk(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """6 factors = 0-100 risk score (20+20+15+15+15+15)."""
        return compute_overtraining_risk(
            self.session_repo,
            self.readiness_repo,
            self.get_training_load_management,
            user_id,
        )

    # ------------------------------------------------------------------
    # 7. Recovery insights
    # ------------------------------------------------------------------

    def get_recovery_insights(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Sleep -> next-day performance, optimal rest days analysis."""
        return compute_recovery_insights(
            self.session_repo,
            self.readiness_repo,
            user_id,
            days,
        )

    # ------------------------------------------------------------------
    # 8. Summary digest
    # ------------------------------------------------------------------

    def get_insights_summary(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """Lightweight dashboard digest."""
        return compute_insights_summary(
            self.get_training_load_management,
            self.get_overtraining_risk,
            self.get_technique_effectiveness,
            self.get_session_quality_scores,
            user_id,
        )

    # ------------------------------------------------------------------
    # 9. Check-in trends (energy, quality, rest patterns)
    # ------------------------------------------------------------------

    def get_checkin_trends(
        self,
        user_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Analyse daily check-in data for energy, quality, and rest trends."""
        return compute_checkin_trends(user_id, days)
