"""Authentication utilities for JWT tokens and password hashing."""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration - SECRET_KEY is REQUIRED in production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is required. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

# Production security check - ensure dev secret is not used in production
ENV = os.getenv("ENV", "development")
if ENV == "production" and (SECRET_KEY.startswith("dev-") or SECRET_KEY == "dev" or len(SECRET_KEY) < 32):
    raise RuntimeError(
        "Production environment detected with insecure SECRET_KEY. "
        "SECRET_KEY must be a secure random string (>= 32 characters). "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Truncates password to 72 bytes as bcrypt has a maximum password length.
    """
    # Bcrypt has a 72 byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes and decode, removing any partial characters
        truncated = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(truncated)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Truncates password to 72 bytes to match hashing behavior.
    """
    # Truncate to 72 bytes to match hash_password behavior
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        truncated = password_bytes[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(truncated, hashed_password)
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
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


def decode_access_token(token: str) -> dict:
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
        raise


def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return secrets.token_urlsafe(32)


def get_refresh_token_expiry() -> str:
    """Get the expiry datetime for a refresh token as ISO 8601 string."""
    expiry = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return expiry.isoformat()
