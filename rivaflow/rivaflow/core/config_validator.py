"""Environment variable validation for production deployment."""

import logging
import os
import sys

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


def validate_environment():
    """
    Validate required environment variables at startup.

    Fails fast with clear error messages if configuration is invalid.
    This prevents silent failures and makes deployment issues obvious.

    Raises:
        ConfigurationError: If required env vars are missing or invalid
    """
    errors = []

    # Check SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        errors.append(
            "SECRET_KEY environment variable is required. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    elif len(secret_key) < 32:
        errors.append(
            f"SECRET_KEY must be at least 32 characters (current: {len(secret_key)}). "
            "Generate a secure one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    # Check DATABASE_URL (required for production)
    database_url = os.getenv("DATABASE_URL")
    env = os.getenv("ENV", "development")

    if env == "production" and not database_url:
        errors.append(
            "DATABASE_URL environment variable is required in production. "
            "Provide a PostgreSQL connection string."
        )

    if database_url:
        # Validate format
        if not (
            database_url.startswith("postgresql://")
            or database_url.startswith("postgres://")
            or database_url.startswith("sqlite:///")
        ):
            errors.append(
                f"DATABASE_URL has invalid format. "
                f"Expected postgresql:// or sqlite:/// but got: {database_url[:20]}..."
            )

    # Check ALLOWED_ORIGINS for CORS (recommended for production)
    allowed_origins = os.getenv("ALLOWED_ORIGINS")
    if env == "production" and not allowed_origins:
        logger.warning(
            "ALLOWED_ORIGINS not set. Using default localhost origins. "
            "Set ALLOWED_ORIGINS=https://yourdomain.com for production."
        )

    # Validate optional but recommended settings
    redis_url = os.getenv("REDIS_URL")
    if env == "production" and not redis_url:
        logger.warning(
            "REDIS_URL not set. Caching will be disabled. "
            "Set REDIS_URL for better performance."
        )

    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    if env == "production" and not sendgrid_key:
        logger.warning(
            "SENDGRID_API_KEY not set. Email notifications will be disabled."
        )

    # If there are errors, fail fast
    if errors:
        error_message = "\n\n" + "=" * 80 + "\n"
        error_message += "CONFIGURATION ERROR - Cannot start application\n"
        error_message += "=" * 80 + "\n\n"
        for i, error in enumerate(errors, 1):
            error_message += f"{i}. {error}\n\n"
        error_message += "=" * 80 + "\n"

        logger.error(error_message)
        raise ConfigurationError(error_message)

    # Log successful validation
    logger.info("✓ Environment configuration validated successfully")
    logger.info(f"  Environment: {env}")
    logger.info(
        f"  Database: {'PostgreSQL' if database_url and 'postgres' in database_url else 'SQLite'}"
    )
    logger.info(f"  Redis caching: {'enabled' if redis_url else 'disabled'}")
    logger.info(f"  Email notifications: {'enabled' if sendgrid_key else 'disabled'}")


if __name__ == "__main__":
    """Allow running as standalone validation script."""
    try:
        validate_environment()
        print("✓ All configuration valid")
        sys.exit(0)
    except ConfigurationError as e:
        print(str(e))
        sys.exit(1)
