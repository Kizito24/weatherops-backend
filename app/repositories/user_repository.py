"""User data access repository."""

import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository.

        Args:
            db: AsyncSession for database access.
        """
        self.db = db

    async def create_user(self, email: str, hashed_password: str) -> User:
        """
        Create a new user.

        Args:
            email: User email address.
            hashed_password: Hashed password.

        Returns:
            Created User model.

        Raises:
            ValueError: If email already exists.
        """
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)

        try:
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User created: {email}")
            return user
        except IntegrityError as e:
            await self.db.rollback()
            if "users_email_key" in str(e):
                raise ValueError(f"User with email {email} already exists") from e
            raise

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve user by email.

        Args:
            email: User email address.

        Returns:
            User model if found, None otherwise.
        """
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Retrieve user by ID.

        Args:
            user_id: User UUID.

        Returns:
            User model if found, None otherwise.
        """
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def get_active_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Retrieve active user by ID.

        Args:
            user_id: User UUID.

        Returns:
            User model if found and active, None otherwise.
        """
        query = select(User).where(
            (User.id == user_id) & (User.is_active == True)
        )
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> User | None:
        """
        Deactivate a user.

        Args:
            user_id: User UUID.

        Returns:
            Updated User model if found, None otherwise.
        """
        user = await self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"User deactivated: {user.email}")
        return user
