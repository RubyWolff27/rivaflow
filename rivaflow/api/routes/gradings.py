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
    professor: Optional[str] = None
    notes: Optional[str] = None


class GradingUpdate(BaseModel):
    """Grading update model."""
    grade: Optional[str] = None
    date_graded: Optional[str] = None
    professor: Optional[str] = None
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
            professor=grading.professor,
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


@router.put("/{grading_id}")
async def update_grading(grading_id: int, grading: GradingUpdate):
    """Update a grading by ID."""
    try:
        updated = service.update_grading(
            grading_id=grading_id,
            grade=grading.grade,
            date_graded=grading.date_graded,
            professor=grading.professor,
            notes=grading.notes,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Grading not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{grading_id}")
async def delete_grading(grading_id: int):
    """Delete a grading by ID."""
    deleted = service.delete_grading(grading_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Grading not found")
    return {"message": "Grading deleted successfully"}
