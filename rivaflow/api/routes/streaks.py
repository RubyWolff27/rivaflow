"""API routes for streak tracking."""
from fastapi import APIRouter
from rivaflow.core.services.streak_service import StreakService

router = APIRouter(prefix="/streaks", tags=["streaks"])


@router.get("/status")
def get_streak_status():
    """Get all streak status (checkin, training, readiness)."""
    service = StreakService()
    status = service.get_streak_status()

    return {
        "checkin": status["checkin"],
        "training": status["training"],
        "readiness": status["readiness"],
        "any_at_risk": status.get("any_at_risk", False),
    }


@router.get("/{streak_type}")
def get_streak(streak_type: str):
    """Get specific streak details."""
    if streak_type not in ["checkin", "training", "readiness"]:
        return {"error": "Invalid streak type"}, 400

    service = StreakService()
    streak = service.get_streak(streak_type)

    return streak
