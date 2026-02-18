"""Groups endpoints for training crews, comp teams, etc."""

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from rivaflow.core.services.groups_service import GroupsService

router = APIRouter()


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
@route_error_handler("create_group", detail="Failed to create group")
def create_group(
    request: Request,
    group: GroupCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new group."""
    repo = GroupsService()
    group_id = repo.create(
        user_id=current_user["id"],
        data=group.model_dump(),
    )
    created = repo.get_by_id(group_id)
    return created


@router.get("/")
@limiter.limit("120/minute")
@route_error_handler("list_groups", detail="Failed to list groups")
def list_groups(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List groups the current user belongs to."""
    repo = GroupsService()
    groups = repo.list_by_user(user_id=current_user["id"])
    # Add member count to each group
    for g in groups:
        g["member_count"] = repo.get_member_count(g["id"])
    return {"groups": groups, "count": len(groups)}


@router.get("/discover")
@limiter.limit("60/minute")
@route_error_handler("discover_groups", detail="Failed to discover groups")
def discover_groups(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List open groups user can join."""
    repo = GroupsService()
    groups = repo.list_discoverable(user_id=current_user["id"])
    return {"groups": groups, "count": len(groups)}


@router.get("/{group_id}")
@limiter.limit("120/minute")
@route_error_handler("get_group", detail="Failed to get group")
def get_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Get group detail with members."""
    repo = GroupsService()
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
@route_error_handler("update_group", detail="Failed to update group")
def update_group(
    request: Request,
    group_id: int,
    group: GroupUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a group. Admin only."""
    repo = GroupsService()
    updated = repo.update(
        group_id=group_id,
        user_id=current_user["id"],
        data=group.model_dump(exclude_none=True),
    )
    if not updated:
        raise AuthorizationError("Only group admins can update the group")
    return repo.get_by_id(group_id)


@router.delete("/{group_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_group", detail="Failed to delete group")
def delete_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a group. Admin only."""
    repo = GroupsService()
    deleted = repo.delete(group_id=group_id, user_id=current_user["id"])
    if not deleted:
        raise AuthorizationError("Only group admins can delete the group")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/members")
@limiter.limit("30/minute")
@route_error_handler("add_member", detail="Failed to add member")
def add_member(
    request: Request,
    group_id: int,
    member: MemberAdd,
    current_user: dict = Depends(get_current_user),
):
    """Add a member to a group (invite). Must be admin."""
    repo = GroupsService()
    role = repo.get_member_role(group_id, current_user["id"])
    if role != "admin":
        raise AuthorizationError("Only group admins can add members")

    group = repo.get_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")

    added = repo.add_member(
        group_id=group_id,
        user_id=member.user_id,
        role=member.role,
    )
    if not added:
        raise ConflictError("User is already a member of this group")
    return {"message": "Member added successfully"}


@router.delete("/{group_id}/members/{user_id}")
@limiter.limit("30/minute")
@route_error_handler("remove_member", detail="Failed to remove member")
def remove_member(
    request: Request,
    group_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Remove a member from a group. Must be admin or self."""
    repo = GroupsService()
    caller_role = repo.get_member_role(group_id, current_user["id"])
    if caller_role != "admin" and current_user["id"] != user_id:
        raise AuthorizationError("Only admins can remove other members")

    removed = repo.remove_member(group_id=group_id, user_id=user_id)
    if not removed:
        raise NotFoundError("Member not found in group")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{group_id}/join")
@limiter.limit("30/minute")
@route_error_handler("join_group", detail="Failed to join group")
def join_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Join an open group."""
    repo = GroupsService()
    group = repo.get_by_id(group_id)
    if not group:
        raise NotFoundError("Group not found")

    if group.get("privacy") != "open":
        raise AuthorizationError("This group is invite-only")

    added = repo.add_member(group_id=group_id, user_id=current_user["id"])
    if not added:
        raise ConflictError("You are already a member of this group")
    return {"message": "Joined group successfully"}


@router.post("/{group_id}/leave")
@limiter.limit("30/minute")
@route_error_handler("leave_group", detail="Failed to leave group")
def leave_group(
    request: Request,
    group_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Leave a group."""
    repo = GroupsService()
    removed = repo.remove_member(group_id=group_id, user_id=current_user["id"])
    if not removed:
        raise NotFoundError("You are not a member of this group")
    return {"message": "Left group successfully"}
