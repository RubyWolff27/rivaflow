"""Authentication endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.api.response_models import CurrentUserResponse
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import handle_service_error
from rivaflow.core.exceptions import (
    AuthenticationError,
    RivaFlowException,
    ValidationError,
)
from rivaflow.core.services.auth_service import AuthService
from rivaflow.core.settings import settings
from rivaflow.db.repositories.waitlist_repo import WaitlistRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def _set_refresh_cookie(response: Response, token: str):
    """Set the refresh token as an httpOnly cookie."""
    response.set_cookie(
        key="rf_token",
        value=token,
        httponly=True,
        secure=settings.IS_PRODUCTION,
        samesite="lax",
        path="/api",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie(key="rf_token", path="/api")


class RegisterRequest(BaseModel):
    """User registration request model."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str
    last_name: str
    invite_token: str | None = None
    default_gym: str | None = None
    current_grade: str | None = None


class LoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str = Field(..., max_length=128)


class TokenResponse(BaseModel):
    """Authentication token response model."""

    access_token: str
    token_type: str = "bearer"
    user: CurrentUserResponse


class AccessTokenResponse(BaseModel):
    """Access token only response model (for refresh)."""

    access_token: str
    token_type: str = "bearer"


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register(request: Request, req: RegisterRequest, response: Response):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **invite_token**: Waitlist invite token (required in production)

    Returns access token, refresh token, and user information.
    """
    waitlist_repo = WaitlistRepository()

    # When waitlist is enabled, require a valid invite token
    if settings.WAITLIST_ENABLED:
        if not req.invite_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration requires an invite. Join the waitlist at rivaflow.app/waitlist",
            )

        if not waitlist_repo.is_invite_valid(req.invite_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired invite token. Please request a new invite.",
            )

    # If invite_token is provided but waitlist is not enforced, still validate
    if req.invite_token and not settings.WAITLIST_ENABLED:
        if not waitlist_repo.is_invite_valid(req.invite_token):
            logger.warning(
                f"Invalid invite token used in {settings.ENV} for {req.email[:3]}***"
            )

    service = AuthService()

    try:
        result = service.register(
            email=req.email,
            password=req.password,
            first_name=req.first_name,
            last_name=req.last_name,
            default_gym=req.default_gym,
            current_grade=req.current_grade,
        )

        # Mark the waitlist entry as registered if an invite token was used
        if req.invite_token:
            try:
                waitlist_repo.mark_registered(req.email)
            except (ConnectionError, OSError) as e:
                logger.error(
                    f"Failed to mark waitlist entry as registered for {req.email[:3]}***: {e}"
                )

        _set_refresh_cookie(response, result["refresh_token"])
        return result
    except ValueError as e:
        # ValueError contains user-facing validation messages
        raise ValidationError(str(e))
    except RivaFlowException:
        raise
    except KeyError as e:
        error_msg = handle_service_error(e, "Registration failed", operation="register")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest, response: Response):
    """
    Login with email and password.

    - **email**: User's email address
    - **password**: User's password

    Returns access token and user information. Refresh token is set as httpOnly cookie.
    """
    service = AuthService()

    try:
        result = service.login(email=req.email, password=req.password)
        _set_refresh_cookie(response, result["refresh_token"])
        return result
    except (ValueError, AuthenticationError):
        # Auth failures - use generic message to prevent user enumeration
        logger.warning(f"Login attempt failed for {req.email[:3]}***")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except KeyError as e:
        error_msg = handle_service_error(e, "Login failed", operation="login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit("10/minute")
def refresh_token(request: Request, response: Response):
    """
    Refresh access token using the httpOnly refresh token cookie.

    Returns new access token.
    """
    token = request.cookies.get("rf_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = AuthService()

    try:
        result = service.refresh_access_token(refresh_token=token)
        # Set the rotated refresh token cookie (not the old one)
        _set_refresh_cookie(response, result["refresh_token"])
        return result
    except ValueError:
        logger.warning("Token refresh failed")
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except RivaFlowException:
        raise
    except KeyError as e:
        error_msg = handle_service_error(
            e, "Token refresh failed", operation="refresh_token"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """
    Logout by invalidating the refresh token cookie.

    Requires authentication (access token in Authorization header).
    """
    token = request.cookies.get("rf_token")
    if token:
        service = AuthService()
        try:
            service.logout(refresh_token=token)
        except RivaFlowException:
            raise
        except (ValueError, KeyError) as e:
            error_msg = handle_service_error(
                e, "Logout failed", user_id=current_user["id"], operation="logout"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )

    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
def logout_all_devices(
    response: Response, current_user: dict = Depends(get_current_user)
):
    """
    Logout from all devices by invalidating all refresh tokens.

    Requires authentication (access token in Authorization header).
    """
    service = AuthService()

    try:
        count = service.logout_all_devices(user_id=current_user["id"])
        _clear_refresh_cookie(response)
        return {"message": f"Logged out from {count} device(s)"}
    except RivaFlowException:
        raise
    except (ValueError, KeyError) as e:
        error_msg = handle_service_error(
            e, "Logout failed", user_id=current_user["id"], operation="logout_all"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires authentication (access token in Authorization header).
    """
    return current_user


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/forgot-password")
@limiter.limit("3/hour")
def forgot_password(request: Request, req: ForgotPasswordRequest):
    """
    Request a password reset email.

    Rate limited to 3 requests per hour per IP address.

    - **email**: User's email address

    Returns success message regardless of whether email exists (prevents user enumeration).
    """
    service = AuthService()

    try:
        # Always return success to prevent user enumeration
        # The service will only send email if user exists
        service.request_password_reset(email=req.email)
        return {
            "message": "If an account exists with this email, you will receive a password reset link."
        }
    except Exception as e:
        logger.error(f"Forgot password error for {req.email[:3]}***: {e}")
        # Still return success to prevent info leakage
        return {
            "message": "If an account exists with this email, you will receive a password reset link."
        }


@router.post("/reset-password")
@limiter.limit("5/hour")
def reset_password(request: Request, req: ResetPasswordRequest):
    """
    Reset password using reset token.

    Rate limited to 5 requests per hour per IP address.

    - **token**: Password reset token from email
    - **new_password**: New password (min 8 characters)

    Returns success or error message.
    """
    service = AuthService()

    try:
        success = service.reset_password(token=req.token, new_password=req.new_password)
    except ValueError as e:
        raise ValidationError(str(e))
    except HTTPException:
        raise
    except KeyError as e:
        error_msg = handle_service_error(
            e, "Password reset failed", operation="reset_password"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        )

    if success:
        return {
            "message": "Password reset successfully. You can now log in with your new password."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
