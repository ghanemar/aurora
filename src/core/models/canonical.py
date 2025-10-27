"""Canonical layer models for normalized validator data.

This module defines SQLAlchemy ORM models for:
- CanonicalValidatorFees: Normalized execution fees per validator/period
- CanonicalValidatorMEV: Normalized MEV tips per validator/period
- CanonicalStakeRewards: Normalized staking rewards per validator/period
- CanonicalValidatorMeta: Normalized validator metadata per period
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import BaseModel

if TYPE_CHECKING:
    from .chains import CanonicalPeriod, Chain, Provider
    from .staging import StagingPayload


class CanonicalValidatorFees(BaseModel):
    """Normalized execution fees per validator/period.

    Provider-independent layer for validator execution fees with full
    traceability to source data.

    Attributes:
        fee_id: Unique fee record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        total_fees_native: Total fees in native units (NUMERIC(38,18))
        fee_count: Number of fee-paying transactions/blocks
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_validator_fees"

    fee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique fee record identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier",
    )

    total_fees_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Total fees in native units (lamports, wei)",
    )

    fee_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of fee-paying transactions/blocks",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_fees")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_fees"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            name="uq_canonical_fees_chain_period_validator",
        ),
        CheckConstraint("total_fees_native >= 0", name="ck_canonical_fees_total_positive"),
        CheckConstraint("fee_count >= 0", name="ck_canonical_fees_count_positive"),
        Index(
            "idx_canonical_fees_chain_period_validator", "chain_id", "period_id", "validator_key"
        ),
        Index("idx_canonical_fees_source_provider", "source_provider_id"),
        Index("idx_canonical_fees_source_payload", "source_payload_id"),
    )


class CanonicalValidatorMEV(BaseModel):
    """Normalized MEV tips per validator/period.

    Provider-independent layer for validator MEV tips with full
    traceability to source data.

    Attributes:
        mev_id: Unique MEV record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        total_mev_native: Total MEV tips in native units (NUMERIC(38,18))
        tip_count: Number of MEV tip distributions
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_validator_mev"

    mev_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique MEV record identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier",
    )

    total_mev_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Total MEV tips in native units (lamports, wei)",
    )

    tip_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of MEV tip distributions",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_mev")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_mev"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            name="uq_canonical_mev_chain_period_validator",
        ),
        CheckConstraint("total_mev_native >= 0", name="ck_canonical_mev_total_positive"),
        CheckConstraint("tip_count >= 0", name="ck_canonical_mev_count_positive"),
        Index("idx_canonical_mev_chain_period_validator", "chain_id", "period_id", "validator_key"),
        Index("idx_canonical_mev_source_provider", "source_provider_id"),
        Index("idx_canonical_mev_source_payload", "source_payload_id"),
    )


class CanonicalStakeRewards(BaseModel):
    """Normalized staking rewards per validator/period.

    Provider-independent layer for staking rewards with optional
    per-staker detail and full traceability to source data.

    Attributes:
        reward_id: Unique reward record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        staker_address: Specific staker address (null if aggregated)
        rewards_native: Staker rewards before commission (NUMERIC(38,18))
        commission_native: Commission earned by validator (NUMERIC(38,18))
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_stake_rewards"

    reward_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique reward record identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier",
    )

    staker_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Specific staker address (null if aggregated)",
    )

    rewards_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Staker rewards before commission in native units",
    )

    commission_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="Commission earned by validator in native units",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_rewards")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_rewards"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        CheckConstraint("rewards_native >= 0", name="ck_canonical_rewards_rewards_positive"),
        CheckConstraint("commission_native >= 0", name="ck_canonical_rewards_commission_positive"),
        Index(
            "idx_canonical_rewards_chain_period_validator", "chain_id", "period_id", "validator_key"
        ),
        Index("idx_canonical_rewards_staker", "staker_address"),
        Index("idx_canonical_rewards_source_provider", "source_provider_id"),
        Index("idx_canonical_rewards_source_payload", "source_payload_id"),
    )


class CanonicalValidatorMeta(BaseModel):
    """Normalized validator metadata per period.

    Provider-independent layer for validator configuration and status
    metadata with full traceability to source data.

    Attributes:
        meta_id: Unique metadata record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        commission_rate_bps: Validator commission rate in basis points (5% = 500)
        is_mev_enabled: Whether validator runs MEV client (Jito for Solana)
        total_stake_native: Total stake amount in native units (NUMERIC(38,18))
        active_stake_native: Active stake amount in native units (NUMERIC(38,18))
        delegator_count: Number of delegators (optional)
        uptime_percentage: Validator uptime percentage (NUMERIC(5,2))
        source_provider_id: Reference to data provider (traceability)
        source_payload_id: Reference to staging payload (traceability)
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_validator_meta"

    meta_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique metadata record identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain",
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to canonical period",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier",
    )

    commission_rate_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Validator commission rate in basis points (5% = 500)",
    )

    is_mev_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether validator runs MEV client (Jito for Solana)",
    )

    total_stake_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="Total stake amount in native units",
    )

    active_stake_native: Mapped[float | None] = mapped_column(
        NUMERIC(38, 18),
        nullable=True,
        comment="Active stake amount in native units",
    )

    delegator_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of delegators",
    )

    uptime_percentage: Mapped[float | None] = mapped_column(
        NUMERIC(5, 2),
        nullable=True,
        comment="Validator uptime percentage (0.00-100.00)",
    )

    source_provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to data provider for traceability",
    )

    source_payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("staging_payloads.payload_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to staging payload for traceability",
    )

    normalized_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_meta")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="canonical_meta"
    )

    source_provider: Mapped["Provider"] = relationship(
        "Provider", foreign_keys=[source_provider_id]
    )

    source_payload: Mapped["StagingPayload"] = relationship(
        "StagingPayload", foreign_keys=[source_payload_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            name="uq_canonical_meta_chain_period_validator",
        ),
        CheckConstraint(
            "commission_rate_bps >= 0 AND commission_rate_bps <= 10000",
            name="ck_canonical_meta_commission_rate_valid",
        ),
        CheckConstraint("total_stake_native >= 0", name="ck_canonical_meta_total_stake_positive"),
        CheckConstraint(
            "active_stake_native IS NULL OR active_stake_native >= 0",
            name="ck_canonical_meta_active_stake_positive",
        ),
        CheckConstraint(
            "delegator_count IS NULL OR delegator_count >= 0",
            name="ck_canonical_meta_delegator_count_positive",
        ),
        CheckConstraint(
            "uptime_percentage IS NULL OR (uptime_percentage >= 0 AND uptime_percentage <= 100)",
            name="ck_canonical_meta_uptime_valid",
        ),
        Index(
            "idx_canonical_meta_chain_period_validator", "chain_id", "period_id", "validator_key"
        ),
        Index("idx_canonical_meta_mev_enabled", "is_mev_enabled"),
        Index("idx_canonical_meta_source_provider", "source_provider_id"),
        Index("idx_canonical_meta_source_payload", "source_payload_id"),
    )
