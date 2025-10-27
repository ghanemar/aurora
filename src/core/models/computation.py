"""Computation layer models for validator P&L and partner commissions.

This module defines SQLAlchemy ORM models for:
- ValidatorPnL: Computed validator profit & loss per period
- Partners: Partner (introducer) entities
- Agreements: Partner agreement contracts
- AgreementVersions: Historical versions of agreements
- AgreementRules: Commission calculation rules per agreement
- PartnerCommissionLines: Computed commission lines per agreement/period
- PartnerCommissionStatements: Aggregated monthly commission statements
"""

import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import BaseModel

if TYPE_CHECKING:
    from .chains import CanonicalPeriod, Chain


class AgreementStatus(str, enum.Enum):
    """Agreement lifecycle status.

    Attributes:
        DRAFT: Agreement being drafted
        ACTIVE: Agreement is active and commissions are being calculated
        SUSPENDED: Agreement temporarily suspended
        TERMINATED: Agreement permanently terminated
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class RevenueComponent(str, enum.Enum):
    """Validator revenue components.

    Attributes:
        EXEC_FEES: Execution fees
        MEV_TIPS: MEV tips
        VOTE_REWARDS: Vote/block rewards
        COMMISSION: Commission from delegators
    """

    EXEC_FEES = "EXEC_FEES"
    MEV_TIPS = "MEV_TIPS"
    VOTE_REWARDS = "VOTE_REWARDS"
    COMMISSION = "COMMISSION"


class AttributionMethod(str, enum.Enum):
    """Commission attribution methods.

    Attributes:
        CLIENT_REVENUE: Based on client validator revenue
        STAKE_WEIGHT: Based on stake weight contribution
        FIXED_SHARE: Fixed percentage share
    """

    CLIENT_REVENUE = "CLIENT_REVENUE"
    STAKE_WEIGHT = "STAKE_WEIGHT"
    FIXED_SHARE = "FIXED_SHARE"


class StatementStatus(str, enum.Enum):
    """Commission statement lifecycle status.

    Attributes:
        DRAFT: Statement being prepared
        PENDING_APPROVAL: Awaiting approval
        APPROVED: Approved by authorized user
        RELEASED: Released to partner
        PAID: Payment completed
    """

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    RELEASED = "RELEASED"
    PAID = "PAID"


class ValidatorPnL(BaseModel):
    """Computed validator profit & loss per period.

    Aggregates revenue components from canonical layer to compute
    deterministic validator P&L for each period.

    Attributes:
        pnl_id: Unique P&L record identifier (UUID)
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        exec_fees_native: Execution fees in native units (NUMERIC(38,18))
        mev_tips_native: MEV tips in native units (NUMERIC(38,18))
        vote_rewards_native: Vote/block rewards in native units (NUMERIC(38,18))
        commission_native: Commission from delegators in native units (NUMERIC(38,18))
        total_revenue_native: Sum of all revenue components (NUMERIC(38,18))
        computed_at: Timestamp when P&L was computed
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "validator_pnl"

    pnl_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique P&L record identifier",
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

    exec_fees_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="Execution fees in native units",
    )

    mev_tips_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="MEV tips in native units",
    )

    vote_rewards_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="Vote/block rewards in native units",
    )

    commission_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        default=0,
        comment="Commission from delegators in native units",
    )

    total_revenue_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Sum of all revenue components",
    )

    computed_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when P&L was computed",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="validator_pnl")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="validator_pnl"
    )

    __table_args__ = (
        UniqueConstraint(
            "chain_id",
            "period_id",
            "validator_key",
            name="uq_validator_pnl_chain_period_validator",
        ),
        CheckConstraint("exec_fees_native >= 0", name="ck_validator_pnl_exec_fees_positive"),
        CheckConstraint("mev_tips_native >= 0", name="ck_validator_pnl_mev_tips_positive"),
        CheckConstraint("vote_rewards_native >= 0", name="ck_validator_pnl_vote_rewards_positive"),
        CheckConstraint("commission_native >= 0", name="ck_validator_pnl_commission_positive"),
        CheckConstraint(
            "total_revenue_native >= 0", name="ck_validator_pnl_total_revenue_positive"
        ),
        Index("idx_validator_pnl_chain_period", "chain_id", "period_id"),
        Index("idx_validator_pnl_validator", "validator_key"),
        Index("idx_validator_pnl_computed", "computed_at"),
    )


