"""Contacts (training partners and instructors) endpoints."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.friend_service import FriendService

router = APIRouter()
service = FriendService()


class FriendCreate(BaseModel):
    """Contact creation model."""
    name: str
    friend_type: str = "training-partner"
    belt_rank: str | None = None
    belt_stripes: int = 0
    instructor_certification: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class FriendUpdate(BaseModel):
    """Contact update model."""
    name: str | None = None
    friend_type: str | None = None
    belt_rank: str | None = None
    belt_stripes: int | None = None
    instructor_certification: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


@router.get("/")
async def list_contacts(
    search: str | None = Query(None, min_length=2, description="Search by name"),
    friend_type: str | None = Query(None, description="Filter by friend type"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    current_user: dict = Depends(get_current_user),
):
    """Get all friends with optional filtering and pagination."""
    if search:
        all_friends = service.search_friends(user_id=current_user["id"], query=search)
    elif friend_type:
        all_friends = service.repo.list_by_type(user_id=current_user["id"], friend_type=friend_type)
    else:
        all_friends = service.list_friends(user_id=current_user["id"])

    # Apply pagination
    total = len(all_friends)
    friends = all_friends[offset:offset + limit]

    return {
        "friends": friends,
        "total": total,
        "limit": limit,
        "offset": offset
    }


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
    friend = service.get_friend(user_id=current_user["id"], friend_id=friend_id)
    if not friend:
        raise NotFoundError("Friend not found")
    return friend


@router.post("/")
async def create_contact(friend: FriendCreate, current_user: dict = Depends(get_current_user)):
    """Create a new friend."""
    # Let exceptions bubble up - global handler will catch them
    created = service.create_friend(
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
    updated = service.update_friend(
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
    deleted = service.delete_friend(user_id=current_user["id"], friend_id=friend_id)
    if not deleted:
        raise NotFoundError("Friend not found")
    return {"message": "Friend deleted successfully"}
