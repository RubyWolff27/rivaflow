"""Global error handling middleware for FastAPI.

Provides consistent error responses across all API endpoints with:
- Standardized error format
- Request ID tracking
- Detailed logging
- Environment-aware error messages
"""

import logging
import os
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from rivaflow.core.exceptions import RivaFlowException

logger = logging.getLogger(__name__)


def format_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
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
            "action": getattr(exc, "action", None),
            "user_agent": request.headers.get("user-agent"),
        },
        exc_info=True,
    )

    # Build response details
    response_details = exc.details if exc.details else None

    # Add actionable next step if provided
    if hasattr(exc, "action") and exc.action:
        if response_details is None:
            response_details = {}
        response_details["suggested_action"] = exc.action

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_code=exc.__class__.__name__.upper().replace("ERROR", "_ERROR"),
            message=exc.message,
            status_code=exc.status_code,
            details=response_details,
            request_id=request.headers.get("X-Request-ID"),
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
    # Sensitive field names that should not have their values exposed
    sensitive_fields = {
        "password",
        "password_hash",
        "secret",
        "token",
        "api_key",
        "access_token",
        "refresh_token",
        "reset_token",
        "secret_key",
    }

    # Format validation errors in user-friendly way
    errors = []
    for error in exc.errors():
        field_name = ".".join(str(loc) for loc in error["loc"])

        # Check if field is sensitive
        is_sensitive = any(sensitive in field_name.lower() for sensitive in sensitive_fields)

        # Only include input value in development mode AND for non-sensitive fields
        env = os.getenv("ENV", "development")
        include_input = env == "development" and not is_sensitive and error.get("input") is not None

        error_dict = {
            "field": field_name,
            "message": error["msg"],
            "type": error["type"],
        }

        if include_input:
            error_dict["input"] = error.get("input")

        errors.append(error_dict)

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
            request_id=request.headers.get("X-Request-ID"),
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
            "hint": "This detailed error is only shown in development mode",
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            request_id=request.headers.get("X-Request-ID"),
        ),
    )
