"""Coach preferences endpoints for Grapple AI personalization."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.coach_preferences_service import (
    CoachPreferencesService,
)

router = APIRouter()

VALID_TRAINING_MODES = {
    "competition_prep",
    "lifestyle",
    "skill_development",
    "recovery",
}
VALID_COACHING_STYLES = {
    "balanced",
    "motivational",
    "analytical",
    "tough_love",
    "technical",
}
VALID_POSITIONS = {"top", "bottom", "both"}
VALID_COMP_EXPERIENCE = {"none", "beginner", "regular", "active"}
VALID_BELT_LEVELS = {"white", "blue", "purple", "brown", "black"}
VALID_COMPETITION_RULESETS = {"none", "ibjjf", "adcc", "sub_only", "naga", "other"}


VALID_INJURY_STATUSES = {"active", "recovered", "managing"}


class Injury(BaseModel):
    """A persistent injury entry."""

    area: str
    side: str = "n/a"
    severity: str = "moderate"
    notes: str | None = None
    status: str = "active"
    resolved_date: str | None = None
    start_date: str | None = None


class CoachPreferencesUpdate(BaseModel):
    """Coach preferences update model."""

    belt_level: str | None = None
    competition_ruleset: str | None = None
    training_mode: str | None = None
    comp_date: str | None = None
    comp_name: str | None = None
    comp_division: str | None = None
    comp_weight_class: str | None = None
    coaching_style: str | None = None
    primary_position: str | None = None
    focus_areas: list[str] | None = None
    weaknesses: str | None = None
    injuries: list[Injury] | None = None
    training_start_date: str | None = None
    years_training: float | None = None
    competition_experience: str | None = None
    available_days_per_week: int | None = None
    motivations: list[str] | None = None
    additional_context: str | None = None
    gi_nogi_preference: str | None = None
    gi_bias_pct: int | None = None


DEFAULTS = {
    "belt_level": "white",
    "competition_ruleset": "none",
    "training_mode": "lifestyle",
    "coaching_style": "balanced",
    "primary_position": "both",
    "focus_areas": [],
    "injuries": [],
    "motivations": [],
    "competition_experience": "none",
    "available_days_per_week": 4,
    "comp_date": None,
    "comp_name": None,
    "comp_division": None,
    "comp_weight_class": None,
    "weaknesses": None,
    "training_start_date": None,
    "years_training": None,
    "additional_context": None,
}


@router.get("/")
@limiter.limit("60/minute")
@route_error_handler("get_preferences", detail="Failed to get coach preferences")
def get_preferences(request: Request, current_user: dict = Depends(get_current_user)):
    """Get coach preferences for the current user."""
    prefs = CoachPreferencesService().get(current_user["id"])
    if not prefs:
        return {"data": {**DEFAULTS}}
    # Strip internal fields
    prefs.pop("id", None)
    prefs.pop("user_id", None)
    prefs.pop("created_at", None)
    prefs.pop("updated_at", None)
    return {"data": prefs}


@router.put("/")
@limiter.limit("30/minute")
@route_error_handler("update_preferences", detail="Failed to update coach preferences")
def update_preferences(
    body: CoachPreferencesUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Create or update coach preferences."""
    fields = body.model_dump(exclude_none=True)

    # Validate enums
    if (
        "training_mode" in fields
        and fields["training_mode"] not in VALID_TRAINING_MODES
    ):
        return {
            "error": f"Invalid training_mode. Must be one of: {VALID_TRAINING_MODES}"
        }
    if (
        "coaching_style" in fields
        and fields["coaching_style"] not in VALID_COACHING_STYLES
    ):
        return {
            "error": f"Invalid coaching_style. Must be one of: {VALID_COACHING_STYLES}"
        }
    if (
        "primary_position" in fields
        and fields["primary_position"] not in VALID_POSITIONS
    ):
        return {"error": f"Invalid primary_position. Must be one of: {VALID_POSITIONS}"}
    if (
        "competition_experience" in fields
        and fields["competition_experience"] not in VALID_COMP_EXPERIENCE
    ):
        return {
            "error": f"Invalid competition_experience. Must be one of: {VALID_COMP_EXPERIENCE}"
        }
    if "belt_level" in fields and fields["belt_level"] not in VALID_BELT_LEVELS:
        return {"error": f"Invalid belt_level. Must be one of: {VALID_BELT_LEVELS}"}
    if (
        "competition_ruleset" in fields
        and fields["competition_ruleset"] not in VALID_COMPETITION_RULESETS
    ):
        return {
            "error": (
                "Invalid competition_ruleset. "
                f"Must be one of: {VALID_COMPETITION_RULESETS}"
            )
        }
    if "available_days_per_week" in fields:
        fields["available_days_per_week"] = max(
            1, min(7, fields["available_days_per_week"])
        )

    # Serialize injuries list of dicts
    if "injuries" in fields:
        fields["injuries"] = [
            inj.model_dump() if hasattr(inj, "model_dump") else inj
            for inj in fields["injuries"]
        ]

    result = CoachPreferencesService().upsert(current_user["id"], **fields)
    if result:
        result.pop("id", None)
        result.pop("user_id", None)
        result.pop("created_at", None)
        result.pop("updated_at", None)
    return {"data": result}
