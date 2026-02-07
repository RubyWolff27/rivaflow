"""Events & Competition Prep endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import NotFoundError
from rivaflow.db.repositories.events_repo import EventRepository
from rivaflow.db.repositories.weight_log_repo import WeightLogRepository

router = APIRouter()
event_repo = EventRepository()
weight_repo = WeightLogRepository()


# --- Pydantic models ---


class EventCreate(BaseModel):
    """Event creation model."""

    name: str
    event_type: str = "competition"
    event_date: str
    location: str | None = None
    weight_class: str | None = None
    target_weight: float | None = None
    division: str | None = None
    notes: str | None = None
    status: str = "upcoming"


class EventUpdate(BaseModel):
    """Event update model."""

    name: str | None = None
    event_type: str | None = None
    event_date: str | None = None
    location: str | None = None
    weight_class: str | None = None
    target_weight: float | None = None
    division: str | None = None
    notes: str | None = None
    status: str | None = None


class WeightLogCreate(BaseModel):
    """Weight log creation model."""

    weight: float
    logged_date: str | None = None
    time_of_day: str | None = None
    notes: str | None = None


# --- Event endpoints ---


@router.get("/next")
async def get_next_event(current_user: dict = Depends(get_current_user)):
    """Get the next upcoming event with countdown information."""
    event = event_repo.get_next_upcoming(user_id=current_user["id"])
    if not event:
        return {"event": None, "days_until": None}

    event_date = datetime.strptime(event["event_date"], "%Y-%m-%d").date()
    days_until = (event_date - date.today()).days

    # Get latest weight for comparison
    latest_weight = weight_repo.get_latest(user_id=current_user["id"])

    return {
        "event": event,
        "days_until": days_until,
        "current_weight": latest_weight["weight"] if latest_weight else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new event."""
    event_id = event_repo.create(
        user_id=current_user["id"],
        data=event.model_dump(),
    )
    created = event_repo.get_by_id(user_id=current_user["id"], event_id=event_id)
    return created


@router.get("/")
async def list_events(
    status: str | None = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
):
    """List events for the current user."""
    events = event_repo.list_by_user(user_id=current_user["id"], status=status)
    return {"events": events, "total": len(events)}


@router.get("/{event_id}")
async def get_event(event_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific event by ID."""
    event = event_repo.get_by_id(user_id=current_user["id"], event_id=event_id)
    if not event:
        raise NotFoundError("Event not found")
    return event


@router.put("/{event_id}")
async def update_event(
    event_id: int,
    event: EventUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an event."""
    data = {k: v for k, v in event.model_dump().items() if v is not None}
    updated = event_repo.update(
        user_id=current_user["id"], event_id=event_id, data=data
    )
    if not updated:
        raise NotFoundError("Event not found")
    return event_repo.get_by_id(user_id=current_user["id"], event_id=event_id)


@router.delete("/{event_id}")
async def delete_event(event_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an event."""
    deleted = event_repo.delete(user_id=current_user["id"], event_id=event_id)
    if not deleted:
        raise NotFoundError("Event not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Weight log endpoints ---


@router.post(
    "/weight-logs/",
    status_code=status.HTTP_201_CREATED,
)
async def create_weight_log(
    log: WeightLogCreate, current_user: dict = Depends(get_current_user)
):
    """Log a weight entry."""
    data = log.model_dump()
    if not data.get("logged_date"):
        data["logged_date"] = date.today().isoformat()
    log_id = weight_repo.create(user_id=current_user["id"], data=data)
    return {"id": log_id, "message": "Weight logged successfully"}


@router.get("/weight-logs/")
async def list_weight_logs(
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user),
):
    """Get weight history with optional date range."""
    logs = weight_repo.list_by_user(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/weight-logs/latest")
async def get_latest_weight(
    current_user: dict = Depends(get_current_user),
):
    """Get the most recent weight log."""
    latest = weight_repo.get_latest(user_id=current_user["id"])
    if not latest:
        return {"weight": None, "logged_date": None}
    return latest


@router.get("/weight-logs/averages")
async def get_weight_averages(
    period: str = Query("weekly", description="Grouping period: weekly or monthly"),
    current_user: dict = Depends(get_current_user),
):
    """Get weight averages grouped by week or month."""
    averages = weight_repo.get_averages(user_id=current_user["id"], period=period)
    return {"averages": averages, "period": period}
