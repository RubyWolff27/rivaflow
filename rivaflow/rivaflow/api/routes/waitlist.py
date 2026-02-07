"""Waitlist API endpoints for public signup and admin management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from rivaflow.core.dependencies import get_admin_user
from rivaflow.core.exceptions import RivaFlowException
from rivaflow.core.services.email_service import EmailService
from rivaflow.db.repositories.waitlist_repo import WaitlistRepository

logger = logging.getLogger(__name__)

# Public waitlist routes
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Admin waitlist routes
admin_router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class WaitlistJoinRequest(BaseModel):
    """Request model for joining the waitlist."""

    email: EmailStr
    first_name: str | None = Field(None, max_length=100)
    gym_name: str | None = Field(None, max_length=200)
    belt_rank: str | None = Field(None, max_length=50)
    referral_source: str | None = Field(None, max_length=200)


class InviteRequest(BaseModel):
    """Request model for inviting a waitlist entry."""

    tier: str = Field("free", pattern="^(free|premium|lifetime_premium)$")


class BulkInviteRequest(BaseModel):
    """Request model for bulk inviting waitlist entries."""

    ids: list[int] = Field(..., min_length=1)
    tier: str = Field("free", pattern="^(free|premium|lifetime_premium)$")


class NotesUpdateRequest(BaseModel):
    """Request model for updating admin notes."""

    notes: str = Field(..., max_length=2000)


# ============================================================================
# Public Endpoints
# ============================================================================


@router.post("/join", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def join_waitlist(request: Request, req: WaitlistJoinRequest):
    """
    Join the RivaFlow waitlist.

    - **email**: Valid email address (required)
    - **first_name**: Your first name (optional)
    - **gym_name**: Your gym name (optional)
    - **belt_rank**: Your current belt rank (optional)
    - **referral_source**: How you heard about RivaFlow (optional)

    Returns your position on the waitlist.
    """
    repo = WaitlistRepository()

    # Check for existing entry
    existing = repo.get_by_email(req.email)
    if existing:
        return {
            "position": existing["position"],
            "message": "You're already on the list!",
        }

    try:
        entry = repo.create(
            email=req.email,
            first_name=req.first_name,
            gym_name=req.gym_name,
            belt_rank=req.belt_rank,
            referral_source=req.referral_source,
        )
        return {
            "position": entry["position"],
            "message": "You've been added to the waitlist! We'll notify you when it's your turn.",
        }
    except (RivaFlowException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to add {req.email} to waitlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join waitlist. Please try again.",
        )


@router.get("/count")
async def get_waitlist_count():
    """
    Get the number of people currently waiting on the waitlist.

    Returns the count of entries with status 'waiting'.
    """
    repo = WaitlistRepository()
    count = repo.get_waiting_count()
    return {"count": count}


# ============================================================================
# Admin Endpoints
# ============================================================================


@admin_router.get("/")
async def list_waitlist(
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_admin_user),
):
    """
    List all waitlist entries with optional filters.

    - **status**: Filter by status (waiting, invited, registered, declined)
    - **search**: Search by email or first name
    - **limit**: Maximum results to return (default 50)
    - **offset**: Number of results to skip (default 0)
    """
    repo = WaitlistRepository()

    entries = repo.list_all(status=status, search=search, limit=limit, offset=offset)
    total = repo.get_count(status=status)

    return {
        "entries": entries,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@admin_router.post("/{waitlist_id}/invite")
async def invite_entry(
    waitlist_id: int = Path(..., gt=0),
    req: InviteRequest = None,
    current_user: dict = Depends(get_admin_user),
):
    """
    Invite a specific waitlist entry.

    Generates a secure invite token, sends an invite email, and sets
    the entry status to 'invited' with a 7-day token expiry.

    - **tier**: Tier to assign (free, premium, lifetime_premium)
    """
    if req is None:
        req = InviteRequest()

    repo = WaitlistRepository()

    # Verify the entry exists
    entry = repo.get_by_id(waitlist_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    if entry["status"] == "invited":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This entry has already been invited",
        )

    if entry["status"] == "registered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This entry has already registered",
        )

    token = repo.invite(waitlist_id, assigned_tier=req.tier)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invite",
        )

    # Send invite email
    try:
        email_service = EmailService()
        email_service.send_waitlist_invite_email(
            email=entry["email"],
            first_name=entry.get("first_name"),
            invite_token=token,
        )
    except (ConnectionError, OSError, RuntimeError) as e:
        logger.error(f"Failed to send invite email to {entry['email']}: {e}")

    logger.info(
        f"Admin {current_user.get('email')} invited waitlist entry "
        f"{waitlist_id} ({entry['email']}) with tier={req.tier}"
    )

    return {"success": True, "invite_token": token}


@admin_router.post("/bulk-invite")
async def bulk_invite_entries(
    req: BulkInviteRequest,
    current_user: dict = Depends(get_admin_user),
):
    """
    Bulk invite multiple waitlist entries.

    Sends invite emails to all successfully invited entries.

    - **ids**: List of waitlist entry IDs to invite
    - **tier**: Tier to assign to all entries (free, premium, lifetime_premium)
    """
    repo = WaitlistRepository()
    results = repo.bulk_invite(req.ids, assigned_tier=req.tier)

    # Send invite emails for each successful invite
    email_service = EmailService()
    for wid, email, token in results:
        try:
            # Look up first_name for the email
            entry = repo.get_by_id(wid)
            first_name = entry.get("first_name") if entry else None
            email_service.send_waitlist_invite_email(
                email=email,
                first_name=first_name,
                invite_token=token,
            )
        except (ConnectionError, OSError, RuntimeError) as e:
            logger.error(f"Failed to send invite email to {email}: {e}")

    logger.info(
        f"Admin {current_user.get('email')} bulk invited "
        f"{len(results)} waitlist entries with tier={req.tier}"
    )

    return {"invited_count": len(results)}


@admin_router.post("/{waitlist_id}/decline")
async def decline_entry(
    waitlist_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_admin_user),
):
    """
    Decline a waitlist entry.

    Sets the entry status to 'declined'.
    """
    repo = WaitlistRepository()

    entry = repo.get_by_id(waitlist_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    success = repo.decline(waitlist_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decline entry",
        )

    logger.info(
        f"Admin {current_user.get('email')} declined waitlist entry "
        f"{waitlist_id} ({entry['email']})"
    )

    return {"success": True}


@admin_router.put("/{waitlist_id}/notes")
async def update_entry_notes(
    req: NotesUpdateRequest,
    waitlist_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_admin_user),
):
    """
    Update admin notes for a waitlist entry.
    """
    repo = WaitlistRepository()

    entry = repo.get_by_id(waitlist_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    success = repo.update_notes(waitlist_id, req.notes)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notes",
        )

    return {"success": True}


@admin_router.get("/stats")
async def get_waitlist_stats(
    current_user: dict = Depends(get_admin_user),
):
    """
    Get waitlist statistics.

    Returns counts for each status: total, waiting, invited, registered, declined.
    """
    repo = WaitlistRepository()

    total = repo.get_count()
    waiting = repo.get_count(status="waiting")
    invited = repo.get_count(status="invited")
    registered = repo.get_count(status="registered")
    declined = repo.get_count(status="declined")

    return {
        "total": total,
        "waiting": waiting,
        "invited": invited,
        "registered": registered,
        "declined": declined,
    }
