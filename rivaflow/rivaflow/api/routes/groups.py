"""Groups endpoints for training crews, comp teams, etc."""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.db.repositories.groups_repo import GroupsRepository

router = APIRouter()
repo = GroupsRepository()


class GroupCreate(BaseModel):
    """Group creation model."""

    name: str
    description: str | None = None
    group_type: str = "training_crew"
    privacy: str = "invite_only"
    gym_id: int | None = None
    avatar_url: str | None = None


class GroupUpdate(BaseModel):
    """Group update model."""

    name: str | None = None
    description: str | None = None
    group_type: str | None = None
    privacy: str | None = None
    gym_id: int | None = None
    avatar_url: str | None = None


class MemberAdd(BaseModel):
    """Add member model."""

    user_id: int
    role: str = "member"


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_group(
    request: Request,
    group: GroupCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new group."""
    group_id = repo.create(
        user_id=current_user["id"],
        data=group.model_dump(),
    )
    created = repo.get_by_id(group_id)
    return created


@router.get("/")
@limiter.limit("120/minute")
def list_groups(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List groups the current user belongs to."""
    groups = repo.list_by_user(user_id=current_user["id"])
    # Add member count to each group
    for g in groups:
        g["member_count"] = repo.get_member_count(g["id"])
    return {"groups": groups, "count": len(groups)}


@router.get("/discover")
@limiter.limit("60/minute")
def discover_groups(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List open groups user can join."""
    groups = repo.list_discoverable(user_id=current_user["id"])
    return {"groups": groups, "count": len(groups)}


@router.get("/{group_id}")
@limiter.limit("120/minute")
def get_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get group detail with members."""
    group = repo.get_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")

    members = repo.get_members(group_id)
    user_role = repo.get_member_role(group_id, current_user["id"])

    return {
        **group,
        "members": members,
        "member_count": len(members),
        "user_role": user_role,
    }


@router.put("/{group_id}")
@limiter.limit("30/minute")
def update_group(
    request: Request,
    group_id: int,
    group: GroupUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a group. Admin only."""
    updated = repo.update(
        group_id=group_id,
        user_id=current_user["id"],
        data=group.model_dump(exclude_none=True),
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can update the group",
        )
    return repo.get_by_id(group_id)


@router.delete("/{group_id}")
@limiter.limit("30/minute")
def delete_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a group. Admin only."""
    deleted = repo.delete(group_id=group_id, user_id=current_user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can delete the group",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/members")
@limiter.limit("30/minute")
def add_member(
    request: Request,
    group_id: int,
    member: MemberAdd,
    current_user: dict = Depends(get_current_user),
):
    """Add a member to a group (invite). Must be admin."""
    role = repo.get_member_role(group_id, current_user["id"])
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can add members",
        )

    group = repo.get_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")

    added = repo.add_member(
        group_id=group_id,
        user_id=member.user_id,
        role=member.role,
    )
    if not added:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group",
        )
    return {"message": "Member added successfully"}


@router.delete("/{group_id}/members/{user_id}")
@limiter.limit("30/minute")
def remove_member(
    request: Request,
    group_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Remove a member from a group. Must be admin or self."""
    caller_role = repo.get_member_role(group_id, current_user["id"])
    if caller_role != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove other members",
        )

    removed = repo.remove_member(group_id=group_id, user_id=user_id)
    if not removed:
        raise NotFoundError("Member not found in group")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/join")
@limiter.limit("30/minute")
def join_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Join an open group."""
    group = repo.get_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")

    if group.get("privacy") != "open":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This group is invite-only",
        )

    added = repo.add_member(group_id=group_id, user_id=current_user["id"])
    if not added:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this group",
        )
    return {"message": "Joined group successfully"}


@router.post("/{group_id}/leave")
@limiter.limit("30/minute")
def leave_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Leave a group."""
    removed = repo.remove_member(group_id=group_id, user_id=current_user["id"])
    if not removed:
        raise NotFoundError("You are not a member of this group")
    return {"message": "Left group successfully"}
