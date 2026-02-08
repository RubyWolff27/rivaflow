"""Technique mastery analytics service."""

from collections import Counter
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    GlossaryRepository,
    SessionRepository,
)
from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository


class TechniqueAnalyticsService:
    """Business logic for technique mastery analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.glossary_repo = GlossaryRepository()
        self.technique_repo = SessionTechniqueRepository()

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
            types: Optional list of class types to filter by

        Returns:
            - category_breakdown: Techniques used by category
            - all_techniques: All techniques with counts (for heatmap)
            - stale_techniques: Techniques not trained recently
            - gi_top_techniques / nogi_top_techniques: Gi vs no-gi split
            - summary: Aggregate counts
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

        # Build movement lookup
        movements = self.glossary_repo.list_all()
        movement_map = {m["id"]: m for m in movements}

        # Get session_techniques in bulk
        session_ids = [s["id"] for s in sessions]
        techs_by_session = self.technique_repo.batch_get_by_session_ids(session_ids)

        # Build session lookup for class_type filtering
        session_map = {s["id"]: s for s in sessions}

        # Count techniques by category and movement
        category_counts: Counter = Counter()
        technique_counts: Counter = Counter()
        gi_techniques: Counter = Counter()
        nogi_techniques: Counter = Counter()
        used_movement_ids: set[int] = set()

        for session_id, techs in techs_by_session.items():
            session = session_map.get(session_id)
            if not session:
                continue

            class_type = session.get("class_type", "")

            for tech in techs:
                mid = tech.get("movement_id")
                if not mid:
                    continue

                movement = movement_map.get(mid)
                if not movement:
                    continue

                used_movement_ids.add(mid)
                technique_counts[mid] += 1
                category_counts[movement.get("category", "other")] += 1

                if class_type == "gi":
                    gi_techniques[mid] += 1
                elif class_type == "no-gi":
                    nogi_techniques[mid] += 1

        # Category breakdown
        category_breakdown = [
            {"category": cat, "count": count} for cat, count in category_counts.items()
        ]

        # All techniques (for heatmap)
        all_techniques = []
        for mid, count in technique_counts.most_common():
            movement = movement_map.get(mid)
            if movement:
                all_techniques.append(
                    {
                        "name": movement["name"],
                        "category": movement.get("category", "other"),
                        "count": count,
                    }
                )

        # Gi vs No-Gi top techniques
        gi_top = []
        for mid, count in gi_techniques.most_common(10):
            movement = movement_map.get(mid)
            if movement:
                gi_top.append({"name": movement["name"], "count": count})

        nogi_top = []
        for mid, count in nogi_techniques.most_common(10):
            movement = movement_map.get(mid)
            if movement:
                nogi_top.append({"name": movement["name"], "count": count})

        # Stale techniques (trained before but not in last 30 days)
        stale_threshold_days = 30
        stale_date = date.today() - timedelta(days=stale_threshold_days)

        recent_sessions = self.session_repo.get_by_date_range(
            user_id, stale_date, date.today()
        )
        recent_ids = [s["id"] for s in recent_sessions]
        recent_techs = self.technique_repo.batch_get_by_session_ids(recent_ids)

        recently_used: set[int] = set()
        for techs in recent_techs.values():
            for tech in techs:
                mid = tech.get("movement_id")
                if mid:
                    recently_used.add(mid)

        # Stale = ever trained but not recently
        all_ever_trained = set(technique_counts.keys())
        stale_ids = all_ever_trained - recently_used
        stale_techniques = [
            {
                "id": mid,
                "name": movement_map[mid]["name"],
                "category": movement_map[mid].get("category", "other"),
            }
            for mid in stale_ids
            if mid in movement_map
        ]

        return {
            "category_breakdown": category_breakdown,
            "all_techniques": all_techniques,
            "stale_techniques": stale_techniques,
            "gi_top_techniques": gi_top,
            "nogi_top_techniques": nogi_top,
            "summary": {
                "total_unique_techniques_used": len(used_movement_ids),
                "stale_count": len(stale_techniques),
            },
        }
