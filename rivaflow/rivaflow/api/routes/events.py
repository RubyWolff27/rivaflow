"""Events & Competition Prep endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.events_service import EventsService

router = APIRouter()


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
@limiter.limit("120/minute")
@route_error_handler("get_next_event", detail="Failed to get next event")
def get_next_event(request: Request, current_user: dict = Depends(get_current_user)):
    """Get the next upcoming event with countdown information."""
    svc = EventsService()
    event = svc.get_next_upcoming(user_id=current_user["id"])
    if not event:
        return {"event": None, "days_until": None}

    event_date = datetime.strptime(event["event_date"], "%Y-%m-%d").date()
    days_until = (event_date - date.today()).days

    # Get latest weight for comparison
    latest_weight = svc.get_latest_weight(user_id=current_user["id"])

    return {
        "event": event,
        "days_until": days_until,
        "current_weight": latest_weight["weight"] if latest_weight else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
@route_error_handler("create_event", detail="Failed to create event")
def create_event(
    request: Request, event: EventCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new event."""
    svc = EventsService()
    event_id = svc.create_event(
        user_id=current_user["id"],
        data=event.model_dump(),
    )
    created = svc.get_event_by_id(user_id=current_user["id"], event_id=event_id)
    return created


@router.get("/")
@limiter.limit("120/minute")
@route_error_handler("list_events", detail="Failed to list events")
def list_events(
    request: Request,
    status: str | None = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
):
    """List events for the current user."""
    svc = EventsService()
    events = svc.list_events(user_id=current_user["id"], status=status)
    return {"events": events, "total": len(events)}


@router.get("/{event_id}")
@limiter.limit("120/minute")
@route_error_handler("get_event", detail="Failed to get event")
def get_event(
    request: Request, event_id: int, current_user: dict = Depends(get_current_user)
):
    """Get a specific event by ID."""
    svc = EventsService()
    event = svc.get_event_by_id(user_id=current_user["id"], event_id=event_id)
    if not event:
        raise NotFoundError("Event not found")
    return event


@router.put("/{event_id}")
@limiter.limit("30/minute")
@route_error_handler("update_event", detail="Failed to update event")
def update_event(
    request: Request,
    event_id: int,
    event: EventUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an event."""
    svc = EventsService()
    data = {k: v for k, v in event.model_dump().items() if v is not None}
    updated = svc.update_event(user_id=current_user["id"], event_id=event_id, data=data)
    if not updated:
        raise NotFoundError("Event not found")
    return svc.get_event_by_id(user_id=current_user["id"], event_id=event_id)


@router.delete("/{event_id}")
@limiter.limit("30/minute")
@route_error_handler("delete_event", detail="Failed to delete event")
def delete_event(
    request: Request, event_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete an event."""
    svc = EventsService()
    deleted = svc.delete_event(user_id=current_user["id"], event_id=event_id)
    if not deleted:
        raise NotFoundError("Event not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Weight log endpoints ---


@router.post(
    "/weight-logs/",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
@route_error_handler("create_weight_log", detail="Failed to log weight")
def create_weight_log(
    request: Request,
    log: WeightLogCreate,
    current_user: dict = Depends(get_current_user),
):
    """Log a weight entry."""
    svc = EventsService()
    data = log.model_dump()
    if not data.get("logged_date"):
        data["logged_date"] = date.today().isoformat()
    log_id = svc.create_weight_log(user_id=current_user["id"], data=data)
    return {"id": log_id, "message": "Weight logged successfully"}


@router.get("/weight-logs/")
@limiter.limit("120/minute")
@route_error_handler("list_weight_logs", detail="Failed to list weight logs")
def list_weight_logs(
    request: Request,
    start_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user),
):
    """Get weight history with optional date range."""
    svc = EventsService()
    logs = svc.list_weight_logs(
        user_id=current_user["id"],
        start_date=start_date,
        end_date=end_date,
    )
    return {"logs": logs, "total": len(logs)}


@router.get("/weight-logs/latest")
@limiter.limit("120/minute")
@route_error_handler("get_latest_weight", detail="Failed to get latest weight")
def get_latest_weight(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get the most recent weight log."""
    svc = EventsService()
    latest = svc.get_latest_weight(user_id=current_user["id"])
    if not latest:
        return {"weight": None, "logged_date": None}
    return latest


@router.get("/weight-logs/averages")
@limiter.limit("120/minute")
@route_error_handler("get_weight_averages", detail="Failed to get weight averages")
def get_weight_averages(
    request: Request,
    period: str = Query("weekly", description="Grouping period: weekly or monthly"),
    current_user: dict = Depends(get_current_user),
):
    """Get weight averages grouped by week or month."""
    svc = EventsService()
    averages = svc.get_weight_averages(user_id=current_user["id"], period=period)
    return {"averages": averages, "period": period}
