"""add canonical stake events table for wallet lifecycle tracking

Revision ID: 8ea71cd7ef5d
Revises: af2383dc7482
Create Date: 2025-11-03 11:54:33.074180

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8ea71cd7ef5d"
down_revision: Union[str, Sequence[str], None] = "af2383dc7482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create stake_event_type enum if it doesn't exist
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE stake_event_type AS ENUM ('STAKE', 'UNSTAKE', 'RESTAKE'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    # Create canonical_stake_events table
    op.create_table(
        "canonical_stake_events",
        sa.Column(
            "stake_event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique stake event identifier",
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
            comment="Reference to canonical period when event occurred",
        ),
        sa.Column(
            "validator_key",
            sa.String(length=100),
            nullable=False,
            comment="Validator identifier where staking action occurred",
        ),
        sa.Column(
            "staker_address",
            sa.String(length=100),
            nullable=False,
            comment="Staker/delegator wallet address",
        ),
        sa.Column(
            "event_type",
            postgresql.ENUM("STAKE", "UNSTAKE", "RESTAKE", name="stake_event_type", create_type=False),
            nullable=False,
            comment="Type of staking lifecycle event",
        ),
        sa.Column(
            "stake_amount_native",
            sa.NUMERIC(38, 18),
            nullable=False,
            comment="Stake amount in native chain units (lamports, wei, etc.)",
        ),
        sa.Column(
            "event_timestamp",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Timestamp when staking event occurred",
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
            name="fk_canonical_stake_events_chain",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["period_id"],
            ["canonical_periods.period_id"],
            name="fk_canonical_stake_events_period",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_provider_id"],
            ["providers.provider_id"],
            name="fk_canonical_stake_events_provider",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_payload_id"],
            ["staging_payloads.payload_id"],
            name="fk_canonical_stake_events_payload",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("stake_event_id", name="pk_canonical_stake_events"),
        sa.CheckConstraint(
            "stake_amount_native >= 0",
            name="ck_canonical_stake_events_amount_positive",
        ),
        sa.CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_stake_events_staker_not_empty",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "idx_canonical_stake_events_chain_period",
        "canonical_stake_events",
        ["chain_id", "period_id"],
    )
    op.create_index(
        "idx_canonical_stake_events_validator",
        "canonical_stake_events",
        ["validator_key"],
    )
    op.create_index(
        "idx_canonical_stake_events_staker",
        "canonical_stake_events",
        ["staker_address"],
    )
    op.create_index(
        "idx_canonical_stake_events_timestamp",
        "canonical_stake_events",
        ["event_timestamp"],
    )
    op.create_index(
        "idx_canonical_stake_events_type",
        "canonical_stake_events",
        ["event_type"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_canonical_stake_events_type", table_name="canonical_stake_events")
    op.drop_index("idx_canonical_stake_events_timestamp", table_name="canonical_stake_events")
    op.drop_index("idx_canonical_stake_events_staker", table_name="canonical_stake_events")
    op.drop_index("idx_canonical_stake_events_validator", table_name="canonical_stake_events")
    op.drop_index("idx_canonical_stake_events_chain_period", table_name="canonical_stake_events")

    # Drop canonical_stake_events table
    op.drop_table("canonical_stake_events")

    # Drop stake_event_type enum
    op.execute("DROP TYPE stake_event_type")
