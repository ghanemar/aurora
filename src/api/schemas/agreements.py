"""Pydantic schemas for commission agreement-related endpoints.

This module defines request/response schemas for partner commission
agreement management API endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.models.computation import (
    AgreementStatus,
    AttributionMethod,
    RevenueComponent,
)


class AgreementBase(BaseModel):
    """Base schema with common agreement fields."""

    agreement_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Descriptive name for agreement"
    )
    effective_from: datetime = Field(..., description="Agreement start date")
    effective_until: datetime | None = Field(
        None,
        description="Agreement end date (null for ongoing)"
    )


class AgreementCreate(AgreementBase):
    """Request schema for creating a new agreement."""

    partner_id: UUID = Field(..., description="Reference to partner")
    status: AgreementStatus = Field(
        default=AgreementStatus.DRAFT,
        description="Agreement lifecycle status"
    )


class AgreementUpdate(BaseModel):
    """Request schema for updating an existing agreement.

    All fields are optional to allow partial updates.
    """

    agreement_name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Descriptive name for agreement"
    )
    status: AgreementStatus | None = Field(None, description="Agreement lifecycle status")
    effective_from: datetime | None = Field(None, description="Agreement start date")
    effective_until: datetime | None = Field(
        None,
        description="Agreement end date (null for ongoing)"
    )


class AgreementResponse(AgreementBase):
    """Response schema for agreement data."""

    model_config = ConfigDict(from_attributes=True)

    agreement_id: UUID = Field(..., description="Unique agreement identifier")
    partner_id: UUID = Field(..., description="Reference to partner")
    current_version: int = Field(..., description="Active version number")
    status: AgreementStatus = Field(..., description="Agreement lifecycle status")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")


class AgreementListResponse(BaseModel):
    """Response schema for list of agreements."""

    total: int = Field(..., description="Total number of records matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of records per page")
    data: list[AgreementResponse] = Field(..., description="List of agreements")


class AgreementRuleBase(BaseModel):
    """Base schema for agreement commission rules."""

    rule_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Descriptive name for rule"
    )
    revenue_component: RevenueComponent = Field(
        ...,
        description="Revenue component this rule applies to"
    )
    commission_rate_bps: int = Field(
        ...,
        ge=0,
        le=10000,
        description="Commission rate in basis points (5% = 500)"
    )
    attribution_method: AttributionMethod = Field(
        ...,
        description="Method for attributing revenue to partner"
    )
    validator_key_pattern: str | None = Field(
        None,
        max_length=200,
        description="Validator key pattern for rule application (SQL LIKE pattern)"
    )


class AgreementRuleCreate(AgreementRuleBase):
    """Request schema for creating an agreement rule."""

    agreement_id: UUID = Field(..., description="Reference to parent agreement")
    version_number: int = Field(..., description="Agreement version this rule applies to")


class AgreementRuleResponse(AgreementRuleBase):
    """Response schema for agreement rule data."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: UUID = Field(..., description="Unique rule identifier")
    agreement_id: UUID = Field(..., description="Reference to parent agreement")
    version_number: int = Field(..., description="Agreement version this rule applies to")
    is_active: bool = Field(..., description="Whether rule is currently active")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")
