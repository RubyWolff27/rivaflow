"""Authentication utilities for JWT tokens and password hashing."""

import secrets
from datetime import timedelta

import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from rivaflow.core.settings import settings
from rivaflow.core.time_utils import utcnow

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def _get_secret_key() -> str:
    """Return the JWT signing key, validating in production."""
    key = settings.SECRET_KEY
    if settings.IS_PRODUCTION and (
        key.startswith("dev-") or key == "dev" or len(key) < 32
    ):
        raise RuntimeError(
            "Production environment detected with insecure SECRET_KEY. "
            "SECRET_KEY must be a secure random string (>= 32 characters). "
            "Generate one with: python -c 'import secrets; "
            "print(secrets.token_urlsafe(32))'"
        )
    return key


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Truncates password to 72 bytes as bcrypt has a maximum password length.
    """
    # Bcrypt has a 72 byte limit, truncate if necessary
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate to 72 bytes and decode, removing any partial characters
        truncated = password_bytes[:72].decode("utf-8", errors="ignore")
        return pwd_context.hash(truncated)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Truncates password to 72 bytes to match hashing behavior.
    """
    # Truncate to 72 bytes to match hash_password behavior
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        truncated = password_bytes[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(truncated, hashed_password)
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Dictionary of decoded claims

    Raises:
        PyJWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(32)


def get_refresh_token_expiry() -> str:
    """Get the expiry datetime for a refresh token as ISO 8601 string."""
    expiry = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return expiry.isoformat()
