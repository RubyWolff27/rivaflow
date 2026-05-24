"""Health check endpoints — public minimal + auth-gated detailed.

Security note (audit 2026-05-24 — Groot bridge review):
    The previous `/health` exposed `version`, `commit`, `email` provider, and
    `database` status to any unauthenticated caller. Useful for legitimate
    monitoring but also a free reconnaissance surface for attackers.

    Current shape:
    - `/health`           — public, returns `{"status": "healthy"}` only.
                            Still performs the internal DB check so 503 cascades.
    - `/health/detailed`  — gated by `HEALTH_DETAILED_TOKEN` header. Returns
                            404 (not 401/403) when the token is wrong/missing
                            so the endpoint's existence isn't disclosed.
    - `/health/ready`     — public, FastAPI-style readiness probe.
    - `/health/live`      — public, FastAPI-style liveness probe (no DB).
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

from rivaflow.core.error_handling import route_error_handler
from rivaflow.db.database import get_connection

logger = logging.getLogger(__name__)

_GIT_SHA = os.getenv("RENDER_GIT_COMMIT", "unknown")
_VERSION_FILE = Path(__file__).parent.parent.parent / "VERSION"
_APP_VERSION = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "0.5.0"

router = APIRouter()


def _check_database() -> tuple[bool, str]:
    """Internal DB connectivity check. Returns (healthy, status_label)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as health_check")
            result = cursor.fetchone()
            if result and result["health_check"] == 1:
                return True, "connected"
            return False, "error"
    except Exception as e:
        logger.error("Health check database error: %s", e)
        return False, "disconnected"


@router.get("/health", tags=["monitoring"])
@route_error_handler("health_check", detail="Health check failed")
def health_check():
    """
    Public health check — returns minimal `{"status": "healthy"}` payload.

    Still performs the internal DB check so 503 propagates correctly to
    load balancers and Render's platform monitoring. Detail is intentionally
    suppressed to avoid reconnaissance exposure.

    Returns:
    - 200 OK if service is healthy
    - 503 Service Unavailable if database connection fails
    """
    db_ok, _ = _check_database()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy"},
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "healthy"})


@router.get("/health/detailed", tags=["monitoring"], include_in_schema=False)
@route_error_handler("detailed_health_check", detail="Detailed health check failed")
def detailed_health_check(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """
    Auth-gated detailed health — version, commit, email config, DB state.

    Requires `X-Admin-Token` header matching the `HEALTH_DETAILED_TOKEN` env var.
    Returns 404 (not 401/403) when missing/wrong so the endpoint's existence
    is not disclosed to unauthenticated probes.

    Internal use only. Do NOT expose publicly via tunnel or domain.
    """
    expected_token = os.getenv("HEALTH_DETAILED_TOKEN")
    if not expected_token or x_admin_token != expected_token:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Not Found"},
        )

    health_status: dict = {
        "status": "healthy",
        "service": "rivaflow-api",
        "version": _APP_VERSION,
        "commit": _GIT_SHA,
    }

    # Check email configuration
    try:
        from rivaflow.core.services.email_service import EmailService

        _email = EmailService()
        health_status["email"] = {
            "enabled": _email.enabled,
            "method": _email.method or "none",
        }
    except Exception:
        health_status["email"] = {"enabled": False, "method": "error"}

    # Check database connectivity
    db_ok, db_label = _check_database()
    health_status["database"] = db_label
    if not db_ok:
        health_status["status"] = "unhealthy"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)


@router.get("/health/ready", tags=["monitoring"])
@route_error_handler("readiness_check", detail="Readiness check failed")
def readiness_check():
    """
    Readiness check — indicates service is ready to accept traffic.

    Kubernetes/container platforms use this to know when to route traffic.
    Public; minimal payload.
    """
    return {"status": "ready", "service": "rivaflow-api"}


@router.get("/health/live", tags=["monitoring"])
@route_error_handler("liveness_check", detail="Liveness check failed")
def liveness_check():
    """
    Liveness check — indicates service process is alive.

    Kubernetes/container platforms use this to detect hung processes.
    Returns immediately without database checks. Public; minimal payload.
    """
    return {"status": "alive", "service": "rivaflow-api"}
