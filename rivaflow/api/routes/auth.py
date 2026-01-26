"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

from rivaflow.core.services.auth_service import AuthService
from rivaflow.core.dependencies import get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request model."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str


class LoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Authentication token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class AccessTokenResponse(BaseModel):
    """Access token only response model (for refresh)."""

    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **first_name**: User's first name
    - **last_name**: User's last name

    Returns access token, refresh token, and user information.
    """
    service = AuthService()

    try:
        result = service.register(
            email=req.email,
            password=req.password,
            first_name=req.first_name,
            last_name=req.last_name,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Login with email and password.

    - **email**: User's email address
    - **password**: User's password

    Returns access token, refresh token, and user information.
    """
    service = AuthService()

    try:
        result = service.login(email=req.email, password=req.password)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(req: RefreshRequest):
    """
    Refresh access token using a refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token.
    """
    service = AuthService()

    try:
        result = service.refresh_access_token(refresh_token=req.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.post("/logout")
async def logout(req: RefreshRequest, current_user: dict = Depends(get_current_user)):
    """
    Logout by invalidating the refresh token.

    - **refresh_token**: Refresh token to invalidate

    Requires authentication (access token in Authorization header).
    """
    service = AuthService()

    try:
        success = service.logout(refresh_token=req.refresh_token)
        if success:
            return {"message": "Logged out successfully"}
        else:
            return {"message": "Refresh token not found or already invalid"}
    except Exception as e:
        print(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


@router.post("/logout-all")
async def logout_all_devices(current_user: dict = Depends(get_current_user)):
    """
    Logout from all devices by invalidating all refresh tokens.

    Requires authentication (access token in Authorization header).
    """
    service = AuthService()

    try:
        count = service.logout_all_devices(user_id=current_user["id"])
        return {"message": f"Logged out from {count} device(s)"}
    except Exception as e:
        print(f"Logout all error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires authentication (access token in Authorization header).
    """
    return current_user