class Partners(BaseModel):
    """Partner (introducer) entities.

    Tracks partner organizations that introduce validators and
    earn commissions based on agreed-upon rates and terms.

    Attributes:
        partner_id: Unique partner identifier (UUID)
        partner_name: Display name for partner organization
        legal_entity_name: Legal entity for contracts/invoicing (nullable)
        contact_email: Primary contact email
        contact_name: Primary contact person name (nullable)
        is_active: Soft-delete flag
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "partners"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique partner identifier",
    )

    partner_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name for partner organization",
    )

    legal_entity_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Legal entity for contracts/invoicing",
    )

    contact_email: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Primary contact email",
    )

    contact_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Primary contact person name",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag",
    )

    # Relationships
    agreements: Mapped[list["Agreements"]] = relationship("Agreements", back_populates="partner")

    commission_lines: Mapped[list["PartnerCommissionLines"]] = relationship(
        "PartnerCommissionLines", back_populates="partner"
    )

    commission_statements: Mapped[list["PartnerCommissionStatements"]] = relationship(
        "PartnerCommissionStatements", back_populates="partner"
    )

    __table_args__ = (
        Index("idx_partners_active", "is_active"),
        Index("idx_partners_email", "contact_email"),
    )


class Agreements(BaseModel):
    """Partner agreement contracts.

    Defines partnership terms and commission structures. Agreements are
    versioned to support historical tracking and term changes.

    Attributes:
        agreement_id: Unique agreement identifier (UUID)
        partner_id: Reference to partner
        agreement_name: Descriptive name for agreement
        current_version: Active version number
        status: Agreement lifecycle status
        effective_from: Agreement start date
        effective_until: Agreement end date (nullable for ongoing)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "agreements"

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique agreement identifier",
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partners.partner_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to partner",
    )

    agreement_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Descriptive name for agreement",
    )

    current_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Active version number",
    )

    status: Mapped[AgreementStatus] = mapped_column(
        nullable=False,
        default=AgreementStatus.DRAFT,
        comment="Agreement lifecycle status",
    )

    effective_from: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Agreement start date",
    )

    effective_until: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Agreement end date (nullable for ongoing)",
    )

    # Relationships
    partner: Mapped["Partners"] = relationship("Partners", back_populates="agreements")

    versions: Mapped[list["AgreementVersions"]] = relationship(
        "AgreementVersions", back_populates="agreement", cascade="all, delete-orphan"
    )

    rules: Mapped[list["AgreementRules"]] = relationship(
        "AgreementRules", back_populates="agreement", cascade="all, delete-orphan"
    )

    commission_lines: Mapped[list["PartnerCommissionLines"]] = relationship(
        "PartnerCommissionLines", back_populates="agreement"
    )

    __table_args__ = (
        Index("idx_agreements_partner", "partner_id"),
        Index("idx_agreements_status", "status"),
        Index("idx_agreements_effective", "effective_from", "effective_until"),
    )


class AgreementVersions(BaseModel):
    """Historical versions of agreements.

    Tracks all versions of agreement terms for audit trail and
    historical commission calculations.

    Attributes:
        version_id: Unique version identifier (UUID)
        agreement_id: Reference to parent agreement
        version_number: Sequential version number
        effective_from: Version start date
        effective_until: Version end date (nullable)
        terms_snapshot: Full agreement terms at this version (JSONB)
        created_by: User who created this version (nullable, references users table)
        created_at: Timestamp when record was created
    """

    __tablename__ = "agreement_versions"

    version_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique version identifier",
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agreements.agreement_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to parent agreement",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential version number",
    )

    effective_from: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="Version start date",
    )

    effective_until: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Version end date (nullable)",
    )

    terms_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Full agreement terms at this version",
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        # Note: users table will be created in Issue #4-5
        # ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this version",
    )

    # Relationships
    agreement: Mapped["Agreements"] = relationship("Agreements", back_populates="versions")

    __table_args__ = (
        UniqueConstraint(
            "agreement_id",
            "version_number",
            name="uq_agreement_versions_agreement_version",
        ),
        Index("idx_agreement_versions_agreement", "agreement_id"),
        Index("idx_agreement_versions_effective", "effective_from", "effective_until"),
    )


