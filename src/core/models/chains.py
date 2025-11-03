"""Chain registry and configuration models.

This module defines SQLAlchemy ORM models for:
- Chain: Blockchain network definitions
- Provider: External data provider configurations
- ChainProviderMapping: Chain-to-provider relationships
- CanonicalPeriod: Period definitions per chain
- CanonicalValidatorIdentity: Validator identity mappings
- CanonicalStakeEvent: Wallet staking lifecycle events
- CanonicalStakerRewardsDetail: Per-staker rewards granularity
"""

import datetime
import enum
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import BaseModel

if TYPE_CHECKING:
    from .canonical import (
        CanonicalStakeRewards,
        CanonicalValidatorFees,
        CanonicalValidatorMeta,
        CanonicalValidatorMEV,
    )
    from .computation import (
        AgreementRules,
        PartnerCommissionLines,
        PartnerCommissionStatements,
        PartnerWallet,
        ValidatorPnL,
    )
    from .staging import IngestionRun, StagingPayload




class StakeEventType(str, enum.Enum):
    """Staking lifecycle event types.

    Attributes:
        STAKE: Wallet staked tokens to a validator
        UNSTAKE: Wallet unstaked/withdrew tokens from a validator
        RESTAKE: Wallet moved stake from one validator to another
    """

    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    RESTAKE = "RESTAKE"

class Chain(BaseModel):
    """Blockchain network configuration.

    Defines supported blockchain networks and their characteristics for
    multi-chain validator revenue tracking.

    Attributes:
        chain_id: Unique chain identifier (e.g., "solana-mainnet", "ethereum-mainnet")
        name: Human-readable chain name
        period_type: How periods are defined (EPOCH, BLOCK_WINDOW, SLOT_RANGE)
        native_unit: Native token unit (e.g., "lamports", "wei")
        native_decimals: Decimal places for native unit conversion
        finality_lag: Number of periods to wait before considering data final
        is_active: Whether chain is actively tracked (soft-delete flag)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "chains"

    chain_id: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="Unique chain identifier (e.g., 'solana-mainnet')"
    )

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Human-readable chain name"
    )

    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Period definition type (EPOCH, BLOCK_WINDOW, SLOT_RANGE)",
    )

    native_unit: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Native token unit (e.g., 'lamports', 'wei')"
    )

    native_decimals: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Decimal places for native unit conversion"
    )

    finality_lag: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Periods to wait before considering data final"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether chain is actively tracked",
    )

    # Relationships
    provider_mappings: Mapped[list["ChainProviderMapping"]] = relationship(
        "ChainProviderMapping", back_populates="chain", cascade="all, delete-orphan"
    )

    canonical_periods: Mapped[list["CanonicalPeriod"]] = relationship(
        "CanonicalPeriod", back_populates="chain", cascade="all, delete-orphan"
    )

    validator_identities: Mapped[list["CanonicalValidatorIdentity"]] = relationship(
        "CanonicalValidatorIdentity", back_populates="chain", cascade="all, delete-orphan"
    )

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun", back_populates="chain", cascade="all, delete-orphan"
    )

    staging_payloads: Mapped[list["StagingPayload"]] = relationship(
        "StagingPayload", back_populates="chain", cascade="all, delete-orphan"
    )

    canonical_fees: Mapped[list["CanonicalValidatorFees"]] = relationship(
        "CanonicalValidatorFees", back_populates="chain", cascade="all, delete-orphan"
    )

    canonical_mev: Mapped[list["CanonicalValidatorMEV"]] = relationship(
        "CanonicalValidatorMEV", back_populates="chain", cascade="all, delete-orphan"
    )

    canonical_rewards: Mapped[list["CanonicalStakeRewards"]] = relationship(
        "CanonicalStakeRewards", back_populates="chain", cascade="all, delete-orphan"
    )

    canonical_meta: Mapped[list["CanonicalValidatorMeta"]] = relationship(
        "CanonicalValidatorMeta", back_populates="chain", cascade="all, delete-orphan"
    )

    validator_pnl: Mapped[list["ValidatorPnL"]] = relationship(
        "ValidatorPnL", back_populates="chain", cascade="all, delete-orphan"
    )

    agreement_rules: Mapped[list["AgreementRules"]] = relationship(
        "AgreementRules", back_populates="chain"
    )

    partner_commission_lines: Mapped[list["PartnerCommissionLines"]] = relationship(
        "PartnerCommissionLines", back_populates="chain", cascade="all, delete-orphan"
    )

    partner_commission_statements: Mapped[list["PartnerCommissionStatements"]] = relationship(
        "PartnerCommissionStatements", back_populates="chain", cascade="all, delete-orphan"
    )

    validators: Mapped[list["Validator"]] = relationship(
        "Validator", back_populates="chain", cascade="all, delete-orphan"
    )

    partner_wallets: Mapped[list["PartnerWallet"]] = relationship(
        "PartnerWallet", back_populates="chain", cascade="all, delete-orphan"
    )

    stake_events: Mapped[list["CanonicalStakeEvent"]] = relationship(
        "CanonicalStakeEvent", back_populates="chain", cascade="all, delete-orphan"
    )

    staker_rewards_detail: Mapped[list["CanonicalStakerRewardsDetail"]] = relationship(
        "CanonicalStakerRewardsDetail", back_populates="chain", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "period_type IN ('EPOCH', 'BLOCK_WINDOW', 'SLOT_RANGE')", name="ck_chains_period_type"
        ),
        CheckConstraint("native_decimals >= 0", name="ck_chains_native_decimals_positive"),
        CheckConstraint("finality_lag >= 0", name="ck_chains_finality_lag_positive"),
        Index("idx_chains_active", "is_active"),
    )


class Provider(BaseModel):
    """External data provider configuration.

    Defines external data providers and their API configurations for
    fetching blockchain data.

    Attributes:
        provider_id: Unique provider identifier (UUID)
        provider_name: Unique human-readable provider name
        provider_type: Data category provided (FEES, MEV, REWARDS, META, RPC)
        base_url: API base URL (optional)
        api_version: API version string (optional)
        is_enabled: Whether provider is enabled (soft-enable/disable)
        rate_limit_per_minute: API rate limit (requests per minute)
        timeout_seconds: Request timeout in seconds
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "providers"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique provider identifier",
    )

    provider_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique human-readable provider name",
    )

    provider_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Data category provided (FEES, MEV, REWARDS, META, RPC)",
    )

    base_url: Mapped[str | None] = mapped_column(Text, nullable=True, comment="API base URL")

    api_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="API version string"
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True, comment="Whether provider is enabled"
    )

    rate_limit_per_minute: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="API rate limit (requests per minute)"
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=30, comment="Request timeout in seconds"
    )

    # Relationships
    chain_mappings: Mapped[list["ChainProviderMapping"]] = relationship(
        "ChainProviderMapping", back_populates="provider", cascade="all, delete-orphan"
    )

    staging_payloads: Mapped[list["StagingPayload"]] = relationship(
        "StagingPayload", back_populates="provider", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "provider_type IN ('FEES', 'MEV', 'REWARDS', 'META', 'RPC')", name="ck_providers_type"
        ),
        Index("idx_providers_name", "provider_name"),
        Index("idx_providers_type", "provider_type"),
        Index("idx_providers_enabled", "is_enabled"),
    )


