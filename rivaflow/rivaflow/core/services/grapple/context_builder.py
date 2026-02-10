"""Context builder for Grapple AI Coach - builds personalized prompts from user data."""

import json
import logging
from datetime import date, datetime, timedelta

from rivaflow.core.services.insights_analytics import (
    InsightsAnalyticsService,
    _linear_slope,
)
from rivaflow.core.services.privacy_service import PrivacyService
from rivaflow.db.repositories.coach_preferences_repo import (
    CoachPreferencesRepository,
)
from rivaflow.db.repositories.readiness_repo import ReadinessRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class GrappleContextBuilder:
    """
    Builds personalized context for Grapple AI Coach from user's training data.

    Similar to the existing chat context builder but optimized for Grapple's needs.
    """

    def __init__(self, user_id: int):
        """
        Initialize context builder.

        Args:
            user_id: User ID to build context for
        """
        self.user_id = user_id
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()
        self.user_repo = UserRepository()
        self.insights = InsightsAnalyticsService()

    def build_system_prompt(self) -> str:
        """
        Build the system prompt with user context and coaching preferences.

        Returns:
            Complete system prompt string
        """
        user_context = self._build_user_context()
        prefs = CoachPreferencesRepository.get(self.user_id)
        mode_directive = self._build_mode_directive(prefs)
        style_directive = self._build_style_directive(prefs)
        injury_directive = self._build_injury_directive(prefs)

        return f"""You are Grapple, an expert Brazilian Jiu-Jitsu (BJJ) coach and training advisor for RivaFlow.

Your role is to:
1. Provide expert advice on BJJ technique, strategy, and training
2. Analyze the user's training patterns and provide personalized insights
3. Give recommendations on recovery, injury prevention, and training frequency
4. Help set realistic goals and track progress
5. Explain BJJ concepts, positions, and techniques clearly
6. Be supportive, motivating, and safety-conscious

Guidelines:
- Always prioritize safety and proper technique over ego or intensity
- Consider training frequency, intensity, and recovery in your advice
- Reference specific sessions or patterns when giving feedback
- Use the DEEP ANALYTICS INSIGHTS section to provide data-driven advice:
  ACWR (training load ratio), overtraining risk, session quality scores,
  game breadth, money moves, sleep-performance correlation, and recovery data
- Be concise but thorough (aim for 2-4 paragraphs per response)
- If medical advice is needed, recommend seeing a doctor or physiotherapist
- Use BJJ terminology appropriately but explain when needed
- Provide actionable advice, not just general statements
{mode_directive}{style_directive}{injury_directive}
CURRENT USER DATA:
{user_context}

Now respond to the user's questions using this context. Reference their specific training data when relevant."""

    def _build_mode_directive(self, prefs: dict | None) -> str:
        """Build mode-specific coaching directive."""
        if not prefs:
            return ""
        mode = prefs.get("training_mode", "lifestyle")

        if mode == "competition_prep":
            comp_name = prefs.get("comp_name") or "upcoming competition"
            comp_date = prefs.get("comp_date")
            comp_div = prefs.get("comp_division") or ""
            comp_wt = prefs.get("comp_weight_class") or ""
            days_str = ""
            if comp_date:
                try:
                    days = (date.fromisoformat(comp_date) - date.today()).days
                    days_str = f" ({days} days away)"
                except ValueError:
                    pass
            detail = f"{comp_name}{days_str}"
            if comp_div:
                detail += f", {comp_div}"
            if comp_wt:
                detail += f", {comp_wt}"
            return f"""
COACHING DIRECTIVE — COMPETITION PREP:
Athlete is preparing for: {detail}.
- Sharpen their A-game over exploring new techniques
- Monitor training load — taper 2 weeks out, light work fight week
- Weight management awareness if weight class is specified
- Emphasize match simulation, competition rolling, and mental prep
- Track ACWR closely and warn about overtraining risk
"""
        if mode == "skill_development":
            focus = ", ".join(prefs.get("focus_areas") or [])
            weak = prefs.get("weaknesses") or ""
            extras = ""
            if focus:
                extras += f"\n- Reference their focus areas: {focus}"
            if weak:
                extras += f"\n- Address their weaknesses: {weak}"
            return f"""
COACHING DIRECTIVE — SKILL DEVELOPMENT:
Focused on technical growth and expanding their game.
- Recommend deliberate practice: positional sparring, drilling, weak positions
- Encourage working from weak positions, not just strengths
- Track technique diversity — flag if drilling a narrow set
- Recommend video study and mental rehearsal alongside mat time{extras}
"""
        if mode == "recovery":
            return """
COACHING DIRECTIVE — RECOVERY MODE:
Athlete is in a recovery period (injury rehab, overtraining, or burnout).
- Strongly discourage high intensity until cleared
- Focus on mobility, flow rolling, and drilling
- Monitor readiness/WHOOP recovery extra carefully
- Suggest graduated return-to-play protocols
- Recommend cross-training (yoga, swimming) where appropriate
- Be extra cautious — err on the side of rest
"""
        # Default: lifestyle
        return """
COACHING DIRECTIVE — LIFESTYLE TRAINING:
Training for long-term enjoyment and health, not competition.
- Prioritize injury prevention and sustainability
- Encourage exploration of new techniques and positions
- Balance training variety (gi/no-gi, different positions)
- Recovery and longevity over intensity
- Fun and social aspects of training matter
"""

    def _build_style_directive(self, prefs: dict | None) -> str:
        """Build coaching style modifier."""
        if not prefs:
            return ""
        style = prefs.get("coaching_style", "balanced")
        styles = {
            "motivational": (
                "COACHING STYLE: Motivational — lead with encouragement, "
                "celebrate progress, frame challenges as opportunities, "
                "use positive language."
            ),
            "analytical": (
                "COACHING STYLE: Analytical — focus on data and patterns, "
                "reference specific numbers (ACWR, HRV, session quality), "
                "be precise and evidence-based."
            ),
            "tough_love": (
                "COACHING STYLE: Tough Love — be direct and honest even "
                "if uncomfortable, call out sandbagging or excuses, push them."
            ),
            "technical": (
                "COACHING STYLE: Technical — focus on technique breakdown "
                "and positional details, reference specific moves and "
                "transitions, less motivational talk, more instruction."
            ),
        }
        text = styles.get(style)
        if text:
            return f"\n{text}\n"
        return ""

    def _build_injury_directive(self, prefs: dict | None) -> str:
        """Build persistent injury context."""
        if not prefs:
            return ""
        injuries = prefs.get("injuries") or []
        if isinstance(injuries, str):
            try:
                injuries = json.loads(injuries)
            except (json.JSONDecodeError, TypeError):
                return ""
        if not injuries:
            return ""
        lines = ["PERSISTENT INJURIES — adjust all recommendations:"]
        for inj in injuries:
            area = inj.get("area", "unknown")
            side = inj.get("side", "")
            severity = inj.get("severity", "")
            notes = inj.get("notes", "")
            entry = f"- {area}"
            if side and side != "n/a":
                entry += f" ({side})"
            if severity:
                entry += f", severity: {severity}"
            if notes:
                entry += f". {notes}"
            lines.append(entry)
        lines.append(
            "Avoid suggesting techniques or positions that "
            "could aggravate these injuries."
        )
        return "\n" + "\n".join(lines) + "\n"

    def _build_user_context(self) -> str:
        """
        Build context string from user's training history.

        Returns:
            Formatted context string
        """
        # Get user profile
        user = self.user_repo.get_by_id(self.user_id)
        if not user:
            return "User profile not found."

        # Get recent sessions (last 30 days + 20 most recent)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sessions = self.session_repo.get_recent(self.user_id, limit=200)

        # Redact all sessions for LLM
        redacted_sessions = []
        for session in recent_sessions:
            redacted = PrivacyService.redact_for_llm(session, include_notes=True)
            redacted_sessions.append(redacted)

        # Calculate summary stats
        total_sessions = len(redacted_sessions)
        context_parts = [
            "USER PROFILE:",
            f"Name: {user['first_name']} {user['last_name']}",
            f"Email: {user['email']}",
            "",
        ]

        # Inject practitioner context from coach preferences
        prefs = CoachPreferencesRepository.get(self.user_id)
        if prefs:
            ctx = ["PRACTITIONER CONTEXT:"]
            if prefs.get("years_training"):
                ctx.append(f"Experience: {prefs['years_training']} years")
            if (
                prefs.get("competition_experience")
                and prefs["competition_experience"] != "none"
            ):
                ctx.append(f"Competition experience: {prefs['competition_experience']}")
            if prefs.get("available_days_per_week"):
                ctx.append(
                    f"Available training days: "
                    f"{prefs['available_days_per_week']}/week"
                )
            if prefs.get("primary_position") and prefs["primary_position"] != "both":
                ctx.append(f"Primary position: {prefs['primary_position']}")
            focus = prefs.get("focus_areas") or []
            if isinstance(focus, str):
                try:
                    focus = json.loads(focus)
                except (json.JSONDecodeError, TypeError):
                    focus = []
            if focus:
                ctx.append(f"Focus areas: {', '.join(focus)}")
            if prefs.get("weaknesses"):
                ctx.append(f"Self-identified weaknesses: {prefs['weaknesses']}")
            motivations = prefs.get("motivations") or []
            if isinstance(motivations, str):
                try:
                    motivations = json.loads(motivations)
                except (json.JSONDecodeError, TypeError):
                    motivations = []
            if motivations:
                ctx.append(f"Motivations: {', '.join(motivations)}")
            if prefs.get("additional_context"):
                ctx.append(f"Additional context: {prefs['additional_context']}")
            if len(ctx) > 1:
                context_parts.extend(ctx)
                context_parts.append("")

        if total_sessions > 0:
            # Calculate training stats
            total_duration = sum(s.get("duration_mins", 0) for s in redacted_sessions)
            total_rolls = sum(s.get("rolls_count", 0) for s in redacted_sessions)
            avg_intensity = (
                sum(s.get("intensity", 0) for s in redacted_sessions) / total_sessions
            )

            # Get unique gyms and techniques
            gyms = set(s.get("gym", "") for s in redacted_sessions if s.get("gym"))
            all_techniques = set()
            for s in redacted_sessions:
                if s.get("techniques"):
                    all_techniques.update(s["techniques"])

            # Sessions in last 30 days
            sessions_last_30_days = [
                s
                for s in redacted_sessions
                if s.get("date") and self._parse_date(s["date"]) >= thirty_days_ago
            ]

            context_parts.extend(
                [
                    "TRAINING SUMMARY:",
                    f"Total sessions logged: {total_sessions}",
                    f"Sessions in last 30 days: {len(sessions_last_30_days)}",
                    f"Total training time: {total_duration} minutes ({total_duration / 60:.1f} hours)",
                    f"Total rolls: {total_rolls}",
                    f"Average intensity: {avg_intensity:.1f}/10",
                    f"Gyms trained at: {', '.join(sorted(gyms)) if gyms else 'Not specified'}",
                    f"Techniques practiced: {len(all_techniques)} unique techniques",
                    "",
                ]
            )

            # Show last 15 sessions in detail
            context_parts.append("RECENT SESSIONS (last 15):")
            context_parts.append("")

            for session in redacted_sessions[:15]:
                date_val = session.get("date", "Unknown")
                date_str = str(date_val) if date_val != "Unknown" else "Unknown"
                gym = session.get("gym", "Unknown")
                duration = session.get("duration_mins", 0)
                intensity = session.get("intensity", 0)
                rolls = session.get("rolls_count", 0)
                techniques = session.get("techniques", [])
                notes = session.get("notes", "")

                session_summary = (
                    f"- {date_str} at {gym}: {duration}min, intensity {intensity}/10"
                )
                if rolls > 0:
                    session_summary += f", {rolls} rolls"
                if techniques:
                    techniques_str = ", ".join(techniques[:5])
                    if len(techniques) > 5:
                        techniques_str += f" (+{len(techniques) - 5} more)"
                    session_summary += f" | Techniques: {techniques_str}"
                if notes:
                    session_summary += f" | Notes: {notes[:200]}"

                context_parts.append(session_summary)

            # Add recent readiness data if available (last 7 days)
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            recent_readiness = self.readiness_repo.get_by_date_range(
                self.user_id, start_date, end_date
            )
            if recent_readiness:
                context_parts.append("")
                context_parts.append("RECENT READINESS (last 7 days):")
                for r in recent_readiness:
                    r_date = r.get("date", "Unknown")
                    energy = r.get("energy_level", 0)
                    soreness = r.get("soreness_level", 0)
                    sleep = r.get("sleep_quality", 0)
                    context_parts.append(
                        f"- {r_date}: Energy {energy}/10, Soreness {soreness}/10, Sleep {sleep}/10"
                    )

            # ── Deep analytics context ──
            try:
                deep = self._build_deep_analytics_context()
                if deep:
                    context_parts.append("")
                    context_parts.append(deep)
            except Exception:
                logger.debug("Deep analytics context unavailable", exc_info=True)

            # ── WHOOP recovery context ──
            try:
                whoop = self._build_whoop_context()
                if whoop:
                    context_parts.append("")
                    context_parts.append(whoop)
            except Exception:
                logger.debug("WHOOP context unavailable", exc_info=True)

        else:
            context_parts.append("No training sessions logged yet.")

        return "\n".join(context_parts)

    def _build_deep_analytics_context(self) -> str:
        """Build deep analytics context from InsightsAnalyticsService."""
        parts = ["DEEP ANALYTICS INSIGHTS:"]

        # Training load (ACWR)
        try:
            load = self.insights.get_training_load_management(self.user_id, days=90)
            parts.append(
                f"Training Load: ACWR={load['current_acwr']} "
                f"({load['current_zone']})"
            )
        except Exception:
            pass

        # Overtraining risk
        try:
            risk = self.insights.get_overtraining_risk(self.user_id)
            parts.append(
                f"Overtraining Risk: {risk['risk_score']}/100 " f"({risk['level']})"
            )
            if risk["recommendations"]:
                parts.append(
                    f"Recommendations: {'; '.join(risk['recommendations'][:2])}"
                )
        except Exception:
            pass

        # Session quality
        try:
            quality = self.insights.get_session_quality_scores(self.user_id)
            parts.append(f"Avg Session Quality: {quality['avg_quality']}/100")
        except Exception:
            pass

        # Technique effectiveness
        try:
            tech = self.insights.get_technique_effectiveness(self.user_id)
            parts.append(f"Game Breadth: {tech['game_breadth']}/100")
            if tech.get("money_moves"):
                names = ", ".join(t["name"] for t in tech["money_moves"][:3])
                parts.append(f"Money Moves: {names}")
        except Exception:
            pass

        # Recovery insights
        try:
            recovery = self.insights.get_recovery_insights(self.user_id, days=90)
            if recovery.get("optimal_rest_days"):
                parts.append(
                    f"Optimal Rest: {recovery['optimal_rest_days']} "
                    f"day(s) between sessions"
                )
            if (
                recovery.get("sleep_correlation")
                and abs(recovery["sleep_correlation"]) >= 0.2
            ):
                parts.append(
                    f"Sleep-Performance Correlation: "
                    f"r={recovery['sleep_correlation']}"
                )
        except Exception:
            pass

        # Readiness correlation
        try:
            corr = self.insights.get_readiness_performance_correlation(self.user_id)
            if corr.get("optimal_zone"):
                parts.append(
                    f"Best Performance Zone: readiness {corr['optimal_zone']} "
                    f"(r={corr['r_value']})"
                )
        except Exception:
            pass

        if len(parts) <= 1:
            return ""

        return "\n".join(parts)

    def _build_whoop_context(self) -> str:
        """Build WHOOP recovery context if user has an active connection."""
        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )
        from rivaflow.db.repositories.whoop_recovery_cache_repo import (
            WhoopRecoveryCacheRepository,
        )

        conn = WhoopConnectionRepository.get_by_user_id(self.user_id)
        if not conn or not conn.get("is_active"):
            return ""

        end_dt = date.today().isoformat() + "T23:59:59"
        start_dt = (date.today() - timedelta(days=7)).isoformat()
        records = WhoopRecoveryCacheRepository.get_by_date_range(
            self.user_id, start_dt, end_dt
        )
        if not records:
            return ""

        latest = records[-1]
        parts = ["WHOOP RECOVERY DATA:"]

        # Latest snapshot
        rec_score = latest.get("recovery_score")
        hrv = latest.get("hrv_ms")
        rhr = latest.get("resting_hr")
        spo2 = latest.get("spo2")
        snap = "Latest Recovery:"
        if rec_score is not None:
            snap += f" {rec_score:.0f}%"
        if hrv is not None:
            snap += f" | HRV: {hrv:.0f}ms"
        if rhr is not None:
            snap += f" | RHR: {rhr:.0f}bpm"
        if spo2 is not None:
            snap += f" | SpO2: {spo2:.0f}%"
        parts.append(snap)

        # Sleep info
        sleep_perf = latest.get("sleep_performance")
        sleep_dur_ms = latest.get("sleep_duration_ms")
        rem_ms = latest.get("rem_sleep_ms")
        sws_ms = latest.get("slow_wave_ms")
        if sleep_perf is not None or sleep_dur_ms is not None:
            sleep_line = "Sleep:"
            if sleep_perf is not None:
                sleep_line += f" {sleep_perf:.0f}% performance"
            if sleep_dur_ms is not None:
                hrs = sleep_dur_ms / 3_600_000
                sleep_line += f" ({hrs:.1f}h"
                if rem_ms is not None and sleep_dur_ms > 0:
                    sleep_line += f", {rem_ms / sleep_dur_ms * 100:.0f}% REM"
                if sws_ms is not None and sleep_dur_ms > 0:
                    sleep_line += f", {sws_ms / sleep_dur_ms * 100:.0f}% SWS"
                sleep_line += ")"
            parts.append(sleep_line)

        # 7-day HRV trend
        hrv_values = [r["hrv_ms"] for r in records if r.get("hrv_ms") is not None]
        if len(hrv_values) >= 3:
            slope = _linear_slope(hrv_values)
            direction = "Declining" if slope < 0 else "Improving"
            parts.append(f"7-Day HRV Trend: {direction} ({slope:+.1f} ms/day)")

        # 7-day avg recovery & sleep debt
        rec_values = [
            r["recovery_score"] for r in records if r.get("recovery_score") is not None
        ]
        avg_rec = sum(rec_values) / len(rec_values) if rec_values else None
        sleep_debt_ms = latest.get("sleep_debt_ms")
        extras = ""
        if avg_rec is not None:
            extras += f"7-Day Avg Recovery: {avg_rec:.0f}%"
        if sleep_debt_ms is not None:
            debt_min = sleep_debt_ms / 60_000
            if extras:
                extras += f" | Sleep Debt: {debt_min:.0f} min"
            else:
                extras += f"Sleep Debt: {debt_min:.0f} min"
        if extras:
            parts.append(extras)

        if len(parts) <= 1:
            return ""

        return "\n".join(parts)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        try:
            if isinstance(date_str, datetime):
                return date_str
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.min

    def get_conversation_context(
        self, recent_messages: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """
        Build full conversation context for LLM.

        Args:
            recent_messages: Recent messages from session (role + content)

        Returns:
            Full message list including system prompt
        """
        system_prompt = self.build_system_prompt()

        # Start with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history
        messages.extend(recent_messages)

        return messages
