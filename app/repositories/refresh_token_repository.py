"""Refresh token data access repository."""

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.refresh_token import RefreshToken

logger = logging.getLogger(__name__)


class RefreshTokenRepository:
    """Repository for refresh token data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository.

        Args:
            db: AsyncSession for database access.
        """
        self.db = db

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """
        Create a new refresh token.

        Args:
            user_id: User UUID.
            token_hash: Hash of the refresh token.
            expires_at: Token expiration datetime.

        Returns:
            Created RefreshToken model.
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)

        try:
            await self.db.commit()
            await self.db.refresh(token)
            logger.info(f"Refresh token created for user: {user_id}")
            return token
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"IntegrityError creating refresh token: {e}")
            raise

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Retrieve refresh token by hash.

        Args:
            token_hash: Hash of the refresh token.

        Returns:
            RefreshToken model if found, None otherwise.
        """
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(query)
        token = result.scalars().first()
        return token

    async def revoke_refresh_token(self, token_id: uuid.UUID) -> RefreshToken | None:
        """
        Revoke a refresh token.

        Args:
            token_id: RefreshToken UUID.

        Returns:
            Updated RefreshToken model if found, None otherwise.
        """
        token = await self._get_token_by_id(token_id)
        if token:
            token.revoked = True
            token.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(token)
            logger.info(f"Refresh token revoked: {token_id}")
        return token

    async def revoke_user_refresh_tokens(self, user_id: uuid.UUID) -> None:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: User UUID.
        """
        query = select(RefreshToken).where(
            (RefreshToken.user_id == user_id) & (RefreshToken.revoked == False)
        )
        result = await self.db.execute(query)
        tokens = result.scalars().all()

        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()
        logger.info(f"All refresh tokens revoked for user: {user_id}")

    async def _get_token_by_id(self, token_id: uuid.UUID) -> RefreshToken | None:
        """
        Internal method to retrieve token by ID.

        Args:
            token_id: RefreshToken UUID.

        Returns:
            RefreshToken model if found, None otherwise.
        """
        query = select(RefreshToken).where(RefreshToken.id == token_id)
        result = await self.db.execute(query)
        return result.scalars().first()
