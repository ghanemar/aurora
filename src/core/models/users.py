"""User authentication and authorization models.

This module defines the User model for the authentication system.
Users can have different roles (ADMIN or PARTNER) and are used for
accessing the admin dashboard and API.
"""

import enum
import uuid
from typing import Optional

from sqlalchemy import Column, Enum, String, Boolean, Uuid, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserRole(enum.Enum):
    """User role enumeration for role-based access control.

    Attributes:
        ADMIN: Administrator with full system access
        PARTNER: Partner user with access to their own data
    """

    ADMIN = "admin"
    PARTNER = "partner"


class User(BaseModel):
    """User model for authentication and authorization.

    Attributes:
        id: Unique user identifier (UUID)
        username: Unique username for login
        email: User email address (unique)
        hashed_password: Bcrypt-hashed password
        full_name: User's full name
        role: User role (ADMIN or PARTNER)
        is_active: Whether the user account is active
        partner_id: Optional foreign key to Partners table (for PARTNER role)
        partner: Relationship to Partners model
    """

    __tablename__ = "users"

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier",
    )

    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique username for login",
    )

    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User email address",
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt-hashed password",
    )

    full_name = Column(
        String(100),
        nullable=False,
        comment="User's full name",
    )

    role = Column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.ADMIN,
        comment="User role for access control",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the user account is active",
    )

    partner_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("partners.partner_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        comment="Foreign key to partners table (for PARTNER role)",
    )

    # Relationships
    # Note: The Partners model has a back_populates="users" relationship
    # that will be defined when the Partners model exists
    # partner = relationship("Partners", back_populates="users")

    def __repr__(self) -> str:
        """String representation of User instance.

        Returns:
            str: User representation with username and role
        """
        return f"User(id={self.id!r}, username={self.username!r}, role={self.role.value})"


# Create composite index on frequently queried columns
Index("ix_users_username_email", User.username, User.email)
