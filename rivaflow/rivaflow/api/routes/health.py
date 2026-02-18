"""Health check endpoint for monitoring and load balancer checks."""

import logging
import os

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from rivaflow.core.error_handling import route_error_handler
from rivaflow.db.database import get_connection

logger = logging.getLogger(__name__)

_GIT_SHA = os.getenv("RENDER_GIT_COMMIT", "unknown")

router = APIRouter()


@router.get("/health", tags=["monitoring"])
@route_error_handler("health_check", detail="Health check failed")
def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
    - 200 OK if service is healthy
    - 503 Service Unavailable if database connection fails

    This endpoint is used by:
    - Render platform health checks
    - Load balancers
    - Monitoring systems (UptimeRobot, Pingdom, etc.)
    """
    health_status = {
        "status": "healthy",
        "service": "rivaflow-api",
        "version": "0.5.0",
        "commit": _GIT_SHA,
    }

    # Check database connectivity
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as health_check")
            result = cursor.fetchone()
            if result and result["health_check"] == 1:
                health_status["database"] = "connected"
            else:
                health_status["database"] = "error"
                health_status["status"] = "unhealthy"
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content=health_status,
                )
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)


@router.get("/health/ready", tags=["monitoring"])
@route_error_handler("readiness_check", detail="Readiness check failed")
def readiness_check():
    """
    Readiness check - indicates service is ready to accept traffic.

    Kubernetes/container platforms use this to know when to route traffic.
    """
    return {"status": "ready", "service": "rivaflow-api"}


@router.get("/health/live", tags=["monitoring"])
@route_error_handler("liveness_check", detail="Liveness check failed")
def liveness_check():
    """
    Liveness check - indicates service process is alive.

    Kubernetes/container platforms use this to detect hung processes.
    Returns immediately without database checks.
    """
    return {"status": "alive", "service": "rivaflow-api"}
