"""Authentication utilities for JWT tokens and password hashing."""

import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from rivaflow.core.settings import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration - Load from centralized settings
# This will raise ValueError if SECRET_KEY is not set
SECRET_KEY = settings.SECRET_KEY

# Production security check - ensure dev secret is not used in production
if settings.IS_PRODUCTION and (
    SECRET_KEY.startswith("dev-") or SECRET_KEY == "dev" or len(SECRET_KEY) < 32
):
    raise RuntimeError(
        "Production environment detected with insecure SECRET_KEY. "
        "SECRET_KEY must be a secure random string (>= 32 characters). "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Dictionary of decoded claims

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(32)


def get_refresh_token_expiry() -> str:
    """Get the expiry datetime for a refresh token as ISO 8601 string."""
    expiry = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return expiry.isoformat()
