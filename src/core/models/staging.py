"""Staging layer models for data ingestion.

This module defines SQLAlchemy ORM models for:
- IngestionRun: Metadata tracking for ingestion jobs
- StagingPayload: Raw provider data storage with full traceability
"""

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .chains import CanonicalPeriod, Chain, Provider


class IngestionStatus(str, enum.Enum):
    """Ingestion job execution status.

    Attributes:
        PENDING: Job queued but not started
        RUNNING: Job currently executing
        SUCCESS: Job completed successfully
        FAILED: Job failed with errors
        PARTIAL: Job completed with some errors
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class DataType(str, enum.Enum):
    """Type of data being staged.

    Attributes:
        FEES: Execution fee data
        MEV: MEV tip data
        REWARDS: Staking reward data
        META: Metadata and configuration
    """

    FEES = "FEES"
    MEV = "MEV"
    REWARDS = "REWARDS"
    META = "META"


class IngestionRun(BaseModel):
    """Ingestion job execution tracking.

    Tracks metadata and status for each ingestion job run, providing
    full audit trail and traceability for data ingestion operations.

    Attributes:
        run_id: Unique run identifier (auto-generated UUID)
        chain_id: Reference to chain being ingested
        period_id: Reference to canonical period (nullable)
        started_at: Timestamp when ingestion started
        completed_at: Timestamp when ingestion completed (nullable)
        status: Current job status (PENDING, RUNNING, SUCCESS, FAILED, PARTIAL)
        error_message: Error details if job failed (nullable)
        records_fetched: Total records fetched from providers
        records_staged: Records successfully written to staging
        job_metadata: Job configuration, provider versions, etc. (JSONB)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """

    __tablename__ = "ingestion_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique run identifier",
    )

    chain_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chains.chain_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to chain being ingested",
    )

    period_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("canonical_periods.period_id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to canonical period",
    )

    started_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when ingestion started",
    )

    completed_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Timestamp when ingestion completed",
    )

    status: Mapped[IngestionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=IngestionStatus.PENDING.value,
        comment="Current job status",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if job failed",
    )

    records_fetched: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total records fetched from providers",
    )

    records_staged: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Records successfully written to staging",
    )

    job_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job configuration, provider versions, etc.",
    )

    # Relationships
    chain: Mapped["Chain"] = relationship("Chain", back_populates="ingestion_runs")

    period: Mapped["CanonicalPeriod | None"] = relationship(
        "CanonicalPeriod", back_populates="ingestion_runs"
    )

    staging_payloads: Mapped[list["StagingPayload"]] = relationship(
        "StagingPayload",
        back_populates="ingestion_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "records_fetched >= 0",
            name="ck_ingestion_runs_records_fetched_positive",
        ),
        CheckConstraint(
            "records_staged >= 0",
            name="ck_ingestion_runs_records_staged_positive",
        ),
        Index("idx_ingestion_runs_chain", "chain_id"),
        Index("idx_ingestion_runs_period", "period_id"),
        Index("idx_ingestion_runs_status", "status"),
        Index("idx_ingestion_runs_started", "started_at"),
    )


class StagingPayload(BaseModel):
    """Raw provider data storage.

    Stores unmodified JSON responses from data providers with full
    traceability to source, enabling idempotency and verification.

    Attributes:
        payload_id: Unique payload identifier (auto-generated UUID)
        run_id: Reference to ingestion run
        chain_id: Reference to chain
        period_id: Reference to canonical period
        validator_key: Validator identifier
        provider_id: Reference to data provider
        data_type: Type of data (FEES, MEV, REWARDS, META)
        fetch_timestamp: When data was fetched from provider
        response_hash: SHA-256 hash of raw_payload for verification
        raw_payload: Unmodified JSON response from provider (JSONB)
        created_at: Timestamp when record was created
    """

    __tablename__ = "staging_payloads"

    payload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique payload identifier",
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ingestion_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to ingestion run",
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

    provider_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("providers.provider_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to data provider",
    )

    data_type: Mapped[DataType] = mapped_column(
        String(20),
        nullable=False,
        comment="Type of data being staged",
    )

    fetch_timestamp: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When data was fetched from provider",
    )

    response_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of raw_payload for verification",
    )

    raw_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Unmodified JSON response from provider",
    )

    # Relationships
    ingestion_run: Mapped["IngestionRun"] = relationship(
        "IngestionRun", back_populates="staging_payloads"
    )

    chain: Mapped["Chain"] = relationship("Chain", back_populates="staging_payloads")

    period: Mapped["CanonicalPeriod"] = relationship(
        "CanonicalPeriod", back_populates="staging_payloads"
    )

    provider: Mapped["Provider"] = relationship("Provider", back_populates="staging_payloads")

    __table_args__ = (
        Index("idx_staging_payloads_run", "run_id"),
        Index("idx_staging_payloads_chain_period", "chain_id", "period_id"),
        Index("idx_staging_payloads_validator", "validator_key"),
        Index("idx_staging_payloads_provider", "provider_id"),
        Index("idx_staging_payloads_data_type", "data_type"),
        Index("idx_staging_payloads_raw_payload", "raw_payload", postgresql_using="gin"),
    )
