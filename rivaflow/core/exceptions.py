"""Custom exception classes for RivaFlow application."""


class RivaFlowException(Exception):
    """Base exception for all RivaFlow errors."""

    status_code = 500
    default_message = "An unexpected error occurred"

    def __init__(self, message: str = None, details: dict = None):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RivaFlowException):
    """Raised when input validation fails."""

    status_code = 400
    default_message = "Validation failed"


class AuthenticationError(RivaFlowException):
    """Raised when authentication fails."""

    status_code = 401
    default_message = "Authentication failed"


class AuthorizationError(RivaFlowException):
    """Raised when user lacks permission for an action."""

    status_code = 403
    default_message = "You do not have permission to perform this action"


class NotFoundError(RivaFlowException):
    """Raised when a requested resource is not found."""

    status_code = 404
    default_message = "Resource not found"


class ConflictError(RivaFlowException):
    """Raised when a request conflicts with existing data."""

    status_code = 409
    default_message = "Request conflicts with existing data"


class RateLimitError(RivaFlowException):
    """Raised when rate limit is exceeded."""

    status_code = 429
    default_message = "Rate limit exceeded"


class ServiceError(RivaFlowException):
    """Raised when an internal service error occurs."""

    status_code = 500
    default_message = "Internal service error"


class DatabaseError(ServiceError):
    """Raised when a database operation fails."""

    default_message = "Database operation failed"


class ExternalServiceError(ServiceError):
    """Raised when an external service (email, API) fails."""

    status_code = 503
    default_message = "External service unavailable"
