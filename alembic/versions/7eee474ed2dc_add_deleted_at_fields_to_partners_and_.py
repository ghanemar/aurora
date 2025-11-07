"""add_deleted_at_fields_to_partners_and_agreements

Revision ID: 7eee474ed2dc
Revises: f215cd43bb25
Create Date: 2025-11-06 13:36:28.098737

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7eee474ed2dc"
down_revision: Union[str, Sequence[str], None] = "f215cd43bb25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add deleted_at column to partners table
    op.add_column(
        "partners",
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Soft-delete timestamp",
        ),
    )
    op.create_index("idx_partners_deleted", "partners", ["deleted_at"])

    # Add deleted_at column to agreements table
    op.add_column(
        "agreements",
        sa.Column(
            "deleted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Soft-delete timestamp",
        ),
    )
    op.create_index("idx_agreements_deleted", "agreements", ["deleted_at"])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove deleted_at column from agreements table
    op.drop_index("idx_agreements_deleted", table_name="agreements")
    op.drop_column("agreements", "deleted_at")

    # Remove deleted_at column from partners table
    op.drop_index("idx_partners_deleted", table_name="partners")
    op.drop_column("partners", "deleted_at")
