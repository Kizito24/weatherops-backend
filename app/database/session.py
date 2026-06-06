"""
Database session factory and dependency injection.
Provides async SQLAlchemy sessions with proper lifecycle management.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
}

# Pool parameters are only supported for non-SQLite databases
if "sqlite" not in settings.DATABASE_URL.lower():
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": settings.DATABASE_POOL_PRE_PING,
        "pool_recycle": 3600,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.

    Yields:
        AsyncSession: Database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_engine():
    """Get database engine."""
    return engine
