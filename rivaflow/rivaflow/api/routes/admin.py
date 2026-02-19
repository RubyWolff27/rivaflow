"""Admin routes — dashboard/stats and shared helpers."""

import logging

from fastapi import APIRouter, Depends, Request

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_admin_user, get_gym_service
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.services.gym_service import GymService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Helper to check if user is admin
def require_admin(current_user: dict = Depends(get_admin_user)) -> dict:
    """
    Dependency to require admin access.

    Now uses centralized get_admin_user dependency which:
    - Returns 403 Forbidden (not 400) for non-admins
    - Logs unauthorized access attempts
    - Provides consistent admin auth across the app
    """
    return current_user


# Helper to get IP address from request
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check X-Forwarded-For header first (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Rightmost entry is added by the trusted reverse proxy
        return forwarded.split(",")[-1].strip()
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    return "unknown"


# Dashboard endpoints
@router.get("/dashboard/stats")
@limiter.limit("60/minute")
@route_error_handler("get_dashboard_stats", detail="Failed to get dashboard stats")
def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(require_admin),
    gym_svc: GymService = Depends(get_gym_service),
):
    """Get platform statistics for admin dashboard."""
    from rivaflow.core.services.admin_service import AdminService

    stats = AdminService.get_dashboard_stats()

    # Add gym stats
    total_gyms = len(gym_svc.list_all(verified_only=False))
    pending_gyms = len(gym_svc.get_pending_gyms())
    verified_gyms = total_gyms - pending_gyms

    return {
        **stats,
        "total_gyms": total_gyms,
        "verified_gyms": verified_gyms,
        "pending_gyms": pending_gyms,
    }
