"""add sample data tables for commission testing

Revision ID: b4ac4c9c08d6
Revises: 7eee474ed2dc
Create Date: 2025-11-09 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b4ac4c9c08d6"
down_revision: Union[str, Sequence[str], None] = "7eee474ed2dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create sample data tables for commission testing."""

    # Create sample_validator_epoch_summary table
    op.create_table(
        "sample_validator_epoch_summary",
        sa.Column(
            "summary_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique summary record identifier",
        ),
        sa.Column(
            "validator_vote_pubkey",
            sa.String(length=44),
            nullable=False,
            comment="Validator vote account public key",
        ),
        sa.Column(
            "validator_node_pubkey",
            sa.String(length=44),
            nullable=False,
            comment="Validator node public key",
        ),
        sa.Column(
            "epoch",
            sa.Integer(),
            nullable=False,
            comment="Solana epoch number (800-860 in sample data)",
        ),
        sa.Column(
            "commission_bps",
            sa.Integer(),
            nullable=False,
            comment="Validator commission rate in basis points (5% = 500)",
        ),
        sa.Column(
            "rpc_activated_stake_lamports",
            sa.BigInteger(),
            nullable=True,
            comment="Activated stake from RPC (may differ from active)",
        ),
        sa.Column(
            "total_delegated_stake_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Total delegated stake including inactive",
        ),
        sa.Column(
            "total_active_stake_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Active stake earning rewards",
        ),
        sa.Column(
            "total_activating_stake_lamports",
            sa.BigInteger(),
            nullable=True,
            comment="Stake in warmup period",
        ),
        sa.Column(
            "total_deactivating_stake_lamports",
            sa.BigInteger(),
            nullable=True,
            comment="Stake in cooldown period",
        ),
        sa.Column(
            "total_stakers",
            sa.Integer(),
            nullable=False,
            comment="Count of unique stake accounts (178 in sample)",
        ),
        sa.Column(
            "last_vote",
            sa.BigInteger(),
            nullable=True,
            comment="Last vote slot number",
        ),
        sa.Column(
            "root_slot",
            sa.BigInteger(),
            nullable=True,
            comment="Root slot number",
        ),
        sa.Column(
            "epoch_vote_account",
            sa.Integer(),
            nullable=True,
            comment="Epoch vote account flag",
        ),
        sa.Column(
            "is_delinquent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether validator was delinquent this epoch",
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
        sa.CheckConstraint(
            "commission_bps >= 0 AND commission_bps <= 10000",
            name="ck_sample_epoch_summary_commission_valid",
        ),
        sa.CheckConstraint(
            "total_delegated_stake_lamports >= 0",
            name="ck_sample_epoch_summary_delegated_stake_positive",
        ),
        sa.CheckConstraint(
            "total_active_stake_lamports >= 0",
            name="ck_sample_epoch_summary_active_stake_positive",
        ),
        sa.CheckConstraint(
            "total_stakers >= 0",
            name="ck_sample_epoch_summary_stakers_positive",
        ),
        sa.PrimaryKeyConstraint("summary_id", name="pk_sample_validator_epoch_summary"),
        sa.UniqueConstraint(
            "validator_vote_pubkey",
            "epoch",
            name="uq_sample_epoch_summary_validator_epoch",
        ),
    )

    # Create indexes for sample_validator_epoch_summary
    op.create_index(
        "idx_sample_epoch_summary_validator",
        "sample_validator_epoch_summary",
        ["validator_vote_pubkey"],
    )
    op.create_index(
        "idx_sample_epoch_summary_epoch",
        "sample_validator_epoch_summary",
        ["epoch"],
    )

    # Create sample_stake_accounts table
    op.create_table(
        "sample_stake_accounts",
        sa.Column(
            "stake_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique stake account record identifier",
        ),
        sa.Column(
            "epoch_summary_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to parent epoch summary",
        ),
        sa.Column(
            "stake_account_pubkey",
            sa.String(length=44),
            nullable=False,
            comment="Stake account public key address",
        ),
        sa.Column(
            "validator_vote_pubkey",
            sa.String(length=44),
            nullable=False,
            comment="Validator vote account this stake is delegated to",
        ),
        sa.Column(
            "epoch",
            sa.Integer(),
            nullable=False,
            comment="Solana epoch number",
        ),
        sa.Column(
            "staker_wallet_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to staker wallet (controls delegation)",
        ),
        sa.Column(
            "withdrawer_wallet_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to withdrawer wallet (economic beneficiary)",
        ),
        sa.Column(
            "stake_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Stake amount in lamports",
        ),
        sa.Column(
            "activation_epoch",
            sa.Integer(),
            nullable=False,
            comment="Epoch when stake became active",
        ),
        sa.Column(
            "deactivation_epoch",
            sa.Integer(),
            nullable=True,
            comment="Epoch when deactivation started (NULL if still active)",
        ),
        sa.Column(
            "rent_exempt_reserve",
            sa.BigInteger(),
            nullable=False,
            server_default=sa.text("2282880"),
            comment="Rent-exempt reserve in lamports",
        ),
        sa.Column(
            "credits_observed",
            sa.BigInteger(),
            nullable=True,
            comment="Credits observed by this stake account",
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
            ["epoch_summary_id"],
            ["sample_validator_epoch_summary.summary_id"],
            name="fk_sample_stake_accounts_epoch_summary",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["staker_wallet_id"],
            ["partner_wallets.wallet_id"],
            name="fk_sample_stake_accounts_staker_wallet",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["withdrawer_wallet_id"],
            ["partner_wallets.wallet_id"],
            name="fk_sample_stake_accounts_withdrawer_wallet",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "stake_lamports >= 0",
            name="ck_sample_stake_accounts_stake_positive",
        ),
        sa.CheckConstraint(
            "activation_epoch >= 0",
            name="ck_sample_stake_accounts_activation_positive",
        ),
        sa.CheckConstraint(
            "deactivation_epoch IS NULL OR deactivation_epoch >= activation_epoch",
            name="ck_sample_stake_accounts_deactivation_valid",
        ),
        sa.CheckConstraint(
            "rent_exempt_reserve >= 0",
            name="ck_sample_stake_accounts_rent_positive",
        ),
        sa.PrimaryKeyConstraint("stake_account_id", name="pk_sample_stake_accounts"),
        sa.UniqueConstraint(
            "stake_account_pubkey",
            "epoch",
            name="uq_sample_stake_accounts_pubkey_epoch",
        ),
    )

    # Create indexes for sample_stake_accounts
    op.create_index(
        "idx_sample_stake_accounts_epoch",
        "sample_stake_accounts",
        ["epoch"],
    )
    op.create_index(
        "idx_sample_stake_accounts_validator",
        "sample_stake_accounts",
        ["validator_vote_pubkey"],
    )
    op.create_index(
        "idx_sample_stake_accounts_withdrawer",
        "sample_stake_accounts",
        ["withdrawer_wallet_id"],
    )
    op.create_index(
        "idx_sample_stake_accounts_staker",
        "sample_stake_accounts",
        ["staker_wallet_id"],
    )
    op.create_index(
        "idx_sample_stake_accounts_pubkey",
        "sample_stake_accounts",
        ["stake_account_pubkey"],
    )

    # Create sample_epoch_rewards table
    op.create_table(
        "sample_epoch_rewards",
        sa.Column(
            "reward_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Unique reward record identifier",
        ),
        sa.Column(
            "epoch_summary_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to parent epoch summary",
        ),
        sa.Column(
            "validator_vote_pubkey",
            sa.String(length=44),
            nullable=False,
            comment="Validator vote account",
        ),
        sa.Column(
            "epoch",
            sa.Integer(),
            nullable=False,
            comment="Solana epoch number",
        ),
        sa.Column(
            "total_epoch_rewards_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Total rewards for this epoch",
        ),
        sa.Column(
            "validator_commission_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Validator's 5% commission",
        ),
        sa.Column(
            "staker_rewards_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Rewards distributed to stakers (95%)",
        ),
        sa.Column(
            "active_stake_lamports",
            sa.BigInteger(),
            nullable=False,
            comment="Active stake used for reward calculation",
        ),
        sa.Column(
            "is_simulated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Always TRUE for this table",
        ),
        sa.Column(
            "simulation_params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Simulation parameters (APY, epochs/year, etc.)",
        ),
        sa.Column(
            "computed_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Timestamp when rewards were computed",
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
            ["epoch_summary_id"],
            ["sample_validator_epoch_summary.summary_id"],
            name="fk_sample_epoch_rewards_epoch_summary",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "total_epoch_rewards_lamports >= 0",
            name="ck_sample_epoch_rewards_total_positive",
        ),
        sa.CheckConstraint(
            "validator_commission_lamports >= 0",
            name="ck_sample_epoch_rewards_commission_positive",
        ),
        sa.CheckConstraint(
            "staker_rewards_lamports >= 0",
            name="ck_sample_epoch_rewards_staker_positive",
        ),
        sa.CheckConstraint(
            "active_stake_lamports >= 0",
            name="ck_sample_epoch_rewards_stake_positive",
        ),
        sa.PrimaryKeyConstraint("reward_id", name="pk_sample_epoch_rewards"),
        sa.UniqueConstraint(
            "validator_vote_pubkey",
            "epoch",
            name="uq_sample_epoch_rewards_validator_epoch",
        ),
        sa.UniqueConstraint(
            "epoch_summary_id",
            name="uq_sample_epoch_rewards_epoch_summary",
        ),
    )

    # Create indexes for sample_epoch_rewards
    op.create_index(
        "idx_sample_epoch_rewards_validator",
        "sample_epoch_rewards",
        ["validator_vote_pubkey"],
    )
    op.create_index(
        "idx_sample_epoch_rewards_epoch",
        "sample_epoch_rewards",
        ["epoch"],
    )


def downgrade() -> None:
    """Downgrade schema - drop sample data tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("sample_epoch_rewards")
    op.drop_table("sample_stake_accounts")
    op.drop_table("sample_validator_epoch_summary")
