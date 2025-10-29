"""Pydantic schemas for validator-related endpoints.

This module defines request/response schemas for validator P&L
and metadata API endpoints.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValidatorPnLResponse(BaseModel):
    """Response schema for validator P&L data.

    Represents computed profit & loss for a validator in a specific
    period, including all revenue components.
    """

    model_config = ConfigDict(from_attributes=True)

    pnl_id: UUID = Field(..., description="Unique P&L record identifier")
    chain_id: str = Field(..., description="Chain identifier (e.g., 'solana', 'ethereum')")
    period_id: UUID = Field(..., description="Reference to canonical period")
    validator_key: str = Field(..., description="Validator public key or identifier")

    exec_fees_native: Decimal = Field(..., description="Execution fees in native units")
    mev_tips_native: Decimal = Field(..., description="MEV tips in native units")
    vote_rewards_native: Decimal = Field(..., description="Vote/block rewards in native units")
    commission_native: Decimal = Field(..., description="Commission from delegators in native units")
    total_revenue_native: Decimal = Field(..., description="Sum of all revenue components")

    computed_at: datetime = Field(..., description="Timestamp when P&L was computed")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")


class ValidatorPnLListResponse(BaseModel):
    """Response schema for list of validator P&L records."""

    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    data: list[ValidatorPnLResponse] = Field(..., description="List of P&L records")


class ValidatorMetaResponse(BaseModel):
    """Response schema for validator metadata.

    Represents normalized validator configuration and status metadata
    for a specific period.
    """

    model_config = ConfigDict(from_attributes=True)

    meta_id: UUID = Field(..., description="Unique metadata record identifier")
    chain_id: str = Field(..., description="Chain identifier")
    period_id: UUID = Field(..., description="Reference to canonical period")
    validator_key: str = Field(..., description="Validator public key or identifier")

    commission_rate_bps: int = Field(
        ...,
        ge=0,
        le=10000,
        description="Validator commission rate in basis points (5% = 500)"
    )
    is_mev_enabled: bool = Field(..., description="Whether validator runs MEV client")

    total_stake_native: Decimal = Field(..., description="Total stake amount in native units")
    active_stake_native: Decimal | None = Field(
        None,
        description="Active stake amount in native units"
    )
    delegator_count: int | None = Field(None, description="Number of delegators")
    uptime_percentage: Decimal | None = Field(
        None,
        ge=0,
        le=100,
        description="Validator uptime percentage (0.00-100.00)"
    )

    source_provider_id: UUID = Field(..., description="Reference to data provider")
    source_payload_id: UUID = Field(..., description="Reference to staging payload")

    normalized_at: datetime = Field(..., description="Timestamp when data was normalized")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")


class ValidatorMetaListResponse(BaseModel):
    """Response schema for list of validator metadata records."""

    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    data: list[ValidatorMetaResponse] = Field(..., description="List of metadata records")
