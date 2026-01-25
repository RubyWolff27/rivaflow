"""Grading/belt progression endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.grading_service import GradingService

router = APIRouter()
service = GradingService()


class GradingCreate(BaseModel):
    """Grading creation model."""
    grade: str
    date_graded: str
    notes: Optional[str] = None


@router.get("/")
async def list_gradings():
    """Get all gradings, ordered by date (newest first)."""
    gradings = service.list_gradings()
    return gradings


@router.post("/")
async def create_grading(grading: GradingCreate):
    """Create a new grading and update the profile's current_grade."""
    try:
        created = service.create_grading(
            grade=grading.grade,
            date_graded=grading.date_graded,
            notes=grading.notes,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_grading():
    """Get the most recent grading."""
    grading = service.get_latest_grading()
    if not grading:
        return None
    return grading


@router.delete("/{grading_id}")
async def delete_grading(grading_id: int):
    """Delete a grading by ID."""
    deleted = service.delete_grading(grading_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Grading not found")
    return {"message": "Grading deleted successfully"}
