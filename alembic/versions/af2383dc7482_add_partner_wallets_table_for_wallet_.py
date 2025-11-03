"""add partner wallets table for wallet attribution

Revision ID: af2383dc7482
Revises: 77e46e2d0509
Create Date: 2025-11-03 11:53:17.119092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "af2383dc7482"
down_revision: Union[str, Sequence[str], None] = "77e46e2d0509"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create partner_wallets table
    op.create_table(
        "partner_wallets",
        sa.Column(
            "wallet_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique wallet record identifier",
        ),
        sa.Column(
            "partner_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to partner who introduced this wallet",
        ),
        sa.Column(
            "chain_id",
            sa.String(length=50),
            nullable=False,
            comment="Reference to chain",
        ),
        sa.Column(
            "wallet_address",
            sa.String(length=100),
            nullable=False,
            comment="Staker/delegator wallet public key address",
        ),
        sa.Column(
            "introduced_date",
            sa.Date(),
            nullable=False,
            comment="Date when partner introduced this wallet (supports retroactive)",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Soft delete flag",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Optional notes about this wallet",
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Timestamp when record was created",
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Timestamp when record was last updated",
        ),
        sa.ForeignKeyConstraint(
            ["chain_id"],
            ["chains.chain_id"],
            name="fk_partner_wallets_chain",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["partners.partner_id"],
            name="fk_partner_wallets_partner",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("wallet_id", name="pk_partner_wallets"),
        sa.UniqueConstraint(
            "chain_id",
            "wallet_address",
            name="uq_partner_wallets_chain_address",
        ),
        sa.CheckConstraint(
            "wallet_address <> ''",
            name="ck_partner_wallets_address_not_empty",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_partner_wallets_partner",
        "partner_wallets",
        ["partner_id"],
    )
    op.create_index(
        "idx_partner_wallets_chain",
        "partner_wallets",
        ["chain_id"],
    )
    op.create_index(
        "idx_partner_wallets_address",
        "partner_wallets",
        ["wallet_address"],
    )
    op.create_index(
        "idx_partner_wallets_active",
        "partner_wallets",
        ["is_active"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_partner_wallets_active", table_name="partner_wallets")
    op.drop_index("idx_partner_wallets_address", table_name="partner_wallets")
    op.drop_index("idx_partner_wallets_chain", table_name="partner_wallets")
    op.drop_index("idx_partner_wallets_partner", table_name="partner_wallets")

    # Drop partner_wallets table
    op.drop_table("partner_wallets")
