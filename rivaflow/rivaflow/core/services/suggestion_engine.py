"""Service layer for generating training suggestions."""

import json
import logging
import statistics
from datetime import date, timedelta

from rivaflow.core.rules import RULES, format_explanation
from rivaflow.core.services.insights_analytics import _linear_slope
from rivaflow.core.services.session_service import SessionService
from rivaflow.db.repositories import ReadinessRepository
from rivaflow.db.repositories.coach_preferences_repo import (
    CoachPreferencesRepository,
)
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

        # Enrich with session frequency / load data
        try:
            from rivaflow.db.repositories.session_repo import SessionRepository

            recent_all = SessionRepository.get_recent(user_id, limit=10)
            if recent_all:
                last_date_str = str(recent_all[0].get("session_date", ""))
                if last_date_str:
                    try:
                        last_dt = date.fromisoformat(last_date_str[:10])
                        session_context["days_since_last_session"] = (
                            date.today() - last_dt
                        ).days
                    except ValueError:
                        pass
                session_context["last_session_intensity"] = recent_all[0].get(
                    "intensity"
                )

            # Sessions this week (Mon-Sun)
            week_start = date.today() - timedelta(days=date.today().weekday())
            week_sessions = [
                s
                for s in recent_all
                if s.get("session_date")
                and str(s["session_date"])[:10] >= week_start.isoformat()
            ]
            session_context["sessions_this_week"] = len(week_sessions)
        except Exception:
            logger.debug("Session frequency enrichment skipped", exc_info=True)

        # Enrich with coach preferences for mode-aware rules
        try:
            prefs = CoachPreferencesRepository.get(user_id)
            if prefs:
                session_context["training_mode"] = prefs.get(
                    "training_mode", "lifestyle"
                )
                # Competition countdown
                if prefs.get("training_mode") == "competition_prep" and prefs.get(
                    "comp_date"
                ):
                    try:
                        comp_date = date.fromisoformat(prefs["comp_date"])
                        session_context["days_until_comp"] = (
                            comp_date - date.today()
                        ).days
                    except ValueError:
                        pass
                # Persistent injuries — only active ones trigger rules
                injuries = prefs.get("injuries") or []
                if isinstance(injuries, str):
                    try:
                        injuries = json.loads(injuries)
                    except (json.JSONDecodeError, TypeError):
                        injuries = []
                active_injuries = [
                    i for i in injuries if i.get("status", "active") == "active"
                ]
                if active_injuries:
                    session_context["persistent_injuries"] = active_injuries
        except Exception:
            logger.debug("Coach preferences enrichment skipped", exc_info=True)

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

                    # Compute sustained HRV slope for 5+ day rule
                    if len(hrv_values) >= 5:
                        session_context["hrv_slope_5d"] = round(
                            _linear_slope(hrv_values), 4
                        )

                # Sleep debt from latest recovery record
                if latest_rec and latest_rec.get("sleep_debt_ms") is not None:
                    session_context["sleep_debt_min"] = round(
                        latest_rec["sleep_debt_ms"] / 60_000
                    )
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
        hrv_slope = session_context.get("hrv_slope_5d")
        replacements["hrv_slope_5d"] = (
            f"{hrv_slope:+.2f}" if hrv_slope is not None else ""
        )

        replacements["days_until_comp"] = session_context.get("days_until_comp", "")

        stale = session_context.get("stale_techniques", [])
        if stale:
            tech_names = [t["name"] for t in stale[:3]]
            replacements["techniques"] = ", ".join(tech_names)

        injuries = session_context.get("persistent_injuries", [])
        if injuries:
            areas = [inj.get("area", "unknown") for inj in injuries[:3]]
            replacements["injury_areas"] = ", ".join(areas)

        # Load management replacements
        replacements["last_intensity"] = session_context.get(
            "last_session_intensity", ""
        )
        replacements["sessions_week"] = session_context.get("sessions_this_week", "")
        replacements["days_off"] = session_context.get("days_since_last_session", "")
        sleep_debt_min = session_context.get("sleep_debt_min")
        replacements["sleep_debt"] = (
            f"{sleep_debt_min / 60:.1f}" if sleep_debt_min is not None else ""
        )

        result = recommendation
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result
