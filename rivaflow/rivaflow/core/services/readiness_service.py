"""Service layer for readiness check-in operations."""

from datetime import date

from rivaflow.db.repositories import ReadinessRepository
from rivaflow.db.repositories.checkin_repo import CheckinRepository


class ReadinessService:
    """Business logic for daily readiness check-ins."""

    def __init__(self):
        self.repo = ReadinessRepository()
        self.checkin_repo = CheckinRepository()

    def log_readiness(
        self,
        user_id: int,
        check_date: date,
        sleep: int,
        stress: int,
        soreness: int,
        energy: int,
        hotspot_note: str | None = None,
        weight_kg: float | None = None,
    ) -> int:
        """
        Log daily readiness check-in (upsert if exists for date).
        Returns readiness ID.
        """
        readiness_id = self.repo.upsert(
            user_id=user_id,
            check_date=check_date,
            sleep=sleep,
            stress=stress,
            soreness=soreness,
            energy=energy,
            hotspot_note=hotspot_note,
            weight_kg=weight_kg,
        )

        # Create check-in record for this readiness entry
        self.checkin_repo.upsert_checkin(
            user_id=user_id,
            check_date=check_date,
            checkin_type="readiness",
            readiness_id=readiness_id,
        )

        return readiness_id

    def get_readiness(self, user_id: int, check_date: date) -> dict | None:
        """Get readiness entry for a specific date."""
        return self.repo.get_by_date(user_id, check_date)

    def get_latest_readiness(self, user_id: int) -> dict | None:
        """Get the most recent readiness entry."""
        return self.repo.get_latest(user_id)

    def get_readiness_range(self, user_id: int, start_date: date, end_date: date) -> list[dict]:
        """Get readiness entries within a date range."""
        return self.repo.get_by_date_range(user_id, start_date, end_date)

    def log_weight_only(self, user_id: int, check_date: date, weight_kg: float) -> int:
        """
        Log weight only for a date. If readiness exists, updates weight.
        If not, creates entry with default middle values (3) for readiness scores.
        Returns readiness ID.
        """
        # Check if entry exists for this date
        existing = self.repo.get_by_date(user_id, check_date)

        if existing:
            # Update existing entry with new weight
            readiness_id = self.repo.upsert(
                user_id=user_id,
                check_date=check_date,
                sleep=existing["sleep"],
                stress=existing["stress"],
                soreness=existing["soreness"],
                energy=existing["energy"],
                hotspot_note=existing.get("hotspot_note"),
                weight_kg=weight_kg,
            )
        else:
            # Create new entry with default middle values (3) for scores
            readiness_id = self.repo.upsert(
                user_id=user_id,
                check_date=check_date,
                sleep=3,
                stress=3,
                soreness=3,
                energy=3,
                hotspot_note=None,
                weight_kg=weight_kg,
            )

        # Create check-in record for this readiness entry
        self.checkin_repo.upsert_checkin(
            user_id=user_id,
            check_date=check_date,
            checkin_type="readiness",
            readiness_id=readiness_id,
        )

        return readiness_id

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
