"""Centralized application settings with environment variable management.

This module provides a single source of truth for all configuration,
including environment variables, API keys, and runtime settings.

All environment variables are read ONCE at import time and cached as
instance attributes. This avoids repeated os.getenv() syscalls on every
property access.
"""

import os
from pathlib import Path


class Settings:
    """
    Application settings with environment variable support.

    All settings are loaded from environment variables at init time.
    """

    def __init__(self):
        # ======================================================================
        # ENVIRONMENT
        # ======================================================================
        self.ENV: str = os.getenv("ENV", "development")
        self.IS_PRODUCTION: bool = self.ENV == "production"
        self.IS_DEVELOPMENT: bool = self.ENV == "development"
        self.IS_TEST: bool = self.ENV == "test"
        self.WAITLIST_ENABLED: bool = (
            os.getenv("WAITLIST_ENABLED", "false").lower() == "true"
        )

        # ======================================================================
        # SECURITY
        # ======================================================================
        self._secret_key: str | None = os.getenv("SECRET_KEY")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")
        )

        # ======================================================================
        # DATABASE
        # ======================================================================
        raw_db_url = os.getenv("DATABASE_URL")
        if raw_db_url and raw_db_url.startswith("postgres://"):
            raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        self.DATABASE_URL: str | None = raw_db_url
        self.DB_TYPE: str = "postgresql" if self.DATABASE_URL else "sqlite"
        self.APP_DIR: Path = Path.home() / ".rivaflow"
        self.DB_PATH: Path = self.APP_DIR / "rivaflow.db"

        # ======================================================================
        # EMAIL / NOTIFICATIONS
        # ======================================================================
        self.SENDGRID_API_KEY: str | None = os.getenv("SENDGRID_API_KEY")
        self.SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER: str | None = os.getenv("SMTP_USER")
        self.SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
        self.FROM_EMAIL: str = os.getenv(
            "FROM_EMAIL", self.SMTP_USER or "noreply@rivaflow.com"
        )
        self.FROM_NAME: str = os.getenv("FROM_NAME", "RivaFlow")

        # ======================================================================
        # APPLICATION URLs
        # ======================================================================
        self.APP_BASE_URL: str = os.getenv(
            "APP_BASE_URL", "https://rivaflow.onrender.com"
        )
        self.API_BASE_URL: str = os.getenv("API_BASE_URL", self.APP_BASE_URL)

        # ======================================================================
        # REDIS / CACHING
        # ======================================================================
        self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "false").lower() == "true"

        # ======================================================================
        # AI / LLM INTEGRATION
        # ======================================================================
        self.GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
        self.TOGETHER_API_KEY: str | None = os.getenv("TOGETHER_API_KEY")
        self.OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
        self.OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

        # ======================================================================
        # FEATURE FLAGS
        # ======================================================================
        self.ENABLE_GRAPPLE: bool = (
            os.getenv("ENABLE_GRAPPLE", "true").lower() == "true"
        )
        self.ENABLE_WHOOP_INTEGRATION: bool = (
            os.getenv("ENABLE_WHOOP_INTEGRATION", "false").lower() == "true"
        )
        self.WHOOP_CLIENT_ID: str | None = os.getenv("WHOOP_CLIENT_ID")
        self.WHOOP_CLIENT_SECRET: str | None = os.getenv("WHOOP_CLIENT_SECRET")
        self.WHOOP_REDIRECT_URI: str = os.getenv(
            "WHOOP_REDIRECT_URI",
            f"{self.API_BASE_URL}/api/v1/integrations/whoop/callback",
        )
        self.WHOOP_ENCRYPTION_KEY: str | None = os.getenv("WHOOP_ENCRYPTION_KEY")
        self.ENABLE_SOCIAL_FEATURES: bool = (
            os.getenv("ENABLE_SOCIAL_FEATURES", "true").lower() == "true"
        )

        # ======================================================================
        # RATE LIMITING
        # ======================================================================
        self.RATE_LIMIT_ENABLED: bool = (
            os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        )
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

        # ======================================================================
        # FILE UPLOADS
        # ======================================================================
        self.MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
        self.MAX_UPLOAD_SIZE_BYTES: int = self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self._upload_dir_path: str = os.getenv(
            "UPLOAD_DIR", str(self.APP_DIR / "uploads")
        )

        # ======================================================================
        # S3 / CLOUDFLARE R2 STORAGE
        # ======================================================================
        self.S3_BUCKET_NAME: str | None = os.getenv("S3_BUCKET_NAME")
        self.S3_PUBLIC_URL: str | None = os.getenv("S3_PUBLIC_URL")
        self.STORAGE_BACKEND: str = "s3" if self.S3_BUCKET_NAME else "local"

        # ======================================================================
        # LOGGING
        # ======================================================================
        self.LOG_LEVEL: str = os.getenv(
            "LOG_LEVEL", "INFO" if self.IS_PRODUCTION else "DEBUG"
        )
        log_file = os.getenv("LOG_FILE")
        self.LOG_FILE: Path | None = Path(log_file) if log_file else None

        # ======================================================================
        # TESTING
        # ======================================================================
        self.TEST_DATABASE_URL: str = os.getenv(
            "TEST_DATABASE_URL", "sqlite:///:memory:"
        )

        # ======================================================================
        # CORS
        # ======================================================================
        origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000",
        )
        self.CORS_ORIGINS: list[str] = [origin.strip() for origin in origins.split(",")]

    @property
    def SECRET_KEY(self) -> str:
        """
        Secret key for JWT signing and encryption.

        REQUIRED in all environments. Raises ValueError if not set.
        """
        if not self._secret_key:
            raise ValueError(
                "SECRET_KEY environment variable is required. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return self._secret_key

    @property
    def UPLOAD_DIR(self) -> Path:
        """Directory for file uploads (creates on first access)."""
        upload_dir = Path(self._upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

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
