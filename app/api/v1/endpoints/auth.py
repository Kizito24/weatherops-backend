"""Authentication API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService, AuthenticationError
from app.dependencies.auth import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Register a new user account and return authentication tokens.

    Args:
        request: Registration request with email and password.
        db: Database session.

    Returns:
        Access and refresh tokens for the new user.

    Raises:
        HTTPException: If registration fails.
    """
    service = AuthService(db)

    try:
        user = await service.register_user(request.email, request.password)
        access_token, refresh_token = await service.create_tokens(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=service.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except AuthenticationError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.

    Args:
        request: Login request with email and password.
        db: Database session.

    Returns:
        Access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    service = AuthService(db)

    try:
        user = await service.authenticate_user(request.email, request.password)
        access_token, refresh_token = await service.create_tokens(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=service.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except AuthenticationError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    Args:
        request: Refresh token request.
        db: Database session.

    Returns:
        New access and refresh tokens.

    Raises:
        HTTPException: If refresh fails.
    """
    service = AuthService(db)

    try:
        new_access_token, new_refresh_token = await service.refresh_access_token(
            request.refresh_token
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=service.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from authentication dependency.

    Returns:
        Current user information.
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Logout current user by revoking all refresh tokens.

    Args:
        current_user: Current user from authentication dependency.
        db: Database session.
    """
    service = AuthService(db)
    await service.logout_user(current_user.id)
    logger.info(f"User logged out: {current_user.id}")
