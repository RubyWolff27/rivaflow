"""Global error handling middleware for FastAPI.

Provides consistent error responses across all API endpoints with:
- Standardized error format
- Request ID tracking
- Detailed logging
- Environment-aware error messages
"""
import logging
import os
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from rivaflow.core.exceptions import RivaFlowException

logger = logging.getLogger(__name__)


def format_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format error response in consistent structure.

    Args:
        error_code: Machine-readable error code (e.g., VALIDATION_ERROR)
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracking (from X-Request-ID header)

    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
        }
    }

    if details:
        response["error"]["details"] = details

    if request_id:
        response["error"]["request_id"] = request_id

    return response


async def rivaflow_exception_handler(request: Request, exc: RivaFlowException) -> JSONResponse:
    """Handle custom RivaFlow exceptions.

    Logs the full error details server-side but returns safe message to client.

    Args:
        request: FastAPI request
        exc: RivaFlow exception

    Returns:
        JSON response with formatted error
    """
    # Log full error with context
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "details": exc.details,
            "user_agent": request.headers.get("user-agent"),
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_code=exc.__class__.__name__.upper().replace("ERROR", "_ERROR"),
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details if exc.details else None,
            request_id=request.headers.get("X-Request-ID")
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Returns detailed validation errors to help client fix input.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON response with validation errors
    """
    # Format validation errors in user-friendly way
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input"),  # Include invalid input for debugging
        })

    # Format errors for logging
    error_summary = "; ".join([f"{e['field']}: {e['message']}" for e in errors])

    logger.warning(
        f"Validation error on {request.url.path}: {error_summary}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_count": len(errors),
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed. Please check your input.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": errors},
            request_id=request.headers.get("X-Request-ID")
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Logs full stack trace server-side but returns generic message to prevent
    information disclosure in production.

    Args:
        request: FastAPI request
        exc: Unexpected exception

    Returns:
        JSON response with generic error
    """
    # Log full exception with stack trace
    logger.exception(
        f"Unhandled exception on {request.url.path}: {type(exc).__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "user_agent": request.headers.get("user-agent"),
        },
    )

    # In development, include more details for debugging
    message = "An unexpected error occurred. Please try again later."
    details = None

    if os.getenv("ENV", "development") == "development":
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {
            "type": type(exc).__name__,
            "hint": "This detailed error is only shown in development mode"
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            request_id=request.headers.get("X-Request-ID")
        ),
    )
