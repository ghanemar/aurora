"""Pytest configuration and fixtures for Aurora test suite."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from core.models.base import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://aurora:aurora_dev@localhost:5432/aurora_test"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests.

    Each test gets a fresh session that automatically rolls back
    after the test completes, ensuring test isolation.

    Yields:
        AsyncSession: Database session for test
    """
    # Create engine for this test
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Create session
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            # Rollback any uncommitted changes
            await session.rollback()

            # Drop all tables
            async with engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.drop_all)

            await engine.dispose()
