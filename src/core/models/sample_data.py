"""Sample data models for GlobalStake validator testing.

This module defines SQLAlchemy ORM models for storing sample validator data
from the GlobalStake Excel file (61 epochs, 178 stake accounts). These tables
are used for testing the commission calculation engine with realistic data patterns.

Tables:
- SampleValidatorEpochSummary: Epoch-level aggregations for the sample validator
- SampleStakeAccount: Per-epoch stake account positions
- SampleEpochReward: Simulated epoch rewards (5% APY assumption)

Note: These are temporary testing tables separate from the production canonical schema.
They will be populated during the sample data seeding milestone and used for commission
calculation validation.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import BaseModel

if TYPE_CHECKING:
    from .computation import PartnerWallet


class SampleValidatorEpochSummary(BaseModel):
    """Epoch-level aggregations for the sample GlobalStake validator.

    Stores summary metrics per epoch from the Excel file (Sheet 1: Validator Summary).
    Represents validator-level aggregates across all delegators for each epoch.

    Attributes:
        summary_id: Unique summary record identifier (UUID)
        validator_vote_pubkey: Validator vote account public key (constant across epochs)
        validator_node_pubkey: Validator node public key (constant across epochs)
        validator_name: Human-readable validator name for display (nullable)
        epoch: Solana epoch number (800-860 in sample data)
        commission_bps: Validator commission rate in basis points (500 = 5%)
        rpc_activated_stake_lamports: Activated stake from RPC (may differ from active)
        total_delegated_stake_lamports: Total delegated stake including inactive
        total_active_stake_lamports: Active stake earning rewards
        total_activating_stake_lamports: Stake in warmup period
        total_deactivating_stake_lamports: Stake in cooldown period
        total_stakers: Count of unique stake accounts (178 in sample)
        last_vote: Last vote slot number (nullable)
        root_slot: Root slot number (nullable)
        epoch_vote_account: Epoch vote account flag (nullable)
        is_delinquent: Whether validator was delinquent this epoch
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "sample_validator_epoch_summary"

    summary_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique summary record identifier",
    )

    validator_vote_pubkey: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        comment="Validator vote account public key",
    )

    validator_node_pubkey: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        comment="Validator node public key",
    )

    validator_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Human-readable validator name for display",
    )

    epoch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Solana epoch number (800-860 in sample data)",
    )

    commission_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Validator commission rate in basis points (5% = 500)",
    )

    rpc_activated_stake_lamports: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Activated stake from RPC (may differ from active)",
    )

    total_delegated_stake_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Total delegated stake including inactive",
    )

    total_active_stake_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Active stake earning rewards",
    )

    total_activating_stake_lamports: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Stake in warmup period",
    )

    total_deactivating_stake_lamports: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Stake in cooldown period",
    )

    total_stakers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Count of unique stake accounts (178 in sample)",
    )

    last_vote: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Last vote slot number",
    )

    root_slot: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Root slot number",
    )

    epoch_vote_account: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Epoch vote account flag",
    )

    is_delinquent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether validator was delinquent this epoch",
    )

    # Relationships
    stake_accounts: Mapped[list["SampleStakeAccount"]] = relationship(
        "SampleStakeAccount", back_populates="epoch_summary"
    )

    epoch_rewards: Mapped["SampleEpochReward"] = relationship(
        "SampleEpochReward", back_populates="epoch_summary", uselist=False
    )

    __table_args__ = (
        UniqueConstraint(
            "validator_vote_pubkey",
            "epoch",
            name="uq_sample_epoch_summary_validator_epoch",
        ),
        CheckConstraint(
            "commission_bps >= 0 AND commission_bps <= 10000",
            name="ck_sample_epoch_summary_commission_valid",
        ),
        CheckConstraint(
            "total_delegated_stake_lamports >= 0",
            name="ck_sample_epoch_summary_delegated_stake_positive",
        ),
        CheckConstraint(
            "total_active_stake_lamports >= 0",
            name="ck_sample_epoch_summary_active_stake_positive",
        ),
        CheckConstraint(
            "total_stakers >= 0",
            name="ck_sample_epoch_summary_stakers_positive",
        ),
        Index("idx_sample_epoch_summary_validator", "validator_vote_pubkey"),
        Index("idx_sample_epoch_summary_epoch", "epoch"),
    )


