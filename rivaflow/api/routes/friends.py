"""Contacts (training partners and instructors) endpoints."""
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import Optional

from rivaflow.core.services.friend_service import FriendService
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError

router = APIRouter()
service = FriendService()


class FriendCreate(BaseModel):
    """Contact creation model."""
    name: str
    friend_type: str = "training-partner"
    belt_rank: Optional[str] = None
    belt_stripes: int = 0
    instructor_certification: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class FriendUpdate(BaseModel):
    """Contact update model."""
    name: Optional[str] = None
    friend_type: Optional[str] = None
    belt_rank: Optional[str] = None
    belt_stripes: Optional[int] = None
    instructor_certification: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_contacts(
    search: Optional[str] = Query(None, description="Search by name"),
    friend_type: Optional[str] = Query(None, description="Filter by friend type"),
    current_user: dict = Depends(get_current_user),
):
    """Get all friends with optional filtering."""
    if search:
        friends = service.search_contacts(user_id=current_user["id"], search=search)
    elif friend_type:
        friends = service.repo.list_by_type(user_id=current_user["id"], friend_type=friend_type)
    else:
        friends = service.list_contacts(user_id=current_user["id"])
    return friends


@router.get("/instructors")
async def list_instructors(current_user: dict = Depends(get_current_user)):
    """Get all friends who are instructors."""
    instructors = service.list_instructors(user_id=current_user["id"])
    return instructors


@router.get("/partners")
async def list_training_partners(current_user: dict = Depends(get_current_user)):
    """Get all friends who are training partners."""
    partners = service.list_training_partners(user_id=current_user["id"])
    return partners


@router.get("/{friend_id}")
async def get_contact(friend_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific friend by ID."""
    friend = service.get_contact(user_id=current_user["id"], friend_id=friend_id)
    if not friend:
        raise NotFoundError("Friend not found")
    return friend


@router.post("/")
async def create_contact(friend: FriendCreate, current_user: dict = Depends(get_current_user)):
    """Create a new friend."""
    # Let exceptions bubble up - global handler will catch them
    created = service.create_contact(
        user_id=current_user["id"],
        name=friend.name,
        friend_type=friend.friend_type,
        belt_rank=friend.belt_rank,
        belt_stripes=friend.belt_stripes,
        instructor_certification=friend.instructor_certification,
        phone=friend.phone,
        email=friend.email,
        notes=friend.notes,
    )
    return created


@router.put("/{friend_id}")
async def update_contact(friend_id: int, friend: FriendUpdate, current_user: dict = Depends(get_current_user)):
    """Update a friend."""
    updated = service.update_contact(
        user_id=current_user["id"],
        friend_id=friend_id,
        name=friend.name,
        friend_type=friend.friend_type,
        belt_rank=friend.belt_rank,
        belt_stripes=friend.belt_stripes,
        instructor_certification=friend.instructor_certification,
        phone=friend.phone,
        email=friend.email,
        notes=friend.notes,
    )
    if not updated:
        raise NotFoundError("Friend not found")
    return updated


@router.delete("/{friend_id}")
async def delete_contact(friend_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a friend."""
    deleted = service.delete_contact(user_id=current_user["id"], friend_id=friend_id)
    if not deleted:
        raise NotFoundError("Friend not found")
    return {"message": "Friend deleted successfully"}
