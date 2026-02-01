"""Context builder for Grapple AI Coach - builds personalized prompts from user data."""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.readiness_repo import ReadinessRepository
from rivaflow.db.repositories.user_repo import UserRepository
from rivaflow.core.services.privacy_service import PrivacyService

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

    def build_system_prompt(self) -> str:
        """
        Build the system prompt with user context.

        Returns:
            Complete system prompt string
        """
        user_context = self._build_user_context()

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
- Be concise but thorough (aim for 2-4 paragraphs per response)
- If medical advice is needed, recommend seeing a doctor or physiotherapist
- Use BJJ terminology appropriately but explain when needed
- Provide actionable advice, not just general statements

CURRENT USER DATA:
{user_context}

Now respond to the user's questions using this context. Reference their specific training data when relevant."""

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
            f"USER PROFILE:",
            f"Name: {user['first_name']} {user['last_name']}",
            f"Email: {user['email']}",
            f"",
        ]

        if total_sessions > 0:
            # Calculate training stats
            total_duration = sum(s.get("duration_mins", 0) for s in redacted_sessions)
            total_rolls = sum(s.get("rolls_count", 0) for s in redacted_sessions)
            avg_intensity = sum(s.get("intensity", 0) for s in redacted_sessions) / total_sessions

            # Get unique gyms and techniques
            gyms = set(s.get("gym", "") for s in redacted_sessions if s.get("gym"))
            all_techniques = set()
            for s in redacted_sessions:
                if s.get("techniques"):
                    all_techniques.update(s["techniques"])

            # Sessions in last 30 days
            sessions_last_30_days = [
                s for s in redacted_sessions
                if s.get("date") and self._parse_date(s["date"]) >= thirty_days_ago
            ]

            context_parts.extend([
                f"TRAINING SUMMARY:",
                f"Total sessions logged: {total_sessions}",
                f"Sessions in last 30 days: {len(sessions_last_30_days)}",
                f"Total training time: {total_duration} minutes ({total_duration / 60:.1f} hours)",
                f"Total rolls: {total_rolls}",
                f"Average intensity: {avg_intensity:.1f}/10",
                f"Gyms trained at: {', '.join(sorted(gyms)) if gyms else 'Not specified'}",
                f"Techniques practiced: {len(all_techniques)} unique techniques",
                f"",
            ])

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

                session_summary = f"- {date_str} at {gym}: {duration}min, intensity {intensity}/10"
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

            # Add recent readiness data if available
            recent_readiness = self.readiness_repo.get_recent(self.user_id, limit=7)
            if recent_readiness:
                context_parts.append("")
                context_parts.append("RECENT READINESS (last 7 days):")
                for r in recent_readiness:
                    date = r.get("date", "Unknown")
                    energy = r.get("energy_level", 0)
                    soreness = r.get("soreness_level", 0)
                    sleep = r.get("sleep_quality", 0)
                    context_parts.append(
                        f"- {date}: Energy {energy}/10, Soreness {soreness}/10, Sleep {sleep}/10"
                    )

        else:
            context_parts.append("No training sessions logged yet.")

        return "\n".join(context_parts)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        try:
            if isinstance(date_str, datetime):
                return date_str
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    def get_conversation_context(self, recent_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
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