class SampleStakeAccount(BaseModel):
    """Per-epoch stake account positions.

    Stores individual stake account state per epoch from the Excel file
    (Sheet 2: Stake Accounts). One row per stake account per epoch.

    Attributes:
        stake_account_id: Unique stake account record identifier (UUID)
        epoch_summary_id: Reference to parent epoch summary
        stake_account_pubkey: Stake account public key address
        validator_vote_pubkey: Validator vote account this stake is delegated to
        epoch: Solana epoch number
        staker_wallet_id: Reference to staker wallet (controls delegation)
        withdrawer_wallet_id: Reference to withdrawer wallet (economic beneficiary)
        stake_lamports: Stake amount in lamports
        activation_epoch: Epoch when stake became active
        deactivation_epoch: Epoch when deactivation started (NULL if still active)
        rent_exempt_reserve: Rent-exempt reserve in lamports (2282880 default)
        credits_observed: Credits observed by this stake account (nullable)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "sample_stake_accounts"

    stake_account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique stake account record identifier",
    )

    epoch_summary_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sample_validator_epoch_summary.summary_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to parent epoch summary",
    )

    stake_account_pubkey: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        comment="Stake account public key address",
    )

    validator_vote_pubkey: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        comment="Validator vote account this stake is delegated to",
    )

    epoch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Solana epoch number",
    )

    staker_wallet_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partner_wallets.wallet_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staker wallet (controls delegation)",
    )

    withdrawer_wallet_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partner_wallets.wallet_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to withdrawer wallet (economic beneficiary)",
    )

    stake_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Stake amount in lamports",
    )

    activation_epoch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Epoch when stake became active",
    )

    deactivation_epoch: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Epoch when deactivation started (NULL if still active)",
    )

    rent_exempt_reserve: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=2282880,
        comment="Rent-exempt reserve in lamports",
    )

    credits_observed: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Credits observed by this stake account",
    )

    # Relationships
    epoch_summary: Mapped["SampleValidatorEpochSummary"] = relationship(
        "SampleValidatorEpochSummary", back_populates="stake_accounts"
    )

    staker_wallet: Mapped["PartnerWallet"] = relationship(
        "PartnerWallet", foreign_keys=[staker_wallet_id]
    )

    withdrawer_wallet: Mapped["PartnerWallet"] = relationship(
        "PartnerWallet", foreign_keys=[withdrawer_wallet_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "stake_account_pubkey",
            "epoch",
            name="uq_sample_stake_accounts_pubkey_epoch",
        ),
        CheckConstraint(
            "stake_lamports >= 0",
            name="ck_sample_stake_accounts_stake_positive",
        ),
        CheckConstraint(
            "activation_epoch >= 0",
            name="ck_sample_stake_accounts_activation_positive",
        ),
        CheckConstraint(
            "deactivation_epoch IS NULL OR deactivation_epoch >= activation_epoch",
            name="ck_sample_stake_accounts_deactivation_valid",
        ),
        CheckConstraint(
            "rent_exempt_reserve >= 0",
            name="ck_sample_stake_accounts_rent_positive",
        ),
        Index("idx_sample_stake_accounts_epoch", "epoch"),
        Index("idx_sample_stake_accounts_validator", "validator_vote_pubkey"),
        Index("idx_sample_stake_accounts_withdrawer", "withdrawer_wallet_id"),
        Index("idx_sample_stake_accounts_staker", "staker_wallet_id"),
        Index("idx_sample_stake_accounts_pubkey", "stake_account_pubkey"),
    )


class SampleEpochReward(BaseModel):
    """Simulated epoch rewards for sample data testing.

    Stores simulated rewards per epoch based on 5% APY assumption (~73 epochs/year).
    Used to test commission calculation engine with realistic reward distributions.

    Attributes:
        reward_id: Unique reward record identifier (UUID)
        epoch_summary_id: Reference to parent epoch summary
        validator_vote_pubkey: Validator vote account
        epoch: Solana epoch number
        total_epoch_rewards_lamports: Total rewards for this epoch
        validator_commission_lamports: Validator's 5% commission
        staker_rewards_lamports: Rewards distributed to stakers (95%)
        active_stake_lamports: Active stake used for reward calculation
        is_simulated: Always TRUE for this table
        simulation_params: Simulation parameters (APY, epochs/year, etc.)
        computed_at: Timestamp when rewards were computed
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "sample_epoch_rewards"

    reward_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique reward record identifier",
    )

    epoch_summary_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sample_validator_epoch_summary.summary_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="Reference to parent epoch summary",
    )

    validator_vote_pubkey: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        comment="Validator vote account",
    )

    epoch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Solana epoch number",
    )

    total_epoch_rewards_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Total rewards for this epoch",
    )

    validator_commission_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Validator's 5% commission",
    )

    staker_rewards_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Rewards distributed to stakers (95%)",
    )

    active_stake_lamports: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Active stake used for reward calculation",
    )

    is_simulated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Always TRUE for this table",
    )

    simulation_params: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Simulation parameters (APY, epochs/year, etc.)",
    )

    computed_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when rewards were computed",
    )

    # Relationships
    epoch_summary: Mapped["SampleValidatorEpochSummary"] = relationship(
        "SampleValidatorEpochSummary", back_populates="epoch_rewards"
    )

    __table_args__ = (
        UniqueConstraint(
            "validator_vote_pubkey",
            "epoch",
            name="uq_sample_epoch_rewards_validator_epoch",
        ),
        CheckConstraint(
            "total_epoch_rewards_lamports >= 0",
            name="ck_sample_epoch_rewards_total_positive",
        ),
        CheckConstraint(
            "validator_commission_lamports >= 0",
            name="ck_sample_epoch_rewards_commission_positive",
        ),
        CheckConstraint(
            "staker_rewards_lamports >= 0",
            name="ck_sample_epoch_rewards_staker_positive",
        ),
        CheckConstraint(
            "active_stake_lamports >= 0",
            name="ck_sample_epoch_rewards_stake_positive",
        ),
        Index("idx_sample_epoch_rewards_validator", "validator_vote_pubkey"),
        Index("idx_sample_epoch_rewards_epoch", "epoch"),
    )
