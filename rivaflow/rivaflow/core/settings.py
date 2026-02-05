"""Centralized application settings with environment variable management.

This module provides a single source of truth for all configuration,
including environment variables, API keys, and runtime settings.
"""

import os
from pathlib import Path


class Settings:
    """
    Application settings with environment variable support.

    All settings are loaded from environment variables with sensible defaults.
    """

    # ==============================================================================
    # ENVIRONMENT
    # ==============================================================================

    @property
    def ENV(self) -> str:
        """Application environment (development, production, test)."""
        return os.getenv("ENV", "development")

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development."""
        return self.ENV == "development"

    @property
    def IS_TEST(self) -> bool:
        """Check if running in test environment."""
        return self.ENV == "test"

    # ==============================================================================
    # SECURITY
    # ==============================================================================

    @property
    def SECRET_KEY(self) -> str:
        """
        Secret key for JWT signing and encryption.

        REQUIRED in all environments. Raises ValueError if not set.
        """
        secret = os.getenv("SECRET_KEY")
        if not secret:
            raise ValueError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return secret

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """JWT access token expiration time in minutes."""
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        """JWT refresh token expiration time in days."""
        return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # ==============================================================================
    # DATABASE
    # ==============================================================================

    @property
    def DATABASE_URL(self) -> str | None:
        """
        Database connection URL.

        If not set, defaults to SQLite at ~/.rivaflow/rivaflow.db
        Format: postgresql://user:pass@host:port/dbname
        """
        url = os.getenv("DATABASE_URL")
        if url and url.startswith("postgres://"):
            # Render uses postgres:// but psycopg2 expects postgresql://
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def DB_TYPE(self) -> str:
        """Database type (sqlite or postgresql)."""
        return "postgresql" if self.DATABASE_URL else "sqlite"

    @property
    def APP_DIR(self) -> Path:
        """Application data directory (~/.rivaflow)."""
        return Path.home() / ".rivaflow"

    @property
    def DB_PATH(self) -> Path:
        """SQLite database file path."""
        return self.APP_DIR / "rivaflow.db"

    # ==============================================================================
    # EMAIL / NOTIFICATIONS
    # ==============================================================================

    @property
    def SENDGRID_API_KEY(self) -> str | None:
        """SendGrid API key for email delivery."""
        return os.getenv("SENDGRID_API_KEY")

    @property
    def SMTP_HOST(self) -> str:
        """SMTP server hostname."""
        return os.getenv("SMTP_HOST", "smtp.gmail.com")

    @property
    def SMTP_PORT(self) -> int:
        """SMTP server port."""
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def SMTP_USER(self) -> str | None:
        """SMTP username."""
        return os.getenv("SMTP_USER")

    @property
    def SMTP_PASSWORD(self) -> str | None:
        """SMTP password."""
        return os.getenv("SMTP_PASSWORD")

    @property
    def FROM_EMAIL(self) -> str:
        """Default sender email address."""
        return os.getenv("FROM_EMAIL", self.SMTP_USER or "noreply@rivaflow.com")

    @property
    def FROM_NAME(self) -> str:
        """Default sender name."""
        return os.getenv("FROM_NAME", "RivaFlow")

    # ==============================================================================
    # APPLICATION URLs
    # ==============================================================================

    @property
    def APP_BASE_URL(self) -> str:
        """Base URL for the application (used in emails, redirects)."""
        return os.getenv("APP_BASE_URL", "https://rivaflow.onrender.com")

    @property
    def API_BASE_URL(self) -> str:
        """Base URL for the API."""
        return os.getenv("API_BASE_URL", self.APP_BASE_URL)

    # ==============================================================================
    # REDIS / CACHING
    # ==============================================================================

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL for caching."""
        return os.getenv("REDIS_URL", "redis://localhost:6379")

    @property
    def CACHE_ENABLED(self) -> bool:
        """Enable caching (Redis)."""
        return os.getenv("CACHE_ENABLED", "false").lower() == "true"

    # ==============================================================================
    # AI / LLM INTEGRATION
    # ==============================================================================

    @property
    def GROQ_API_KEY(self) -> str | None:
        """Groq API key for LLM features."""
        return os.getenv("GROQ_API_KEY")

    @property
    def TOGETHER_API_KEY(self) -> str | None:
        """Together AI API key."""
        return os.getenv("TOGETHER_API_KEY")

    @property
    def OLLAMA_URL(self) -> str:
        """Ollama server URL for local LLM."""
        return os.getenv("OLLAMA_URL", "http://localhost:11434")

    # ==============================================================================
    # FEATURE FLAGS
    # ==============================================================================

    @property
    def ENABLE_GRAPPLE(self) -> bool:
        """Enable Grapple AI coaching features."""
        return os.getenv("ENABLE_GRAPPLE", "true").lower() == "true"

    @property
    def ENABLE_WHOOP_INTEGRATION(self) -> bool:
        """Enable WHOOP fitness tracker integration."""
        return os.getenv("ENABLE_WHOOP_INTEGRATION", "false").lower() == "true"

    @property
    def ENABLE_SOCIAL_FEATURES(self) -> bool:
        """Enable social features (friends, likes, comments)."""
        return os.getenv("ENABLE_SOCIAL_FEATURES", "true").lower() == "true"

    # ==============================================================================
    # RATE LIMITING
    # ==============================================================================

    @property
    def RATE_LIMIT_ENABLED(self) -> bool:
        """Enable rate limiting."""
        return os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        """Maximum requests per minute per user."""
        return int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    @property
    def RATE_LIMIT_PER_HOUR(self) -> int:
        """Maximum requests per hour per user."""
        return int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

    # ==============================================================================
    # FILE UPLOADS
    # ==============================================================================

    @property
    def MAX_UPLOAD_SIZE_MB(self) -> int:
        """Maximum file upload size in megabytes."""
        return int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        """Maximum file upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def UPLOAD_DIR(self) -> Path:
        """Directory for file uploads."""
        upload_dir = Path(os.getenv("UPLOAD_DIR", str(self.APP_DIR / "uploads")))
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    # ==============================================================================
    # LOGGING
    # ==============================================================================

    @property
    def LOG_LEVEL(self) -> str:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        return os.getenv("LOG_LEVEL", "INFO" if self.IS_PRODUCTION else "DEBUG")

    @property
    def LOG_FILE(self) -> Path | None:
        """Log file path (None for stdout only)."""
        log_file = os.getenv("LOG_FILE")
        return Path(log_file) if log_file else None

    # ==============================================================================
    # TESTING
    # ==============================================================================

    @property
    def TEST_DATABASE_URL(self) -> str:
        """Database URL for testing (in-memory SQLite)."""
        return os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

    # ==============================================================================
    # CORS
    # ==============================================================================

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Allowed CORS origins (comma-separated)."""
        origins = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
        )
        return [origin.strip() for origin in origins.split(",")]

    # ==============================================================================
    # UTILITY METHODS
    # ==============================================================================

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get an environment variable with optional default."""
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        """
        Get a required environment variable.

        Raises:
            ValueError: If the environment variable is not set
        """
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"{key} environment variable is required")
        return value

    def as_dict(self) -> dict:
        """Export all settings as a dictionary (for debugging)."""
        return {
            "ENV": self.ENV,
            "IS_PRODUCTION": self.IS_PRODUCTION,
            "IS_DEVELOPMENT": self.IS_DEVELOPMENT,
            "DB_TYPE": self.DB_TYPE,
            "APP_BASE_URL": self.APP_BASE_URL,
            "CACHE_ENABLED": self.CACHE_ENABLED,
            "RATE_LIMIT_ENABLED": self.RATE_LIMIT_ENABLED,
            "LOG_LEVEL": self.LOG_LEVEL,
            # Omit sensitive values like SECRET_KEY, API keys
        }


# Global settings instance
settings = Settings()
