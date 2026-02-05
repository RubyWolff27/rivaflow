"""Secure error handling utilities."""

import logging

logger = logging.getLogger(__name__)


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

    logger.error(f"{user_message}: {type(error).__name__}", exc_info=True, extra=log_context)

    # Return generic message to client
    return user_message
