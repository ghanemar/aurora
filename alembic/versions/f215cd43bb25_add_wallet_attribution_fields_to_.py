"""add wallet attribution fields to agreements and commission lines

Revision ID: f215cd43bb25
Revises: fdc94691839a
Create Date: 2025-11-03 13:09:50.618089

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f215cd43bb25"
down_revision: Union[str, Sequence[str], None] = "fdc94691839a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add wallet_attribution_enabled to agreements table
    op.add_column(
        "agreements",
        sa.Column(
            "wallet_attribution_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Enable wallet-level commission attribution for this agreement",
        ),
    )

    # Add wallet_address to partner_commission_lines table
    op.add_column(
        "partner_commission_lines",
        sa.Column(
            "wallet_address",
            sa.String(length=100),
            nullable=True,
            comment="Optional wallet address for granular attribution (NULL = validator-level)",
        ),
    )

    # Create index on wallet_address for efficient filtering
    op.create_index(
        "idx_partner_commission_lines_wallet",
        "partner_commission_lines",
        ["wallet_address"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index(
        "idx_partner_commission_lines_wallet",
        table_name="partner_commission_lines",
    )

    # Drop wallet_address column
    op.drop_column("partner_commission_lines", "wallet_address")

    # Drop wallet_attribution_enabled column
    op.drop_column("agreements", "wallet_attribution_enabled")