class ChainProviderMapping(BaseModel):
    """Chain-to-provider relationship mapping.

    Maps chains to their configured data providers with role-based
    priority for fallback handling.

    Attributes:
        mapping_id: Unique mapping identifier (UUID)
        chain_id: Reference to chain
        provider_id: Reference to provider
        provider_role: Data type this provider supplies (FEES, MEV, REWARDS, META, RPC)
        priority: Source priority (1 = highest) for fallback
        is_active: Whether mapping is active
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "chain_provider_mappings"

    mapping_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique mapping identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to chain",
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to provider",
    )

    provider_role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Data type this provider supplies"
    )

    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Source priority (1 = highest) for fallback"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether mapping is active"
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="provider_mappings")

    provider: Mapped["Provider"] = relationship("Provider", back_populates="chain_mappings")

    __table_args__ = (
        CheckConstraint(
            "provider_role IN ('FEES', 'MEV', 'REWARDS', 'META', 'RPC')",
            name="ck_chain_provider_mappings_role",
        ),
        UniqueConstraint(
            "chain_id", "provider_role", "priority", name="uq_chain_provider_role_priority"
        ),
        Index("idx_chain_provider_chain", "chain_id"),
        Index("idx_chain_provider_provider", "provider_id"),
    )


class CanonicalPeriod(BaseModel):
    """Period definitions per chain.

    Defines time periods for each chain with finalization tracking
    to respect chain-specific finality requirements.

    Attributes:
        period_id: Unique period identifier (UUID)
        chain_id: Reference to chain
        period_identifier: Chain-specific period ID (e.g., "850" for Solana epoch)
        period_start: Period start timestamp
        period_end: Period end timestamp
        is_finalized: Whether period data is considered final
        finalized_at: Timestamp when period was finalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_periods"

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique period identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to chain",
    )

    period_identifier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Chain-specific period ID (e.g., '850' for Solana epoch)",
    )

    period_start: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, comment="Period start timestamp"
    )

    period_end: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, comment="Period end timestamp"
    )

    is_finalized: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether period data is considered final"
    )

    finalized_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="Timestamp when period was finalized"
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="canonical_periods")

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        "IngestionRun", back_populates="period"
    )

    staging_payloads: Mapped[list["StagingPayload"]] = relationship(
        "StagingPayload", back_populates="period", cascade="all, delete-orphan"
    )

    canonical_fees: Mapped[list["CanonicalValidatorFees"]] = relationship(
        "CanonicalValidatorFees", back_populates="period", cascade="all, delete-orphan"
    )

    canonical_mev: Mapped[list["CanonicalValidatorMEV"]] = relationship(
        "CanonicalValidatorMEV", back_populates="period", cascade="all, delete-orphan"
    )

    canonical_rewards: Mapped[list["CanonicalStakeRewards"]] = relationship(
        "CanonicalStakeRewards", back_populates="period", cascade="all, delete-orphan"
    )

    canonical_meta: Mapped[list["CanonicalValidatorMeta"]] = relationship(
        "CanonicalValidatorMeta", back_populates="period", cascade="all, delete-orphan"
    )

    validator_pnl: Mapped[list["ValidatorPnL"]] = relationship(
        "ValidatorPnL", back_populates="period", cascade="all, delete-orphan"
    )

    partner_commission_lines: Mapped[list["PartnerCommissionLines"]] = relationship(
        "PartnerCommissionLines", back_populates="period", cascade="all, delete-orphan"
    )

    partner_commission_statements: Mapped[list["PartnerCommissionStatements"]] = relationship(
        "PartnerCommissionStatements", back_populates="period", cascade="all, delete-orphan"
    )

    stake_events: Mapped[list["CanonicalStakeEvent"]] = relationship(
        "CanonicalStakeEvent", back_populates="period", cascade="all, delete-orphan"
    )

    staker_rewards_detail: Mapped[list["CanonicalStakerRewardsDetail"]] = relationship(
        "CanonicalStakerRewardsDetail", back_populates="period", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("chain_id", "period_identifier", name="uq_canonical_periods_chain_period"),
        Index("idx_canonical_periods_chain", "chain_id"),
        Index("idx_canonical_periods_finalized", "is_finalized"),
        Index("idx_canonical_periods_range", "chain_id", "period_start", "period_end"),
    )


