"""Authentication business logic service."""

import asyncio
import uuid
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import (
    encode_token,
    decode_token,
    extract_user_id,
    verify_token_type,
    TokenError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Lock to prevent concurrent refresh token operations for the same user
_refresh_locks: dict[uuid.UUID, asyncio.Lock] = {}


def _get_refresh_lock(user_id: uuid.UUID) -> asyncio.Lock:
    """Get or create a lock for a user's refresh token operations."""
    if user_id not in _refresh_locks:
        _refresh_locks[user_id] = asyncio.Lock()
    return _refresh_locks[user_id]


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize auth service.

        Args:
            db: AsyncSession for database access.
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)
        self.settings = get_settings()

    async def register_user(self, email: str, password: str) -> User:
        """
        Register a new user.

        Args:
            email: User email address.
            password: User password (plaintext).

        Returns:
            Created User model.

        Raises:
            AuthenticationError: If registration fails.
        """
        if len(password) < 8:
            raise AuthenticationError("Password must be at least 8 characters")

        hashed = hash_password(password)

        try:
            user = await self.user_repo.create_user(email, hashed)
            logger.info(f"User registered successfully: {email}")
            return user
        except ValueError as e:
            logger.warning(f"Registration failed: {e}")
            raise AuthenticationError(str(e)) from e

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate a user by email and password.

        Args:
            email: User email address.
            password: User password (plaintext).

        Returns:
            Authenticated User model.

        Raises:
            AuthenticationError: If authentication fails.
        """
        user = await self.user_repo.get_user_by_email(email)

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            logger.warning(f"Login attempt by inactive user: {email}")
            raise AuthenticationError("User account is inactive")

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt: {email}")
            raise AuthenticationError("Invalid email or password")

        logger.info(f"User authenticated successfully: {email}")
        return user

    async def create_tokens(self, user_id: uuid.UUID) -> tuple[str, str]:
        """
        Create access and refresh tokens for a user.

        Args:
            user_id: User UUID.

        Returns:
            Tuple of (access_token, refresh_token).
        """
        # Create access token
        access_token = encode_token(
            subject=str(user_id),
            token_type="access",
        )

        # Create refresh token
        refresh_token = encode_token(
            subject=str(user_id),
            token_type="refresh",
        )

        # Store refresh token hash in database
        token_hash = self._hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.token_repo.create_refresh_token(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Create new access token using a refresh token.

        Args:
            refresh_token: Refresh token string.

        Returns:
            Tuple of (new_access_token, new_refresh_token).

        Raises:
            AuthenticationError: If refresh token is invalid.
        """
        try:
            # Decode and validate refresh token
            payload = decode_token(refresh_token)
            verify_token_type(payload, "refresh")
            user_id_str = extract_user_id(payload)
            user_id = uuid.UUID(user_id_str)

            # Use a lock to prevent concurrent refresh operations for the same user
            lock = _get_refresh_lock(user_id)
            async with lock:
                # Check if token is stored and valid in database
                token_hash = self._hash_token(refresh_token)
                stored_token = await self.token_repo.get_refresh_token_by_hash(token_hash)

                if not stored_token or not stored_token.is_valid():
                    logger.warning(f"Invalid refresh token used for user: {user_id}")
                    raise AuthenticationError("Refresh token is invalid or revoked")

                # Verify user exists and is active
                user = await self.user_repo.get_active_user_by_id(user_id)
                if not user:
                    logger.warning(f"Refresh attempt for non-existent/inactive user: {user_id}")
                    raise AuthenticationError("User not found or inactive")

                # Revoke old refresh token
                await self.token_repo.revoke_refresh_token(stored_token.id)

                # Create new tokens
                new_access_token, new_refresh_token = await self.create_tokens(user_id)

                logger.info(f"Access token refreshed for user: {user_id}")
                return new_access_token, new_refresh_token

        except TokenError as e:
            logger.warning(f"Token refresh failed: {e}")
            raise AuthenticationError("Invalid refresh token") from e

    async def verify_access_token(self, token: str) -> uuid.UUID:
        """
        Verify an access token and extract user_id.

        Args:
            token: Access token string.

        Returns:
            User UUID.

        Raises:
            AuthenticationError: If token is invalid.
        """
        try:
            payload = decode_token(token)
            verify_token_type(payload, "access")
            user_id_str = extract_user_id(payload)
            return uuid.UUID(user_id_str)
        except TokenError as e:
            raise AuthenticationError("Invalid or expired access token") from e

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.

        Args:
            token: Access token string.

        Returns:
            User model.

        Raises:
            AuthenticationError: If token is invalid or user not found.
        """
        user_id = await self.verify_access_token(token)
        user = await self.user_repo.get_active_user_by_id(user_id)

        if not user:
            raise AuthenticationError("User not found")

        return user

    async def logout_user(self, user_id: uuid.UUID) -> None:
        """
        Logout user by revoking all refresh tokens.

        Args:
            user_id: User UUID.
        """
        await self.token_repo.revoke_user_refresh_tokens(user_id)
        logger.info(f"User logged out: {user_id}")

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash a token for secure storage.

        Args:
            token: Token string.

        Returns:
            Hashed token.
        """
        return hashlib.sha256(token.encode()).hexdigest()
