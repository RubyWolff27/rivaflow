"""
Tier Check Middleware
Decorators for enforcing tier-based access control on API routes
"""

from functools import wraps

from fastapi import HTTPException, Request, status

from rivaflow.core.services.tier_access_service import TierAccessService


def require_feature(feature: str):
    """
    Decorator to require a specific feature for route access

    Usage:
        @router.get("/advanced-analytics")
        @require_feature("advanced_analytics")
        async def get_advanced_analytics(request: Request, current_user=Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            kwargs.get("request") or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_tier = current_user.get("subscription_tier", "free")
            has_access, error_msg = TierAccessService.check_tier_access(
                user_tier, feature
            )

            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg or "Access denied",
                    headers={"X-Upgrade-Required": "true"},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def check_limit(feature: str, increment: bool = True):
    """
    Decorator to check feature usage limits

    Usage:
        @router.post("/friends/add")
        @check_limit("max_friends", increment=True)
        async def add_friend(request: Request, current_user=Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_id = current_user["id"]
            user_tier = current_user.get("subscription_tier", "free")

            allowed, error_msg, current_count = TierAccessService.check_usage_limit(
                user_id, user_tier, feature, increment=increment
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_msg or "Usage limit exceeded",
                    headers={
                        "X-Upgrade-Required": "true",
                        "X-Current-Usage": str(current_count),
                    },
                )

            # Add usage info to request state
            if hasattr(kwargs.get("request"), "state"):
                kwargs["request"].state.feature_usage = {
                    "feature": feature,
                    "current": current_count,
                    "incremented": increment,
                }

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_premium():
    """
    Decorator to require premium tier (premium, lifetime_premium, or admin)

    Usage:
        @router.get("/premium-feature")
        @require_premium()
        async def get_premium_feature(request: Request, current_user=Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_tier = current_user.get("subscription_tier", "free")

            if user_tier not in ["premium", "lifetime_premium", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This feature requires a Premium subscription.",
                    headers={"X-Upgrade-Required": "true"},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin():
    """
    Decorator to require admin tier

    Usage:
        @router.post("/admin/verify-gym")
        @require_admin()
        async def verify_gym(request: Request, current_user=Depends(get_current_user)):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_tier = current_user.get("subscription_tier", "free")

            if user_tier != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrative access required.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
