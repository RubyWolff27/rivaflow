"""Service layer for generating training suggestions."""

from datetime import date

from rivaflow.core.rules import RULES, format_explanation
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.repositories import ReadinessRepository
from rivaflow.db.repositories.glossary_repo import GlossaryRepository


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
        consecutive_counts = self.session_service.get_consecutive_class_type_count(user_id)
        stale_techniques = self.glossary_repo.get_stale(user_id, days=7)

        session_context = {
            "consecutive_gi_sessions": consecutive_counts.get("gi", 0),
            "consecutive_nogi_sessions": consecutive_counts.get("no-gi", 0),
            "stale_techniques": stale_techniques,
        }

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

        stale = session_context.get("stale_techniques", [])
        if stale:
            tech_names = [t["name"] for t in stale[:3]]
            replacements["techniques"] = ", ".join(tech_names)

        result = recommendation
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result
