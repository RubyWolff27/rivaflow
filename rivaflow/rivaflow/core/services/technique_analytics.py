"""Technique mastery analytics service."""

from collections import Counter
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    GlossaryRepository,
    SessionRepository,
    SessionRollRepository,
)


class TechniqueAnalyticsService:
    """Business logic for technique mastery analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.roll_repo = SessionRollRepository()
        self.glossary_repo = GlossaryRepository()

    def get_technique_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get technique mastery analytics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - category_breakdown: Time spent on each technique category
            - stale_techniques: Techniques not trained recently
            - success_heatmap: Technique success rates over time
            - gi_vs_nogi: Technique applicability comparison
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date, types=types)
        movements = self.glossary_repo.list_all(user_id)

        # Category breakdown (count submissions by category)
        category_counts = Counter()

        # Get rolls in bulk to avoid N+1 queries
        session_ids = [session["id"] for session in sessions]
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        for session in sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    for movement_id in roll["submissions_for"]:
                        movement = self.glossary_repo.get_by_id(movement_id)
                        if movement:
                            category_counts[movement["category"]] += 1

        category_breakdown = [
            {"category": cat, "count": count} for cat, count in category_counts.items()
        ]

        # Stale techniques (movements from glossary not used in X days)
        stale_threshold_days = 30
        stale_date = date.today() - timedelta(days=stale_threshold_days)

        all_movement_ids = {m["id"] for m in movements}
        used_movement_ids = set()

        recent_sessions = self.session_repo.get_by_date_range(user_id, stale_date, date.today())

        # Get rolls in bulk to avoid N+1 queries
        recent_session_ids = [session["id"] for session in recent_sessions]
        recent_rolls_by_session = self.roll_repo.get_by_session_ids(user_id, recent_session_ids)

        for session in recent_sessions:
            rolls = recent_rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    used_movement_ids.update(roll["submissions_for"])
                if roll.get("submissions_against"):
                    used_movement_ids.update(roll["submissions_against"])

        stale_movement_ids = all_movement_ids - used_movement_ids
        stale_techniques = [
            {
                "id": m["id"],
                "name": m["name"],
                "category": m["category"],
            }
            for m in movements
            if m["id"] in stale_movement_ids
        ]

        # Gi vs No-Gi comparison
        gi_sessions = [s for s in sessions if s["class_type"] == "gi"]
        nogi_sessions = [s for s in sessions if s["class_type"] == "no-gi"]

        gi_techniques = Counter()
        nogi_techniques = Counter()

        # Use already-loaded rolls from bulk query above
        for session in gi_sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    gi_techniques.update(roll["submissions_for"])

        for session in nogi_sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    nogi_techniques.update(roll["submissions_for"])

        # Get top 10 from each
        gi_top = []
        for movement_id, count in gi_techniques.most_common(10):
            movement = self.glossary_repo.get_by_id(movement_id)
            if movement:
                gi_top.append({"name": movement["name"], "count": count})

        nogi_top = []
        for movement_id, count in nogi_techniques.most_common(10):
            movement = self.glossary_repo.get_by_id(movement_id)
            if movement:
                nogi_top.append({"name": movement["name"], "count": count})

        return {
            "category_breakdown": category_breakdown,
            "stale_techniques": stale_techniques,
            "gi_top_techniques": gi_top,
            "nogi_top_techniques": nogi_top,
            "summary": {
                "total_unique_techniques_used": len(used_movement_ids),
                "stale_count": len(stale_techniques),
            },
        }
