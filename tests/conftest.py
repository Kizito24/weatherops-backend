"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import AsyncSessionLocal, get_db_session
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Yields:
        AsyncSession: Test database session.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_local = AsyncSessionLocal(bind=engine, class_=AsyncSession)

    async with async_session_local() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client.

    Args:
        test_db: Test database session.

    Yields:
        AsyncClient: Test HTTP client.
    """

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db_session] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
