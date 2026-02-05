"""Health check endpoint for monitoring and load balancer checks."""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from rivaflow.db.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["monitoring"])
async def health_check():
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
        "version": "0.2.0",
    }

    # Check database connectivity
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as health_check")
            result = cursor.fetchone()
            if result and result.get("health_check") == 1:
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
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error repr: {repr(e)}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        health_status["error_type"] = type(e).__name__
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)

    return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)


@router.get("/health/ready", tags=["monitoring"])
async def readiness_check():
    """
    Readiness check - indicates service is ready to accept traffic.

    Kubernetes/container platforms use this to know when to route traffic.
    """
    return {"status": "ready", "service": "rivaflow-api"}


@router.get("/health/live", tags=["monitoring"])
async def liveness_check():
    """
    Liveness check - indicates service process is alive.

    Kubernetes/container platforms use this to detect hung processes.
    Returns immediately without database checks.
    """
    return {"status": "alive", "service": "rivaflow-api"}
