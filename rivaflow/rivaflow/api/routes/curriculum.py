"""Belt-curriculum endpoints — declared slate, evidence, coach sign-off, export.

Note what is absent: there is no route that sets a slot's status, and no route
that updates or deletes a sign-off. Status is derived by
``CurriculumService.compute_slot_state``; sign-offs are immutable attributed
records. Both omissions are the feature.
"""

import logging

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user, get_curriculum_service
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.curriculum_service import CurriculumService

logger = logging.getLogger(__name__)


def _set_curriculum_cache_control(response: Response):
    """Set Cache-Control for curriculum GET endpoints (private, 60s)."""
    response.headers["Cache-Control"] = "private, max-age=60"


router = APIRouter(dependencies=[Depends(_set_curriculum_cache_control)])


class SlotDeclaration(BaseModel):
    """Declare or edit a slot's sequence: entry -> position -> finish."""

    seq_entry: str | None = None
    seq_position: str | None = None
    seq_finish: str | None = None
    game_tag: str | None = Field(None, description="a-game | b-game | syllabus-only")
    movement_ids: str | None = Field(
        None, description="JSON array of glossary movement ids"
    )
    is_draft: bool | None = None
    tension_note: str | None = None
    blocker_note: str | None = None


class SlotCreate(SlotDeclaration):
    """Create an extra slot beyond the seeded syllabus shape."""

    block: str
    requirement_key: str
    requirement_label: str | None = None
    slot_index: int
    of_choice: bool = True
    belt: str = "purple"


class EvidenceCreate(BaseModel):
    """Log drilled or live evidence against a slot."""

    kind: str = Field(..., description="drilled | live")
    session_id: int | None = None
    partner_ref: str | None = Field(
        None, description="Stable partner identifier; falls back to rank+size"
    )
    partner_rank_band: str | None = Field(
        None, description="lower | same | higher (relative to me)"
    )
    partner_size: str | None = Field(
        None, description="smaller | similar | bigger (relative to me)"
    )
    note: str | None = None
    logged_at: str | None = Field(None, description="ISO date; defaults to today")


class SignoffCreate(BaseModel):
    """A coach's verdict on a slot. Create-only, never editable."""

    verdict: str = Field(..., description="verified | not-yet | show-me")
    coach_name: str
    coach_rank: str | None = None
    note: str | None = None


class MetaUpdate(BaseModel):
    """The hard gates that actually decide the belt."""

    competition_date: str | None = None
    competition_note: str | None = None
    classes_logged: int | None = None
    stripes: int | None = None
    notes: str | None = None


@router.get("/slots")
@limiter.limit("60/minute")
@route_error_handler("curriculum slots", detail="Failed to load curriculum slots")
def get_slots(
    request: Request,
    belt: str = Query("purple"),
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Full slate with a status computed per slot from evidence and sign-offs."""
    return service.get_slots(user_id=current_user["id"], belt=belt)


@router.post("/slots")
@limiter.limit("30/minute")
@route_error_handler("curriculum slot create", detail="Failed to create slot")
def create_slot(
    request: Request,
    payload: SlotCreate,
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Declare an extra slot beyond the seeded syllabus shape."""
    return service.create_slot(
        user_id=current_user["id"], payload=payload.model_dump(exclude_unset=True)
    )


@router.put("/slots/{slot_id}")
@limiter.limit("30/minute")
@route_error_handler("curriculum slot update", detail="Failed to update slot")
def update_slot(
    request: Request,
    slot_id: int,
    payload: SlotDeclaration,
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Edit a slot's declared sequence, game tag, or notes."""
    return service.update_slot(
        user_id=current_user["id"],
        slot_id=slot_id,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.post("/slots/{slot_id}/evidence")
@limiter.limit("60/minute")
@route_error_handler("curriculum evidence", detail="Failed to log evidence")
def add_evidence(
    request: Request,
    slot_id: int,
    payload: EvidenceCreate,
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Log drilled or live evidence. This is the only way a status can move."""
    return service.add_evidence(
        user_id=current_user["id"],
        slot_id=slot_id,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.post("/slots/{slot_id}/signoff")
@limiter.limit("30/minute")
@route_error_handler("curriculum signoff", detail="Failed to record sign-off")
def add_signoff(
    request: Request,
    slot_id: int,
    payload: SignoffCreate,
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Record a coach sign-off.

    Create-only by design — there is no update or delete route. A changed
    verdict is a new row, and the history keeps both.
    """
    return service.add_signoff(
        user_id=current_user["id"],
        slot_id=slot_id,
        payload=payload.model_dump(exclude_unset=True),
    )


@router.get("/summary")
@limiter.limit("60/minute")
@route_error_handler("curriculum summary", detail="Failed to load curriculum summary")
def get_summary(
    request: Request,
    belt: str = Query("purple"),
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Per-block status counts, hard gates, and the radar's raw a/b-game counts."""
    return service.get_summary(user_id=current_user["id"], belt=belt)


@router.get("/export")
@limiter.limit("30/minute")
@route_error_handler("curriculum export", detail="Failed to build curriculum export")
def get_export(
    request: Request,
    belt: str = Query("purple"),
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Gap-first coach view: hard gates, then not-yet before in-progress before
    verified. Carries no percentage or completion score anywhere."""
    return service.get_export(user_id=current_user["id"], belt=belt)


@router.put("/meta")
@limiter.limit("30/minute")
@route_error_handler("curriculum meta", detail="Failed to update hard gates")
def update_meta(
    request: Request,
    payload: MetaUpdate,
    belt: str = Query("purple"),
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Set the hard gates: competition date, class count, stripes, notes."""
    return service.upsert_meta(
        user_id=current_user["id"],
        payload=payload.model_dump(exclude_unset=True),
        belt=belt,
    )


@router.post("/seed")
@limiter.limit("5/minute")
@route_error_handler("curriculum seed", detail="Failed to seed curriculum")
def seed_curriculum(
    request: Request,
    with_draft: bool = Query(
        False, description="Attach Ruby's DRAFT slate to the of-choice slots"
    ),
    belt: str = Query("purple"),
    current_user: dict = Depends(get_current_user),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Create the syllabus slots for the current user. No-op when already seeded."""
    return service.seed_user(
        user_id=current_user["id"], with_draft=with_draft, belt=belt
    )
