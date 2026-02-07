"""FastAPI dependency injection for authentication."""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from rivaflow.core.auth import decode_access_token
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User dictionary with id, email, first_name, last_name, etc.

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    token = credentials.credentials

    try:
        # Decode JWT token
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_str = payload.get("sub")
        user_id: int = int(user_id_str) if user_id_str else None

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Remove sensitive fields
        user.pop("hashed_password", None)

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except (ValueError, KeyError, TypeError) as e:
        # Log unexpected errors and return generic 401
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures the current user is active.
    This is redundant with get_current_user but kept for semantic clarity.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active user dictionary

    Raises:
        HTTPException: 401 if user is not active
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    return current_user


def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures the current user is an admin.

    Use this dependency on admin-only endpoints to restrict access.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Admin user dictionary

    Raises:
        HTTPException: 403 Forbidden if user is not an admin
    """
    if not current_user.get("is_admin"):
        logger.warning(
            f"Non-admin user {current_user.get('email')} attempted to access admin endpoint"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This incident will be logged.",
        )
    return current_user
