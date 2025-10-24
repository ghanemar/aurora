"""Database session factory and connection management.

This module provides async database session creation and management
for PostgreSQL using SQLAlchemy's async engine.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from config.settings import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Create declarative base for ORM models
Base: Any = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency for FastAPI routes to get database session.

    Yields:
        AsyncSession: Database session instance

    Example:
        ```python
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Check database connectivity.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
