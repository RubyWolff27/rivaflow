"""Readiness and recovery analytics service."""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import statistics

from rivaflow.db.repositories import (
    SessionRepository,
    ReadinessRepository,
)


class ReadinessAnalyticsService:
    """Business logic for readiness and recovery analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()

    def get_readiness_trends(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None, types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get readiness and recovery analytics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - readiness_over_time: Daily readiness scores
            - training_load_vs_readiness: Scatter plot data
            - recovery_patterns: Day of week averages
            - injury_timeline: Hotspot tracking
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        readiness_records = self.readiness_repo.get_by_date_range(user_id, start_date, end_date)
        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date, types=types)

        # Readiness over time
        readiness_over_time = []
        for record in readiness_records:
            readiness_over_time.append({
                "date": record["check_date"].isoformat(),
                "composite_score": record["composite_score"],
                "sleep": record["sleep"],
                "stress": record["stress"],
                "soreness": record["soreness"],
                "energy": record["energy"],
            })

        # Training load vs readiness (combine sessions with readiness on same day)
        load_vs_readiness = []
        for session in sessions:
            # Find readiness for same day
            matching_readiness = next(
                (r for r in readiness_records if r["check_date"] == session["session_date"]),
                None
            )
            if matching_readiness:
                load_vs_readiness.append({
                    "date": session["session_date"].isoformat(),
                    "readiness": matching_readiness["composite_score"],
                    "intensity": session["intensity"],
                    "duration": session["duration_mins"],
                    "class_type": session["class_type"],
                })

        # Recovery patterns by day of week
        day_of_week_readiness = defaultdict(list)
        for record in readiness_records:
            day_name = record["check_date"].strftime("%A")
            day_of_week_readiness[day_name].append(record["composite_score"])

        recovery_patterns = []
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            scores = day_of_week_readiness[day]
            recovery_patterns.append({
                "day": day,
                "avg_readiness": round(statistics.mean(scores), 1) if scores else 0,
                "count": len(scores),
            })

        # Injury timeline (hotspots)
        injury_timeline = [
            {
                "date": r["check_date"].isoformat(),
                "hotspot": r.get("hotspot_note", ""),
            }
            for r in readiness_records
            if r.get("hotspot_note")
        ]

        # Weight tracking
        weight_records = [r for r in readiness_records if r.get("weight_kg") is not None]
        weight_over_time = []
        for record in weight_records:
            weight_over_time.append({
                "date": record["check_date"].isoformat(),
                "weight_kg": round(record["weight_kg"], 1),
            })

        # Calculate weight stats
        weight_stats = {}
        if weight_records:
            weights = [r["weight_kg"] for r in weight_records]
            weight_stats = {
                "has_data": True,
                "start_weight": round(weights[0], 1),
                "end_weight": round(weights[-1], 1),
                "weight_change": round(weights[-1] - weights[0], 2),
                "min_weight": round(min(weights), 1),
                "max_weight": round(max(weights), 1),
                "avg_weight": round(statistics.mean(weights), 1),
            }
        else:
            weight_stats = {
                "has_data": False,
                "start_weight": None,
                "end_weight": None,
                "weight_change": None,
                "min_weight": None,
                "max_weight": None,
                "avg_weight": None,
            }

        return {
            "readiness_over_time": readiness_over_time,
            "training_load_vs_readiness": load_vs_readiness,
            "recovery_patterns": recovery_patterns,
            "injury_timeline": injury_timeline,
            "weight_over_time": weight_over_time,
            "weight_stats": weight_stats,
        }

    def get_whoop_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None, types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get Whoop fitness tracker analytics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - strain_vs_performance: Whoop strain with submission ratio
            - heart_rate_zones: HR analysis by class type
            - calorie_burn: Calorie analysis
            - recovery_correlation: Strain vs next-day readiness
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date, types=types)
        whoop_sessions = [s for s in sessions if s.get("whoop_strain") is not None]

        # Strain vs performance
        strain_vs_performance = []
        for session in whoop_sessions:
            sub_ratio = 0
            if session["submissions_against"] > 0:
                sub_ratio = round(
                    session["submissions_for"] / session["submissions_against"], 2
                )

            strain_vs_performance.append({
                "date": session["session_date"].isoformat(),
                "strain": session.get("whoop_strain"),
                "submissions_for": session["submissions_for"],
                "submissions_against": session["submissions_against"],
                "sub_ratio": sub_ratio,
            })

        # Heart rate zones by class type
        hr_by_class = defaultdict(lambda: {"avg_hr": [], "max_hr": []})
        for session in whoop_sessions:
            if session.get("whoop_avg_hr"):
                hr_by_class[session["class_type"]]["avg_hr"].append(session["whoop_avg_hr"])
            if session.get("whoop_max_hr"):
                hr_by_class[session["class_type"]]["max_hr"].append(session["whoop_max_hr"])

        heart_rate_zones = []
        for class_type, hrs in hr_by_class.items():
            heart_rate_zones.append({
                "class_type": class_type,
                "avg_hr": round(statistics.mean(hrs["avg_hr"])) if hrs["avg_hr"] else 0,
                "max_hr": round(statistics.mean(hrs["max_hr"])) if hrs["max_hr"] else 0,
                "sessions": len(hrs["avg_hr"]),
            })

        # Calorie burn analysis
        calorie_analysis = defaultdict(lambda: {"calories": [], "duration": []})
        for session in whoop_sessions:
            if session.get("whoop_calories"):
                calorie_analysis[session["class_type"]]["calories"].append(session["whoop_calories"])
                calorie_analysis[session["class_type"]]["duration"].append(session["duration_mins"])

        calorie_burn = []
        for class_type, data in calorie_analysis.items():
            total_cals = sum(data["calories"])
            total_mins = sum(data["duration"])
            calorie_burn.append({
                "class_type": class_type,
                "total_calories": total_cals,
                "avg_calories": round(statistics.mean(data["calories"])) if data["calories"] else 0,
                "calories_per_min": round(total_cals / total_mins, 1) if total_mins > 0 else 0,
                "sessions": len(data["calories"]),
            })

        # Recovery correlation (Whoop strain vs next day readiness)
        readiness_records = self.readiness_repo.get_by_date_range(user_id, start_date, end_date)
        recovery_correlation = []

        for session in whoop_sessions:
            if session.get("whoop_strain"):
                next_day = session["session_date"] + timedelta(days=1)
                next_readiness = next(
                    (r for r in readiness_records if r["check_date"] == next_day),
                    None
                )
                if next_readiness:
                    recovery_correlation.append({
                        "date": session["session_date"].isoformat(),
                        "strain": session["whoop_strain"],
                        "next_day_readiness": next_readiness["composite_score"],
                    })

        return {
            "strain_vs_performance": strain_vs_performance,
            "heart_rate_zones": heart_rate_zones,
            "calorie_burn": calorie_burn,
            "recovery_correlation": recovery_correlation,
            "summary": {
                "total_whoop_sessions": len(whoop_sessions),
                "avg_strain": round(statistics.mean([s["whoop_strain"] for s in whoop_sessions if s.get("whoop_strain")]), 1) if whoop_sessions else 0,
                "total_calories": sum(s.get("whoop_calories", 0) for s in whoop_sessions),
            },
        }
