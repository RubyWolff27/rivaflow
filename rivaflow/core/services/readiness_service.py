"""Service layer for readiness check-in operations."""
from datetime import date
from typing import Optional

from rivaflow.db.repositories import ReadinessRepository


class ReadinessService:
    """Business logic for daily readiness check-ins."""

    def __init__(self):
        self.repo = ReadinessRepository()

    def log_readiness(
        self,
        check_date: date,
        sleep: int,
        stress: int,
        soreness: int,
        energy: int,
        hotspot_note: Optional[str] = None,
    ) -> int:
        """
        Log daily readiness check-in (upsert if exists for date).
        Returns readiness ID.
        """
        return self.repo.upsert(
            check_date=check_date,
            sleep=sleep,
            stress=stress,
            soreness=soreness,
            energy=energy,
            hotspot_note=hotspot_note,
        )

    def get_readiness(self, check_date: date) -> Optional[dict]:
        """Get readiness entry for a specific date."""
        return self.repo.get_by_date(check_date)

    def get_latest_readiness(self) -> Optional[dict]:
        """Get the most recent readiness entry."""
        return self.repo.get_latest()

    def get_readiness_range(self, start_date: date, end_date: date) -> list[dict]:
        """Get readiness entries within a date range."""
        return self.repo.get_by_date_range(start_date, end_date)

    def calculate_composite_score(self, readiness: dict) -> int:
        """Calculate composite readiness score (4-20 range, higher is better)."""
        return (
            readiness["sleep"]
            + (6 - readiness["stress"])
            + (6 - readiness["soreness"])
            + readiness["energy"]
        )

    def get_score_label(self, score: int) -> str:
        """Get human-readable label for a composite score."""
        if score >= 17:
            return "Excellent"
        elif score >= 14:
            return "Good"
        elif score >= 11:
            return "Moderate"
        elif score >= 8:
            return "Low"
        else:
            return "Very Low"

    def format_readiness_summary(self, readiness: dict) -> str:
        """Format readiness as a human-readable summary."""
        score = self.calculate_composite_score(readiness)
        label = self.get_score_label(score)

        # Create bar charts for each metric
        sleep_bar = "█" * readiness["sleep"] + "░" * (5 - readiness["sleep"])
        stress_bar = "█" * readiness["stress"] + "░" * (5 - readiness["stress"])
        soreness_bar = "█" * readiness["soreness"] + "░" * (5 - readiness["soreness"])
        energy_bar = "█" * readiness["energy"] + "░" * (5 - readiness["energy"])

        lines = [
            f"✓ Readiness logged: {readiness['check_date']}",
            f"  Score: {score}/20 ({label})",
            f"  Sleep: {sleep_bar} {readiness['sleep']}  Stress: {stress_bar} {readiness['stress']}",
            f"  Soreness: {soreness_bar} {readiness['soreness']}  Energy: {energy_bar} {readiness['energy']}",
        ]

        if readiness.get("hotspot_note"):
            lines.append(f"  Hotspot: {readiness['hotspot_note']}")

        return "\n".join(lines)
