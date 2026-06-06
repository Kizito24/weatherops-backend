"""FastAPI authentication dependencies."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.user import User
from app.services.auth_service import AuthService, AuthenticationError

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    FastAPI dependency to extract and validate current user from token.

    Args:
        authorization: Bearer token from Authorization header.
        db: Database session.

    Returns:
        Current User model.

    Raises:
        HTTPException: If authentication fails.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    token = authorization
    if token.startswith("Bearer "):
        token = token[7:]
    elif token.startswith("bearer "):
        token = token[7:]

    service = AuthService(db)

    try:
        user = await service.get_current_user(token)
        return user
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency to ensure user is active.

    Args:
        current_user: Current user from get_current_user dependency.

    Returns:
        Current User model if active.

    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


# Type annotation for convenience
CurrentUser = Annotated[User, Depends(get_current_active_user)]
