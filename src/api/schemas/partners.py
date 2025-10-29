"""Pydantic schemas for partner-related endpoints.

This module defines request/response schemas for partner (introducer)
management API endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PartnerBase(BaseModel):
    """Base schema with common partner fields."""

    partner_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Display name for partner organization"
    )
    legal_entity_name: str | None = Field(
        None,
        max_length=200,
        description="Legal entity for contracts/invoicing"
    )
    contact_email: EmailStr = Field(..., description="Primary contact email")
    contact_name: str | None = Field(
        None,
        max_length=200,
        description="Primary contact person name"
    )


class PartnerCreate(PartnerBase):
    """Request schema for creating a new partner."""

    is_active: bool = Field(default=True, description="Whether partner is active")


class PartnerUpdate(BaseModel):
    """Request schema for updating an existing partner.

    All fields are optional to allow partial updates.
    """

    partner_name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Display name for partner organization"
    )
    legal_entity_name: str | None = Field(
        None,
        max_length=200,
        description="Legal entity for contracts/invoicing"
    )
    contact_email: EmailStr | None = Field(None, description="Primary contact email")
    contact_name: str | None = Field(
        None,
        max_length=200,
        description="Primary contact person name"
    )
    is_active: bool | None = Field(None, description="Whether partner is active")


class PartnerResponse(PartnerBase):
    """Response schema for partner data."""

    model_config = ConfigDict(from_attributes=True)

    partner_id: UUID = Field(..., description="Unique partner identifier")
    is_active: bool = Field(..., description="Whether partner is active")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")


class PartnerListResponse(BaseModel):
    """Response schema for list of partners."""

    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    data: list[PartnerResponse] = Field(..., description="List of partners")
