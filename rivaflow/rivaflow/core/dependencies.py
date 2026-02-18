"""FastAPI dependency injection for authentication and services."""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

from rivaflow.core.auth import decode_access_token
from rivaflow.core.utils.cache import get_cache
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# User cache TTL — short enough that permission changes propagate quickly
_USER_CACHE_TTL = 60  # seconds

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Uses a short-lived in-memory cache to avoid hitting the database
    on every single authenticated request.

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

        # Check cache first
        cache = get_cache()
        cache_key = f"user:{user_id}"
        from rivaflow.core.utils.cache import _MISSING

        cached_user = cache.get(cache_key)
        if cached_user is not _MISSING:
            return cached_user

        # Cache miss — fetch from database
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

        # Cache the user for subsequent requests
        cache.set(cache_key, user, _USER_CACHE_TTL)

        return user

    except PyJWTError:
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


# ---------------------------------------------------------------------------
# Service provider functions for Depends() injection
# ---------------------------------------------------------------------------


def get_session_service():
    """Provide a SessionService instance."""
    from rivaflow.core.services.session_service import SessionService

    return SessionService()


def get_analytics_service():
    """Provide an AnalyticsService instance."""
    from rivaflow.core.services.analytics_service import AnalyticsService

    return AnalyticsService()


def get_goals_service():
    """Provide a GoalsService instance."""
    from rivaflow.core.services.goals_service import GoalsService

    return GoalsService()


def get_social_service():
    """Provide a SocialService instance."""
    from rivaflow.core.services.social_service import SocialService

    return SocialService()


def get_profile_service():
    """Provide a ProfileService instance."""
    from rivaflow.core.services.profile_service import ProfileService

    return ProfileService()
