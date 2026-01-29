"""Global error handling middleware for FastAPI."""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from rivaflow.core.exceptions import RivaFlowException

logger = logging.getLogger(__name__)


async def rivaflow_exception_handler(request: Request, exc: RivaFlowException) -> JSONResponse:
    """
    Handle custom RivaFlow exceptions.

    Logs the full error details server-side but returns safe message to client.
    """
    # Log full error with context
    logger.error(
        f"RivaFlowException: {exc.__class__.__name__} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": exc.__class__.__name__,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns detailed validation errors to help client fix input.
    """
    logger.warning(
        f"Validation error on {request.url.path}: {exc.errors()}",
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "details": exc.errors(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Logs full stack trace server-side but returns generic message to prevent
    information disclosure.
    """
    # Log full exception with stack trace
    logger.exception(
        f"Unhandled exception on {request.url.path}",
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "type": "InternalServerError",
        },
    )
