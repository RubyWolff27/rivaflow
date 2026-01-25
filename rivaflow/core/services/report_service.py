"""Service layer for report generation and analytics."""
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
import csv
from pathlib import Path

from rivaflow.db.repositories import SessionRepository, ReadinessRepository


class ReportService:
    """Business logic for generating training reports."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()

    def get_week_dates(self, target_date: Optional[date] = None) -> tuple[date, date]:
        """Get Monday-Sunday date range for the week containing target_date."""
        if target_date is None:
            target_date = date.today()

        # Find Monday of this week (0 = Monday, 6 = Sunday)
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)

        return monday, sunday

    def get_month_dates(self, target_date: Optional[date] = None) -> tuple[date, date]:
        """Get first and last day of the month containing target_date."""
        if target_date is None:
            target_date = date.today()

        first_day = target_date.replace(day=1)

        # Last day is first day of next month minus one day
        if target_date.month == 12:
            next_month = first_day.replace(year=target_date.year + 1, month=1)
        else:
            next_month = first_day.replace(month=target_date.month + 1)

        last_day = next_month - timedelta(days=1)

        return first_day, last_day

    def generate_report(self, start_date: date, end_date: date) -> dict:
        """Generate comprehensive report for date range."""
        sessions = self.session_repo.get_by_date_range(start_date, end_date)
        readiness_entries = self.readiness_repo.get_by_date_range(start_date, end_date)

        if not sessions:
            return {
                "start_date": start_date,
                "end_date": end_date,
                "sessions": [],
                "readiness": readiness_entries,
                "summary": self._empty_summary(),
                "breakdown_by_type": {},
                "breakdown_by_gym": {},
                "weight_tracking": self._calculate_weight_stats(readiness_entries),
            }

        return {
            "start_date": start_date,
            "end_date": end_date,
            "sessions": sessions,
            "readiness": readiness_entries,
            "summary": self._calculate_summary(sessions),
            "breakdown_by_type": self._breakdown_by_type(sessions),
            "breakdown_by_gym": self._breakdown_by_gym(sessions),
            "weight_tracking": self._calculate_weight_stats(readiness_entries),
        }

    def _empty_summary(self) -> dict:
        """Return empty summary for no data."""
        return {
            "total_classes": 0,
            "total_hours": 0.0,
            "total_rolls": 0,
            "unique_partners": 0,
            "submissions_for": 0,
            "submissions_against": 0,
            "avg_intensity": 0.0,
            "subs_per_class": 0.0,
            "subs_per_roll": 0.0,
            "taps_per_roll": 0.0,
            "sub_ratio": 0.0,
        }

    def _calculate_summary(self, sessions: list[dict]) -> dict:
        """Calculate aggregate statistics for sessions."""
        total_classes = len(sessions)
        total_mins = sum(s["duration_mins"] for s in sessions)
        total_hours = round(total_mins / 60, 1)
        total_rolls = sum(s["rolls"] for s in sessions)
        submissions_for = sum(s["submissions_for"] for s in sessions)
        submissions_against = sum(s["submissions_against"] for s in sessions)
        avg_intensity = round(
            sum(s["intensity"] for s in sessions) / total_classes, 1
        )

        # Collect unique partners
        partners_set = set()
        for session in sessions:
            if session.get("partners"):
                partners_set.update(session["partners"])
        unique_partners = len(partners_set)

        # Calculate rates
        subs_per_class = round(
            (submissions_for + submissions_against) / total_classes, 2
        ) if total_classes > 0 else 0.0

        subs_per_roll = round(
            submissions_for / total_rolls, 2
        ) if total_rolls > 0 else 0.0

        taps_per_roll = round(
            submissions_against / total_rolls, 2
        ) if total_rolls > 0 else 0.0

        sub_ratio = round(
            submissions_for / submissions_against, 2
        ) if submissions_against > 0 else float(submissions_for) if submissions_for > 0 else 0.0

        return {
            "total_classes": total_classes,
            "total_hours": total_hours,
            "total_rolls": total_rolls,
            "unique_partners": unique_partners,
            "submissions_for": submissions_for,
            "submissions_against": submissions_against,
            "avg_intensity": avg_intensity,
            "subs_per_class": subs_per_class,
            "subs_per_roll": subs_per_roll,
            "taps_per_roll": taps_per_roll,
            "sub_ratio": sub_ratio,
        }

    def _breakdown_by_type(self, sessions: list[dict]) -> dict:
        """Break down statistics by class type."""
        by_type = defaultdict(lambda: {"classes": 0, "hours": 0.0, "rolls": 0})

        for session in sessions:
            class_type = session["class_type"]
            by_type[class_type]["classes"] += 1
            by_type[class_type]["hours"] += round(session["duration_mins"] / 60, 1)
            by_type[class_type]["rolls"] += session["rolls"]

        return dict(by_type)

    def _breakdown_by_gym(self, sessions: list[dict]) -> dict:
        """Break down statistics by gym."""
        by_gym = defaultdict(int)

        for session in sessions:
            by_gym[session["gym_name"]] += 1

        return dict(by_gym)

    def _calculate_weight_stats(self, readiness_entries: list[dict]) -> dict:
        """Calculate weight tracking statistics from readiness data."""
        # Filter entries with weight data
        weight_entries = [
            {"date": r["check_date"], "weight_kg": r["weight_kg"]}
            for r in readiness_entries
            if r.get("weight_kg") is not None
        ]

        if not weight_entries:
            return {
                "has_data": False,
                "start_weight": None,
                "end_weight": None,
                "weight_change": None,
                "min_weight": None,
                "max_weight": None,
                "avg_weight": None,
                "entries": [],
            }

        # Sort by date (oldest to newest)
        weight_entries.sort(key=lambda x: x["date"])

        weights = [e["weight_kg"] for e in weight_entries]
        start_weight = weights[0]
        end_weight = weights[-1]
        weight_change = round(end_weight - start_weight, 2)

        return {
            "has_data": True,
            "start_weight": round(start_weight, 1),
            "end_weight": round(end_weight, 1),
            "weight_change": weight_change,
            "min_weight": round(min(weights), 1),
            "max_weight": round(max(weights), 1),
            "avg_weight": round(sum(weights) / len(weights), 1),
            "entries": weight_entries,
        }

    def export_to_csv(
        self, sessions: list[dict], output_path: str
    ) -> None:
        """Export sessions to CSV file."""
        if not sessions:
            return

        # Define CSV columns
        fieldnames = [
            "date",
            "class_type",
            "gym_name",
            "location",
            "duration_mins",
            "intensity",
            "rolls",
            "submissions_for",
            "submissions_against",
            "partners",
            "techniques",
            "notes",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for session in sessions:
                row = {
                    "date": session["session_date"],
                    "class_type": session["class_type"],
                    "gym_name": session["gym_name"],
                    "location": session.get("location", ""),
                    "duration_mins": session["duration_mins"],
                    "intensity": session["intensity"],
                    "rolls": session["rolls"],
                    "submissions_for": session["submissions_for"],
                    "submissions_against": session["submissions_against"],
                    "partners": ", ".join(session["partners"]) if session.get("partners") else "",
                    "techniques": ", ".join(session["techniques"]) if session.get("techniques") else "",
                    "notes": session.get("notes", ""),
                }
                writer.writerow(row)
