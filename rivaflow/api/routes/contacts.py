"""Contacts (training partners and instructors) endpoints."""
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.contact_service import ContactService
from rivaflow.core.dependencies import get_current_user

router = APIRouter()
service = ContactService()


class ContactCreate(BaseModel):
    """Contact creation model."""
    name: str
    contact_type: str = "training-partner"
    belt_rank: Optional[str] = None
    belt_stripes: int = 0
    instructor_certification: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    """Contact update model."""
    name: Optional[str] = None
    contact_type: Optional[str] = None
    belt_rank: Optional[str] = None
    belt_stripes: Optional[int] = None
    instructor_certification: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_contacts(
    search: Optional[str] = Query(None, description="Search by name"),
    contact_type: Optional[str] = Query(None, description="Filter by contact type"),
    current_user: dict = Depends(get_current_user),
):
    """Get all contacts with optional filtering."""
    if search:
        contacts = service.search_contacts(user_id=current_user["id"], search=search)
    elif contact_type:
        contacts = service.repo.list_by_type(user_id=current_user["id"], contact_type=contact_type)
    else:
        contacts = service.list_contacts(user_id=current_user["id"])
    return contacts


@router.get("/instructors")
async def list_instructors(current_user: dict = Depends(get_current_user)):
    """Get all contacts who are instructors."""
    instructors = service.list_instructors(user_id=current_user["id"])
    return instructors


@router.get("/partners")
async def list_training_partners(current_user: dict = Depends(get_current_user)):
    """Get all contacts who are training partners."""
    partners = service.list_training_partners(user_id=current_user["id"])
    return partners


@router.get("/{contact_id}")
async def get_contact(contact_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific contact by ID."""
    contact = service.get_contact(user_id=current_user["id"], contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/")
async def create_contact(contact: ContactCreate, current_user: dict = Depends(get_current_user)):
    """Create a new contact."""
    try:
        created = service.create_contact(
            user_id=current_user["id"],
            name=contact.name,
            contact_type=contact.contact_type,
            belt_rank=contact.belt_rank,
            belt_stripes=contact.belt_stripes,
            instructor_certification=contact.instructor_certification,
            phone=contact.phone,
            email=contact.email,
            notes=contact.notes,
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{contact_id}")
async def update_contact(contact_id: int, contact: ContactUpdate, current_user: dict = Depends(get_current_user)):
    """Update a contact."""
    try:
        updated = service.update_contact(
            user_id=current_user["id"],
            contact_id=contact_id,
            name=contact.name,
            contact_type=contact.contact_type,
            belt_rank=contact.belt_rank,
            belt_stripes=contact.belt_stripes,
            instructor_certification=contact.instructor_certification,
            phone=contact.phone,
            email=contact.email,
            notes=contact.notes,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Contact not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a contact."""
    deleted = service.delete_contact(user_id=current_user["id"], contact_id=contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}
