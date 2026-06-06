"""
Security utilities including JWT token handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def create_access_token(
    subject: str, expires_delta: timedelta | None = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject to encode (typically a user ID).
        expires_delta: Optional token expiration time delta.

    Returns:
        Encoded JWT token.
    """
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> str:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify.

    Returns:
        The subject (user ID) from the token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    settings = get_settings()
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    subject: str = payload.get("sub")
    if subject is None:
        raise JWTError("Invalid token")
    return subject
