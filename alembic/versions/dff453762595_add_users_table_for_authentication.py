"""add users table for authentication

Revision ID: dff453762595
Revises: cec3a80e61a4
Create Date: 2025-10-28 15:25:30.145716

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dff453762595"
down_revision: Union[str, Sequence[str], None] = "cec3a80e61a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add users table for authentication."""
    # Create UserRole enum
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'partner')")

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            comment="Unique user identifier",
        ),
        sa.Column(
            "username",
            sa.String(50),
            nullable=False,
            unique=True,
            comment="Unique username for login",
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False,
            unique=True,
            comment="User email address",
        ),
        sa.Column(
            "hashed_password",
            sa.String(255),
            nullable=False,
            comment="Bcrypt-hashed password",
        ),
        sa.Column(
            "full_name",
            sa.String(100),
            nullable=False,
            comment="User's full name",
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
            server_default="admin",
            comment="User role for access control",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the user account is active",
        ),
        sa.Column(
            "partner_id",
            sa.Uuid(),
            sa.ForeignKey("partners.partner_id", ondelete="RESTRICT"),
            nullable=True,
            comment="Foreign key to partners table (for PARTNER role)",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Timestamp when record was created",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Timestamp when record was last updated",
        ),
    )

    # Add CHECK constraint for role values
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'partner'))"
    )

    # Drop the default, convert to enum type, then re-add default
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'admin'::userrole")

    # Create indexes
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_partner_id", "users", ["partner_id"], unique=False)
    op.create_index("ix_users_username_email", "users", ["username", "email"], unique=False)


def downgrade() -> None:
    """Downgrade schema: Remove users table."""
    # Drop indexes
    op.drop_index("ix_users_username_email", table_name="users")
    op.drop_index("ix_users_partner_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")

    # Drop table
    op.drop_table("users")

    # Drop enum using raw SQL
    op.execute("DROP TYPE IF EXISTS userrole")