class AgreementRules(BaseModel):
    """Commission calculation rules per agreement.

    Defines how commissions are calculated for each agreement, including
    rate structures, attribution methods, and optional caps/floors.

    Attributes:
        rule_id: Unique rule identifier (UUID)
        agreement_id: Reference to parent agreement
        version_number: Agreement version this rule belongs to
        rule_order: Execution order for multi-rule agreements
        chain_id: Optional chain filter (nullable)
        validator_key: Optional validator filter (nullable)
        revenue_component: Which P&L component this rule applies to
        attribution_method: How to calculate commission
        commission_rate_bps: Commission percentage (basis points)
        floor_amount_native: Min commission per period (nullable)
        cap_amount_native: Max commission per period (nullable)
        tier_config: Optional tier escalations (JSONB, nullable)
        is_active: Soft-delete flag
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "agreement_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique rule identifier",
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agreements.agreement_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to parent agreement",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Agreement version this rule belongs to",
    )

    rule_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Execution order for multi-rule agreements",
    )

    chain_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=True,
        comment="Optional chain filter (nullable)",
    )

    validator_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Optional validator filter (nullable)",
    )

    revenue_component: Mapped[RevenueComponent] = mapped_column(
        nullable=False,
        comment="Which P&L component this rule applies to",
    )

    attribution_method: Mapped[AttributionMethod] = mapped_column(
        nullable=False,
        comment="How to calculate commission",
    )

    commission_rate_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Commission percentage (basis points)",
    )

    floor_amount_native: Mapped[float | None] = mapped_column(
        NUMERIC(38, 18),
        nullable=True,
        comment="Min commission per period (nullable)",
    )

    cap_amount_native: Mapped[float | None] = mapped_column(
        NUMERIC(38, 18),
        nullable=True,
        comment="Max commission per period (nullable)",
    )

    tier_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Optional tier escalations (JSONB)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag",
    )

    # Relationships
    agreement: Mapped["Agreements"] = relationship("Agreements", back_populates="rules")

    chain: Mapped[Optional["Chain"]] = relationship("Chain", back_populates="agreement_rules")

    commission_lines: Mapped[list["PartnerCommissionLines"]] = relationship(
        "PartnerCommissionLines", back_populates="rule"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["agreement_id", "version_number"],
            ["agreement_versions.agreement_id", "agreement_versions.version_number"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "commission_rate_bps >= 0 AND commission_rate_bps <= 10000",
            name="ck_agreement_rules_commission_rate_valid",
        ),
        CheckConstraint(
            "floor_amount_native IS NULL OR floor_amount_native >= 0",
            name="ck_agreement_rules_floor_positive",
        ),
        CheckConstraint(
            "cap_amount_native IS NULL OR cap_amount_native >= 0",
            name="ck_agreement_rules_cap_positive",
        ),
        Index("idx_agreement_rules_agreement", "agreement_id"),
        Index("idx_agreement_rules_chain", "chain_id"),
        Index("idx_agreement_rules_validator", "validator_key"),
        Index("idx_agreement_rules_active", "is_active"),
    )


class PartnerCommissionLines(BaseModel):
    """Computed commission lines per agreement/period.

    Individual commission line items calculated per rule, validator,
    and period. Supports manual overrides with audit trail.

    Attributes:
        line_id: Unique line identifier (UUID)
        agreement_id: Reference to agreement
        agreement_version: Agreement version number
        rule_id: Reference to commission rule
        partner_id: Reference to partner
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier (nullable for aggregated)
        revenue_component: Revenue component this commission is based on
        attribution_method: Attribution method used
        base_amount_native: Revenue amount commission is based on (NUMERIC(38,18))
        commission_rate_bps: Commission rate applied (basis points)
        pre_override_amount_native: Calculated commission before override (NUMERIC(38,18))
        override_amount_native: Manual adjustment amount (nullable, NUMERIC(38,18))
        override_reason: Justification for override (nullable)
        override_user_id: User who made override (nullable)
        override_timestamp: When override was made (nullable)
        final_amount_native: Final commission amount (NUMERIC(38,18))
        computed_at: Timestamp when commission was computed
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "partner_commission_lines"

    line_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique line identifier",
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agreements.agreement_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to agreement",
    )

    agreement_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Agreement version number",
    )

    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agreement_rules.rule_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to commission rule",
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partners.partner_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to partner",
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

    validator_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Validator identifier (nullable for aggregated)",
    )

    revenue_component: Mapped[RevenueComponent] = mapped_column(
        nullable=False,
        comment="Revenue component this commission is based on",
    )

    attribution_method: Mapped[AttributionMethod] = mapped_column(
        nullable=False,
        comment="Attribution method used",
    )

    base_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Revenue amount commission is based on",
    )

    commission_rate_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Commission rate applied (basis points)",
    )

    pre_override_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Calculated commission before override",
    )

    override_amount_native: Mapped[float | None] = mapped_column(
        NUMERIC(38, 18),
        nullable=True,
        comment="Manual adjustment amount (nullable)",
    )

    override_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Justification for override",
    )

    override_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        # Note: users table will be created in Issue #4-5
        # ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="User who made override",
    )

    override_timestamp: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When override was made",
    )

    final_amount_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Final commission amount",
    )

    computed_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when commission was computed",
    )

    # Relationships
    agreement: Mapped["Agreements"] = relationship("Agreements", back_populates="commission_lines")

    rule: Mapped["AgreementRules"] = relationship(
        "AgreementRules", back_populates="commission_lines"
    )

    partner: Mapped["Partners"] = relationship("Partners", back_populates="commission_lines")

    chain: Mapped["Chain"] = relationship("Chain", back_populates="partner_commission_lines")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="partner_commission_lines"
    )

    __table_args__ = (
        CheckConstraint("base_amount_native >= 0", name="ck_commission_lines_base_positive"),
        CheckConstraint(
            "commission_rate_bps >= 0 AND commission_rate_bps <= 10000",
            name="ck_commission_lines_rate_valid",
        ),
        CheckConstraint(
            "pre_override_amount_native >= 0",
            name="ck_commission_lines_pre_override_positive",
        ),
        CheckConstraint(
            "final_amount_native >= 0",
            name="ck_commission_lines_final_positive",
        ),
        Index("idx_commission_lines_agreement", "agreement_id"),
        Index("idx_commission_lines_partner", "partner_id"),
        Index("idx_commission_lines_chain_period", "chain_id", "period_id"),
        Index("idx_commission_lines_validator", "validator_key"),
        Index("idx_commission_lines_computed", "computed_at"),
    )


