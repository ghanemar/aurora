"""Pydantic schemas for partner wallet endpoints.

This module defines request/response schemas for partner wallet
management API endpoints including CSV bulk uploads.
"""

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PartnerWalletBase(BaseModel):
    """Base schema with common partner wallet fields."""

    chain_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Chain identifier (e.g., 'solana', 'ethereum')",
    )
    wallet_address: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Wallet address on the blockchain",
    )
    introduced_date: datetime.date = Field(
        ..., description="Date wallet was introduced by partner"
    )
    notes: str | None = Field(
        None, max_length=500, description="Optional notes about this wallet"
    )


class PartnerWalletCreate(PartnerWalletBase):
    """Request schema for creating a new partner wallet."""

    pass


class PartnerWalletUpdate(BaseModel):
    """Request schema for updating an existing partner wallet.

    All fields are optional to allow partial updates.
    """

    chain_id: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        description="Chain identifier (e.g., 'solana', 'ethereum')",
    )
    wallet_address: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Wallet address on the blockchain",
    )
    introduced_date: datetime.date | None = Field(
        None, description="Date wallet was introduced by partner"
    )
    notes: str | None = Field(
        None, max_length=500, description="Optional notes about this wallet"
    )
    is_active: bool | None = Field(None, description="Whether wallet is active")


class PartnerWalletResponse(PartnerWalletBase):
    """Response schema for a single partner wallet."""

    wallet_id: UUID = Field(..., description="Unique wallet identifier")
    partner_id: UUID = Field(..., description="Parent partner identifier")
    is_active: bool = Field(..., description="Whether wallet is active")
    created_at: datetime.datetime = Field(..., description="Creation timestamp")
    updated_at: datetime.datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PartnerWalletListResponse(BaseModel):
    """Response schema for listing partner wallets with pagination."""

    total: int = Field(..., description="Total number of wallets matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    wallets: list[PartnerWalletResponse] = Field(..., description="List of wallets")


class BulkUploadRequest(BaseModel):
    """Request schema for bulk wallet upload (for JSON requests)."""

    wallets: list[PartnerWalletCreate] = Field(
        ..., description="List of wallets to create"
    )
    skip_duplicates: bool = Field(
        False, description="Skip duplicate wallets instead of failing"
    )


class BulkUploadResponse(BaseModel):
    """Response schema for bulk wallet upload results."""

    success: int = Field(..., description="Number of wallets successfully created")
    skipped: int = Field(..., description="Number of duplicate wallets skipped")
    errors: list[dict] = Field(..., description="List of errors encountered")


class WalletValidationResponse(BaseModel):
    """Response schema for wallet stake history validation."""

    valid: bool = Field(..., description="Whether wallet has valid stake history")
    stake_events_count: int = Field(..., description="Number of stake events found")
    first_stake_date: datetime.datetime | None = Field(
        None, description="Date of first stake event"
    )
    last_stake_date: datetime.datetime | None = Field(
        None, description="Date of last stake event"
    )
