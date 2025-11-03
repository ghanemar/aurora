"""Base model class with common fields for all ORM models.

This module provides the base SQLAlchemy model class with standard
timestamp fields and common functionality.
"""

from typing import Any

from sqlalchemy import TIMESTAMP, Column
from sqlalchemy.sql import func

from src.db.session import Base as DeclarativeBase


class BaseModel(DeclarativeBase):
    """Abstract base class for all database models.

    Provides common timestamp fields (created_at, updated_at) that are
    automatically managed by the database.

    Attributes:
        created_at: Timestamp when record was created (auto-set on insert)
        updated_at: Timestamp when record was last modified (auto-updated)
    """

    __abstract__ = True

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created",
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when record was last updated",
    )

    def __repr__(self) -> str:
        """String representation of model instance.

        Returns:
            str: Class name and primary key value(s)
        """
        # Get primary key columns
        pk_columns = [col.name for col in self.__table__.primary_key.columns]
        pk_values = ", ".join(f"{col}={getattr(self, col)!r}" for col in pk_columns)
        return f"{self.__class__.__name__}({pk_values})"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of model with column names as keys
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