class PartnerCommissionStatements(BaseModel):
    """Aggregated monthly commission statements.

    Summary statements grouping all commission lines for a partner
    per chain/period. Supports approval workflow and payment tracking.

    Attributes:
        statement_id: Unique statement identifier (UUID)
        partner_id: Reference to partner
        chain_id: Reference to chain
        period_id: Reference to canonical period
        total_commission_native: Sum of all commission lines (NUMERIC(38,18))
        line_count: Number of commission lines included
        status: Statement lifecycle status
        approved_by: User who approved statement (nullable)
        approved_at: When statement was approved (nullable)
        released_by: User who released statement (nullable)
        released_at: When statement was released (nullable)
        paid_at: When payment was completed (nullable)
        statement_metadata: Additional statement information (JSONB, nullable)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "partner_commission_statements"

    statement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique statement identifier",
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("partners.partner_id", ondelete="RESTRICT"),
        nullable=False,
        comment="Reference to partner",
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

    total_commission_native: Mapped[float] = mapped_column(
        NUMERIC(38, 18),
        nullable=False,
        comment="Sum of all commission lines",
    )

    line_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of commission lines included",
    )

    status: Mapped[StatementStatus] = mapped_column(
        nullable=False,
        default=StatementStatus.DRAFT,
        comment="Statement lifecycle status",
    )

    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        # Note: users table will be created in Issue #4-5
        # ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="User who approved statement",
    )

    approved_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When statement was approved",
    )

    released_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        # Note: users table will be created in Issue #4-5
        # ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="User who released statement",
    )

    released_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When statement was released",
    )

    paid_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When payment was completed",
    )

    statement_metadata: Mapped[dict | None] = mapped_column(
        "metadata",  # Column name in database
        JSONB,
        nullable=True,
        comment="Additional statement information",
    )

    # Relationships
    partner: Mapped["Partners"] = relationship("Partners", back_populates="commission_statements")

    chain: Mapped["Chain"] = relationship("Chain", back_populates="partner_commission_statements")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="partner_commission_statements"
    )

    __table_args__ = (
        UniqueConstraint(
            "partner_id",
            "chain_id",
            "period_id",
            name="uq_statements_partner_chain_period",
        ),
        CheckConstraint(
            "total_commission_native >= 0",
            name="ck_statements_total_positive",
        ),
        CheckConstraint("line_count >= 0", name="ck_statements_line_count_positive"),
        Index("idx_statements_partner", "partner_id"),
        Index("idx_statements_chain_period", "chain_id", "period_id"),
        Index("idx_statements_status", "status"),
    )
