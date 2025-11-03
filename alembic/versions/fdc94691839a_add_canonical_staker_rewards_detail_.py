"""add canonical staker rewards detail table for granular wallet attribution

Revision ID: fdc94691839a
Revises: 8ea71cd7ef5d
Create Date: 2025-11-03 13:09:04.592560

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fdc94691839a"
down_revision: Union[str, Sequence[str], None] = "8ea71cd7ef5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create revenue_component enum if it doesn't exist
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE revenue_component AS ENUM ('MEV', 'TIPS', 'BLOCK_REWARDS', 'CONSENSUS_REWARDS', 'EXECUTION_REWARDS', 'OTHER'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    # Create canonical_staker_rewards_detail table
    op.create_table(
        "canonical_staker_rewards_detail",
        sa.Column(
            "detail_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique detail record identifier",
        ),
        sa.Column(
            "chain_id",
            sa.String(length=50),
            nullable=False,
            comment="Reference to chain",
        ),
        sa.Column(
            "period_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to canonical period when reward was earned",
        ),
        sa.Column(
            "validator_key",
            sa.String(length=100),
            nullable=False,
            comment="Validator identifier where staker earned rewards",
        ),
        sa.Column(
            "staker_address",
            sa.String(length=100),
            nullable=False,
            comment="Staker/delegator wallet address that earned rewards",
        ),
        sa.Column(
            "revenue_component",
            postgresql.ENUM(
                "MEV",
                "TIPS",
                "BLOCK_REWARDS",
                "CONSENSUS_REWARDS",
                "EXECUTION_REWARDS",
                "OTHER",
                name="revenue_component",
                create_type=False,
            ),
            nullable=False,
            comment="Revenue component type for granular attribution",
        ),
        sa.Column(
            "reward_amount_native",
            sa.NUMERIC(38, 18),
            nullable=False,
            comment="Reward amount in native chain units (lamports, wei, etc.)",
        ),
        sa.Column(
            "stake_amount_native",
            sa.NUMERIC(38, 18),
            nullable=False,
            comment="Stake amount in native chain units during this period",
        ),
        sa.Column(
            "source_provider_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to data provider for traceability",
        ),
        sa.Column(
            "source_payload_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to staging payload for traceability",
        ),
        sa.Column(
            "normalized_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Timestamp when data was normalized",
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
            name="fk_canonical_staker_rewards_detail_chain",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["period_id"],
            ["canonical_periods.period_id"],
            name="fk_canonical_staker_rewards_detail_period",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_provider_id"],
            ["providers.provider_id"],
            name="fk_canonical_staker_rewards_detail_provider",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_payload_id"],
            ["staging_payloads.payload_id"],
            name="fk_canonical_staker_rewards_detail_payload",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "detail_id", name="pk_canonical_staker_rewards_detail"
        ),
        sa.UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            "staker_address",
            "revenue_component",
            name="uq_canonical_staker_rewards_detail_unique_record",
        ),
        sa.CheckConstraint(
            "reward_amount_native >= 0",
            name="ck_canonical_staker_rewards_detail_reward_positive",
        ),
        sa.CheckConstraint(
            "stake_amount_native > 0",
            name="ck_canonical_staker_rewards_detail_stake_positive",
        ),
        sa.CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_staker_rewards_detail_staker_not_empty",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_canonical_staker_rewards_detail_chain_period",
        "canonical_staker_rewards_detail",
        ["chain_id", "period_id"],
    )
    op.create_index(
        "idx_canonical_staker_rewards_detail_validator",
        "canonical_staker_rewards_detail",
        ["validator_key"],
    )
    op.create_index(
        "idx_canonical_staker_rewards_detail_staker",
        "canonical_staker_rewards_detail",
        ["staker_address"],
    )
    op.create_index(
        "idx_canonical_staker_rewards_detail_component",
        "canonical_staker_rewards_detail",
        ["revenue_component"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(
        "idx_canonical_staker_rewards_detail_component",
        table_name="canonical_staker_rewards_detail",
    )
    op.drop_index(
        "idx_canonical_staker_rewards_detail_staker",
        table_name="canonical_staker_rewards_detail",
    )
    op.drop_index(
        "idx_canonical_staker_rewards_detail_validator",
        table_name="canonical_staker_rewards_detail",
    )
    op.drop_index(
        "idx_canonical_staker_rewards_detail_chain_period",
        table_name="canonical_staker_rewards_detail",
    )

    # Drop canonical_staker_rewards_detail table
    op.drop_table("canonical_staker_rewards_detail")

    # Drop revenue_component enum
    op.execute("DROP TYPE IF EXISTS revenue_component")
