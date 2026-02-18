"""Service for computing per-session Strava-like insights."""

from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import SessionRepository, SessionRollRepository
from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository


class SessionInsightService:
    """Compute insights for individual training sessions."""

    # Partner roll milestones worth celebrating
    PARTNER_MILESTONES = [1, 10, 25, 50, 100, 250, 500]

    # Technique session milestones
    TECHNIQUE_MILESTONES = [1, 5, 10, 25, 50, 100]

    def __init__(self):
        self.session_repo = SessionRepository()
        self.roll_repo = SessionRollRepository()
        self.technique_repo = SessionTechniqueRepository()

    def get_session_insights(self, user_id: int, session_id: int) -> dict[str, Any]:
        """Generate insights for a specific session."""
        session = self.session_repo.get_by_id(user_id, session_id)
        if not session:
            return {"insights": []}

        insights: list[dict[str, str]] = []

        insights.extend(self._check_new_techniques(user_id, session_id))
        insights.extend(self._check_technique_depth(user_id, session_id))
        insights.extend(self._check_partner_milestones(user_id, session_id, session))
        insights.extend(self._check_personal_records(user_id, session))
        insights.extend(self._check_streak(user_id, session))

        return {"insights": insights}

    def _check_new_techniques(
        self, user_id: int, session_id: int
    ) -> list[dict[str, str]]:
        """Check if any technique in this session was trained for the first time."""
        insights = []
        new_techs = SessionRepository.get_new_techniques_for_session(
            user_id, session_id
        )
        for tech in new_techs:
            insights.append(
                {
                    "type": "new_technique",
                    "title": "New Technique!",
                    "description": f"First time training {tech['name']}",
                    "icon": "star",
                }
            )
        return insights

    def _check_technique_depth(
        self, user_id: int, session_id: int
    ) -> list[dict[str, str]]:
        """Check if techniques hit session-count milestones."""
        insights = []
        session_techs = SessionRepository.get_session_techniques_with_names(
            user_id, session_id
        )

        for tech in session_techs:
            count = tech["session_count"]

            # Check milestones (skip 1 since new_technique covers that)
            for milestone in self.TECHNIQUE_MILESTONES:
                if milestone == 1:
                    continue
                if count == milestone:
                    insights.append(
                        {
                            "type": "technique_depth",
                            "title": f"{tech['name']} x{milestone}",
                            "description": (
                                f"You've trained {tech['name']}"
                                f" in {milestone} sessions"
                            ),
                            "icon": "target",
                        }
                    )
        return insights

    def _check_partner_milestones(
        self, user_id: int, session_id: int, session: dict
    ) -> list[dict[str, str]]:
        """Check if any partner hit a roll count milestone."""
        insights = []

        # Check detailed rolls
        rolls = self.roll_repo.get_by_session_id(user_id, session_id)
        partner_names_checked: set[str] = set()

        for roll in rolls:
            partner_name = roll.get("partner_name", "")
            partner_id = roll.get("partner_id")
            if not partner_name or partner_name in partner_names_checked:
                continue
            partner_names_checked.add(partner_name)

            total = SessionRepository.count_rolls_with_partner(
                user_id, partner_id, partner_name
            )
            for milestone in self.PARTNER_MILESTONES:
                if total == milestone:
                    if milestone == 1:
                        insights.append(
                            {
                                "type": "partner_milestone",
                                "title": "First Roll!",
                                "description": (
                                    f"First time rolling with {partner_name}"
                                ),
                                "icon": "users",
                            }
                        )
                    else:
                        insights.append(
                            {
                                "type": "partner_milestone",
                                "title": f"{milestone} Rolls!",
                                "description": (
                                    f"You've hit {milestone} rolls with"
                                    f" {partner_name}"
                                ),
                                "icon": "trophy",
                            }
                        )

        # Also check simple partners list for first-time mentions
        simple_partners = session.get("partners", []) or []
        for partner_name in simple_partners:
            if partner_name in partner_names_checked:
                continue
            partner_names_checked.add(partner_name)
            count = SessionRepository.count_partner_sessions(user_id, partner_name)
            if count == 1:
                insights.append(
                    {
                        "type": "partner_milestone",
                        "title": "New Training Partner!",
                        "description": (f"First session with {partner_name}"),
                        "icon": "users",
                    }
                )

        return insights

    def _check_personal_records(
        self, user_id: int, session: dict
    ) -> list[dict[str, str]]:
        """Check if this session set any personal records."""
        insights = []
        session_date = session.get("session_date")
        if isinstance(session_date, str):
            session_date = date.fromisoformat(session_date)

        # Most rolls in a single session (all time)
        rolls = session.get("rolls", 0) or 0
        if rolls > 0:
            prev_max = SessionRepository.get_max_rolls_excluding(user_id, session["id"])
            if rolls > prev_max and prev_max > 0:
                insights.append(
                    {
                        "type": "personal_record",
                        "title": "Most Rolls!",
                        "description": (
                            f"New all-time record: {rolls} rolls" f" (prev: {prev_max})"
                        ),
                        "icon": "trophy",
                    }
                )

        # Longest session (all time)
        duration = session.get("duration_mins", 0) or 0
        if duration > 0:
            prev_max = SessionRepository.get_max_duration_excluding(
                user_id, session["id"]
            )
            if duration > prev_max and prev_max > 0:
                insights.append(
                    {
                        "type": "personal_record",
                        "title": "Longest Session!",
                        "description": (
                            f"New record: {duration} minutes" f" (prev: {prev_max})"
                        ),
                        "icon": "trophy",
                    }
                )

        # Submissions highlight (min 2 rolls)
        subs_for = session.get("submissions_for", 0) or 0
        if subs_for > 0 and rolls >= 2:
            insights.append(
                {
                    "type": "personal_record",
                    "title": f"{subs_for} Submissions!",
                    "description": (f"You submitted {subs_for} time(s) this session"),
                    "icon": "zap",
                }
            )

        return insights

    def _check_streak(self, user_id: int, session: dict) -> list[dict[str, str]]:
        """Check training streak at the time of this session."""
        insights = []
        session_date = session.get("session_date")
        if isinstance(session_date, str):
            session_date = date.fromisoformat(session_date)

        # Count consecutive days with sessions ending at this date
        streak = 0
        check_date = session_date
        while True:
            count = SessionRepository.count_sessions_on_date(
                user_id, check_date.isoformat()
            )
            if count > 0:
                streak += 1
                check_date = check_date - timedelta(days=1)
            else:
                break

        streak_milestones = [3, 5, 7, 10, 14, 21, 30, 60, 90]
        for milestone in streak_milestones:
            if streak == milestone:
                insights.append(
                    {
                        "type": "streak",
                        "title": f"{streak}-Day Streak!",
                        "description": (f"You've trained {streak} days in a row"),
                        "icon": "flame",
                    }
                )

        return insights