class CanonicalValidatorIdentity(BaseModel):
    """Chain-specific validator identity mappings.

    Maps validator identities across different chains with chain-specific
    public key and address fields.

    Attributes:
        identity_id: Unique identity identifier (UUID)
        chain_id: Reference to chain
        validator_key: Canonical validator identifier (chain-specific primary key)
        vote_pubkey: Solana vote account public key (Solana-specific)
        node_pubkey: Solana node public key (Solana-specific)
        identity_pubkey: Solana identity public key (Solana-specific)
        fee_recipient: Ethereum fee recipient address (Ethereum-specific)
        display_name: Human-readable validator name
        is_active: Whether validator is active
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_validator_identities"

    identity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identity identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to chain",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Canonical validator identifier (chain-specific)"
    )

    vote_pubkey: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Solana vote account public key"
    )

    node_pubkey: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Solana node public key"
    )

    identity_pubkey: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Solana identity public key"
    )

    fee_recipient: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Ethereum fee recipient address"
    )

    display_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Human-readable validator name"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether validator is active"
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="validator_identities")

    __table_args__ = (
        UniqueConstraint(
            "chain_id", "validator_key", name="uq_canonical_validator_identities_chain_key"
        ),
        Index("idx_validator_identities_chain", "chain_id"),
        Index("idx_validator_identities_key", "validator_key"),
    )



class Validator(BaseModel):
    """Validator registry for platform-managed validators.

    This model tracks validators that are actively managed by the platform,
    separate from the P&L data. It provides a registry of validators with
    metadata and status information.
    """

    __tablename__ = "validators"
    __table_args__ = (
        CheckConstraint("validator_key <> ''", name="ck_validators_validator_key_not_empty"),
        Index("ix_validators_chain_id", "chain_id"),
        Index("ix_validators_is_active", "is_active"),
        {"comment": "Registry of validators managed by the platform"},
    )

    # Primary Key
    validator_key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment="Validator public key or identifier",
    )
    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Blockchain network identifier",
    )

    # Fields
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of the validator",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether the validator is active",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when record was created",
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when record was last updated",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship(
        "Chain",
        back_populates="validators",
        foreign_keys=[chain_id],
    )


class CanonicalStakeEvent(BaseModel):
    """Canonical stake lifecycle events for wallet attribution.

    Tracks STAKE/UNSTAKE/RESTAKE events for delegator wallets, enabling
    validation that wallets were actively staking during periods for which
    commissions are attributed.

    Attributes:
        stake_event_id: Unique stake event identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period when event occurred
        validator_key: Validator identifier where staking action occurred
        staker_address: Staker/delegator wallet address
        event_type: Type of staking lifecycle event (STAKE/UNSTAKE/RESTAKE)
        stake_amount_native: Stake amount in native chain units
        event_timestamp: Timestamp when staking event occurred
        source_provider_id: Reference to data provider for traceability
        source_payload_id: Reference to staging payload for traceability
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_stake_events"

    stake_event_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique stake event identifier",
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
        comment="Reference to canonical period when event occurred",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier where staking action occurred",
    )

    staker_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Staker/delegator wallet address",
    )

    event_type: Mapped[StakeEventType] = mapped_column(
        nullable=False,
        comment="Type of staking lifecycle event",
    )

    stake_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Stake amount in native chain units (lamports, wei, etc.)",
    )

    event_timestamp: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Timestamp when staking event occurred",
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

    normalized_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="stake_events")

    period: Mapped["CanonicalPeriod"] = relationship("CanonicalPeriod", back_populates="stake_events")

    provider: Mapped["Provider"] = relationship("Provider")

    __table_args__ = (
        CheckConstraint(
            "stake_amount_native >= 0",
            name="ck_canonical_stake_events_amount_positive",
        ),
        CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_stake_events_staker_not_empty",
        ),
        Index("idx_canonical_stake_events_chain_period", "chain_id", "period_id"),
        Index("idx_canonical_stake_events_validator", "validator_key"),
        Index("idx_canonical_stake_events_staker", "staker_address"),
        Index("idx_canonical_stake_events_timestamp", "event_timestamp"),
        Index("idx_canonical_stake_events_type", "event_type"),
    )


