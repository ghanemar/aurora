"""Base repository class with common CRUD operations.

This module provides the base repository class that all specific
repositories inherit from, implementing common database operations.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.base import BaseModel

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations.

    This class provides standard database operations (Create, Read, Update, Delete)
    that can be inherited by specific repositories. It uses generic types to provide
    type-safe operations for any SQLAlchemy model.

    Attributes:
        model: The SQLAlchemy model class this repository operates on
        session: The async database session for executing queries
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Initialize repository with model class and database session.

        Args:
            model: The SQLAlchemy model class
            session: The async database session
        """
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelType | None:
        """Get a single record by ID.

        Args:
            id: The UUID primary key of the record

        Returns:
            The model instance if found, None otherwise
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """Get multiple records with pagination.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            order_by: Column name to order by (default: None)
            include_deleted: Include soft-deleted records (default: False)

        Returns:
            List of model instances
        """
        stmt = select(self.model).offset(offset).limit(limit)

        # Exclude soft-deleted records by default
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        if order_by:
            stmt = stmt.order_by(getattr(self.model, order_by))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, include_deleted: bool = False, **filters: Any) -> int:
        """Count total records matching the given filters.

        Args:
            include_deleted: Include soft-deleted records (default: False)
            **filters: Column name and value pairs to filter by

        Returns:
            Count of matching records
        """
        stmt = select(func.count()).select_from(self.model)

        # Exclude soft-deleted records by default
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **data: Any) -> ModelType:
        """Create a new record.

        Args:
            **data: Column name and value pairs for the new record

        Returns:
            The created model instance
        """
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, **data: Any) -> ModelType | None:
        """Update an existing record by ID.

        Args:
            id: The UUID primary key of the record to update
            **data: Column name and value pairs to update

        Returns:
            The updated model instance if found, None otherwise
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .execution_options(synchronize_session="fetch")
        )

        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID.

        Args:
            id: The UUID primary key of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0

    async def filter_by(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> list[ModelType]:
        """Get multiple records filtered by column values with pagination.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)
            order_by: Column name to order by (default: None)
            include_deleted: Include soft-deleted records (default: False)
            **filters: Column name and value pairs to filter by

        Returns:
            List of model instances matching the filters
        """
        stmt = select(self.model).offset(offset).limit(limit)

        # Exclude soft-deleted records by default
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        for key, value in filters.items():
            if hasattr(self.model, key):
                if value is None:
                    stmt = stmt.where(getattr(self.model, key).is_(None))
                else:
                    stmt = stmt.where(getattr(self.model, key) == value)

        if order_by:
            stmt = stmt.order_by(getattr(self.model, order_by))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, **filters: Any) -> bool:
        """Check if any records exist matching the given filters.

        Args:
            **filters: Column name and value pairs to filter by

        Returns:
            True if any matching records exist, False otherwise
        """
        stmt = select(func.count()).select_from(self.model).limit(1)

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
