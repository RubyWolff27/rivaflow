"""Grading/belt progression endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.grading_service import GradingService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter()
service = GradingService()


class GradingCreate(BaseModel):
    """Grading creation model."""
    grade: str
    date_graded: str
    professor: Optional[str] = None
    notes: Optional[str] = None


class GradingUpdate(BaseModel):
    """Grading update model."""
    grade: Optional[str] = None
    date_graded: Optional[str] = None
    professor: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_gradings(current_user: dict = Depends(get_current_user)):
    """Get all gradings, ordered by date (newest first)."""
    gradings = service.list_gradings(user_id=current_user["id"])
    return gradings


@router.post("/")
async def create_grading(grading: GradingCreate, current_user: dict = Depends(get_current_user)):
    """Create a new grading and update the profile's current_grade."""
    created = service.create_grading(
        user_id=current_user["id"],
        grade=grading.grade,
        date_graded=grading.date_graded,
        professor=grading.professor,
        notes=grading.notes,
    )
    return created


@router.get("/latest")
async def get_latest_grading(current_user: dict = Depends(get_current_user)):
    """Get the most recent grading."""
    grading = service.get_latest_grading(user_id=current_user["id"])
    if not grading:
        return None
    return grading


@router.put("/{grading_id}")
async def update_grading(grading_id: int, grading: GradingUpdate, current_user: dict = Depends(get_current_user)):
    """Update a grading by ID."""
    try:
        updated = service.update_grading(
            user_id=current_user["id"],
            grading_id=grading_id,
            grade=grading.grade,
            date_graded=grading.date_graded,
            professor=grading.professor,
            notes=grading.notes,
        )
        if not updated:
            raise NotFoundError("Grading not found")
        return updated
    except HTTPException:
        raise


@router.delete("/{grading_id}")
async def delete_grading(grading_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a grading by ID."""
    deleted = service.delete_grading(user_id=current_user["id"], grading_id=grading_id)
    if not deleted:
        raise NotFoundError("Grading not found")
    return {"message": "Grading deleted successfully"}
