"""Service layer for generating training suggestions."""

import logging
import statistics
from datetime import date, timedelta

from rivaflow.core.rules import RULES, format_explanation
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.repositories import ReadinessRepository
from rivaflow.db.repositories.glossary_repo import GlossaryRepository

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Generate transparent, rules-based training suggestions."""

    def __init__(self):
        self.readiness_repo = ReadinessRepository()
        self.glossary_repo = GlossaryRepository()
        self.session_service = SessionService()

    def get_suggestion(self, user_id: int, target_date: date | None = None) -> dict:
        """
        Get training suggestion for a date.
        Returns dict with suggestion, triggered rules, and readiness snapshot.
        """
        if target_date is None:
            target_date = date.today()

        # Get latest readiness
        readiness = self.readiness_repo.get_latest(user_id)

        # Get session context
        consecutive_counts = self.session_service.get_consecutive_class_type_count(
            user_id
        )
        stale_techniques = self.glossary_repo.get_stale(user_id, days=7)

        session_context = {
            "consecutive_gi_sessions": consecutive_counts.get("gi", 0),
            "consecutive_nogi_sessions": consecutive_counts.get("no-gi", 0),
            "stale_techniques": stale_techniques,
        }

        # Enrich readiness with WHOOP recovery data if available
        try:
            from rivaflow.db.repositories.whoop_connection_repo import (
                WhoopConnectionRepository,
            )
            from rivaflow.db.repositories.whoop_recovery_cache_repo import (
                WhoopRecoveryCacheRepository,
            )

            conn_repo = WhoopConnectionRepository()
            whoop_conn = conn_repo.get_by_user_id(user_id)
            if whoop_conn and whoop_conn.get("is_active"):
                recovery_repo = WhoopRecoveryCacheRepository()
                latest_rec = recovery_repo.get_latest(user_id)
                if latest_rec and readiness:
                    readiness["whoop_recovery_score"] = latest_rec.get("recovery_score")
                    readiness["hrv_ms"] = latest_rec.get("hrv_ms")

                # Calculate HRV drop percentage
                if latest_rec and latest_rec.get("hrv_ms"):
                    week_ago = (date.today() - timedelta(days=7)).isoformat()
                    today_str = date.today().isoformat() + "T23:59:59"
                    recent = recovery_repo.get_by_date_range(
                        user_id, week_ago, today_str
                    )
                    hrv_values = [
                        r["hrv_ms"] for r in recent if r.get("hrv_ms") is not None
                    ]
                    if len(hrv_values) >= 2:
                        avg_hrv = statistics.mean(hrv_values)
                        if avg_hrv > 0:
                            drop_pct = round(
                                ((avg_hrv - latest_rec["hrv_ms"]) / avg_hrv) * 100,
                                1,
                            )
                            if drop_pct > 0:
                                session_context["hrv_drop_pct"] = drop_pct
        except Exception:
            logger.debug("WHOOP context enrichment skipped", exc_info=True)

        # Evaluate rules
        triggered_rules = []
        for rule in sorted(RULES, key=lambda r: r.priority):
            if rule.condition(readiness, session_context):
                triggered_rules.append(
                    {
                        "name": rule.name,
                        "recommendation": self._format_recommendation(
                            rule.recommendation, readiness, session_context
                        ),
                        "explanation": format_explanation(
                            rule.explanation, readiness, session_context
                        ),
                        "priority": rule.priority,
                    }
                )

        # Build suggestion
        if not triggered_rules:
            primary_suggestion = "Train as planned — no specific recommendations"
        else:
            # Use highest priority rule (lowest number)
            primary_rule = triggered_rules[0]
            primary_suggestion = primary_rule["recommendation"]

        return {
            "date": target_date,
            "suggestion": primary_suggestion,
            "triggered_rules": triggered_rules,
            "readiness": readiness,
            "session_context": session_context,
        }

    def _format_recommendation(
        self, recommendation: str, readiness: dict, session_context: dict
    ) -> str:
        """Format recommendation string with context values."""
        # Similar to format_explanation but for recommendation text
        replacements = {}

        if readiness:
            hotspot = readiness.get("hotspot_note")
            replacements["hotspot"] = hotspot if hotspot else "the affected area"
            replacements["whoop_recovery"] = readiness.get("whoop_recovery_score", "")

        replacements["hrv_drop_pct"] = session_context.get("hrv_drop_pct", "")

        stale = session_context.get("stale_techniques", [])
        if stale:
            tech_names = [t["name"] for t in stale[:3]]
            replacements["techniques"] = ", ".join(tech_names)

        result = recommendation
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result
