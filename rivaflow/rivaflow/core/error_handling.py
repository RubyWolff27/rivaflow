"""Secure error handling utilities."""

import asyncio
import functools
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def route_error_handler(
    operation: str,
    detail: str = "An error occurred",
):
    """Decorator that wraps route handlers with standardized error handling.

    Re-raises RivaFlowException and HTTPException unchanged.
    Catches ValueError/KeyError/TypeError, logs with exc_info, and raises HTTP 500.

    Usage::

        @router.get("/foo")
        @route_error_handler("foo lookup")
        def get_foo(...):
            return service.get_foo(...)
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except (ValueError, KeyError, TypeError):
                logger.error("%s failed", operation, exc_info=True)
                raise HTTPException(status_code=500, detail=detail)

        return wrapper

    return decorator


def handle_service_error(
    error: Exception,
    user_message: str = "An error occurred",
    user_id: int | None = None,
    operation: str | None = None,
) -> str:
    """
    Handle service errors securely.

    Logs full error details server-side but returns generic message to client.

    Args:
        error: The exception that occurred
        user_message: Generic message to show to user
        user_id: Optional user ID for logging context
        operation: Optional operation name for logging context

    Returns:
        Generic user-facing error message
    """
    # Log full details server-side
    log_context = {}
    if user_id:
        log_context["user_id"] = user_id
    if operation:
        log_context["operation"] = operation

    logger.error(
        f"{user_message}: {type(error).__name__}", exc_info=True, extra=log_context
    )

    # Return generic message to client
    return user_message
