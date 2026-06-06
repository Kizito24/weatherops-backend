"""JWT token encoding and decoding utilities."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Base exception for token-related errors."""

    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""

    pass


class InvalidTokenError(TokenError):
    """Raised when a token is invalid or malformed."""

    pass


def encode_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Encode a JWT token.

    Args:
        subject: Subject to encode (typically user_id).
        token_type: Type of token ('access' or 'refresh').
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT token string.
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Use default based on token type
        if token_type == "access":
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        elif token_type == "refresh":
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        else:
            raise ValueError(f"Unknown token type: {token_type}")

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # Unique token ID to prevent collisions
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        Decoded token payload as dictionary.

    Raises:
        TokenExpiredError: If token has expired.
        InvalidTokenError: If token is invalid or malformed.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError("Token has expired") from e
        raise InvalidTokenError("Invalid token") from e


def verify_token_type(payload: dict[str, Any], expected_type: str) -> None:
    """
    Verify that a token has the expected type.

    Args:
        payload: Decoded token payload.
        expected_type: Expected token type ('access' or 'refresh').

    Raises:
        InvalidTokenError: If token type doesn't match.
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise InvalidTokenError(
            f"Invalid token type. Expected {expected_type}, got {token_type}"
        )


def extract_user_id(payload: dict[str, Any]) -> str:
    """
    Extract user_id from token payload.

    Args:
        payload: Decoded token payload.

    Returns:
        User ID as string.

    Raises:
        InvalidTokenError: If user_id is missing.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token: missing user_id")
    return user_id