class CanonicalStakerRewardsDetail(BaseModel):
    """Canonical per-staker rewards granularity for wallet attribution.

    Provides per-staker, per-component reward detail enabling precise
    wallet-level commission calculations. This table breaks down rewards
    by revenue component (MEV, TIPS, etc.) for each staker wallet.

    Attributes:
        detail_id: Unique detail record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period when reward was earned
        validator_key: Validator identifier where staker earned rewards
        staker_address: Staker/delegator wallet address that earned rewards
        revenue_component: Revenue component type for granular attribution
        reward_amount_native: Reward amount in native chain units
        stake_amount_native: Stake amount in native chain units during this period
        source_provider_id: Reference to data provider for traceability
        source_payload_id: Reference to staging payload for traceability
        normalized_at: Timestamp when data was normalized
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "canonical_staker_rewards_detail"

    detail_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique detail record identifier",
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
        comment="Reference to canonical period when reward was earned",
    )

    validator_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validator identifier where staker earned rewards",
    )

    staker_address: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Staker/delegator wallet address that earned rewards",
    )

    revenue_component: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Revenue component type for granular attribution",
    )

    reward_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Reward amount in native chain units (lamports, wei, etc.)",
    )

    stake_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Stake amount in native chain units during this period",
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

    normalized_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when data was normalized",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="staker_rewards_detail")

    period: Mapped["CanonicalPeriod"] = relationship("CanonicalPeriod", back_populates="staker_rewards_detail")

    provider: Mapped["Provider"] = relationship("Provider")

    __table_args__ = (
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            "staker_address",
            "revenue_component",
            name="uq_canonical_staker_rewards_detail_unique_record",
        ),
        CheckConstraint(
            "reward_amount_native >= 0",
            name="ck_canonical_staker_rewards_detail_reward_positive",
        ),
        CheckConstraint(
            "stake_amount_native > 0",
            name="ck_canonical_staker_rewards_detail_stake_positive",
        ),
        CheckConstraint(
            "staker_address <> ''",
            name="ck_canonical_staker_rewards_detail_staker_not_empty",
        ),
        Index("idx_canonical_staker_rewards_detail_chain_period", "chain_id", "period_id"),
        Index("idx_canonical_staker_rewards_detail_validator", "validator_key"),
        Index("idx_canonical_staker_rewards_detail_staker", "staker_address"),
        Index("idx_canonical_staker_rewards_detail_component", "revenue_component"),
    )
