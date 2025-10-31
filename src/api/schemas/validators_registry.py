"""Pydantic schemas for validator registry operations.

This module defines request and response schemas for validator CRUD operations
in the registry (separate from P&L tracking).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidatorRegistryBase(BaseModel):
    """Base schema for validator registry fields."""

    validator_key: str = Field(..., min_length=1, max_length=100, description="Validator public key or identifier")
    chain_id: str = Field(..., min_length=1, max_length=50, description="Blockchain network identifier")
    description: str | None = Field(None, max_length=500, description="Optional description of the validator")


class ValidatorRegistryCreate(ValidatorRegistryBase):
    """Schema for creating a new validator in the registry."""

    pass


class ValidatorRegistryUpdate(BaseModel):
    """Schema for updating an existing validator in the registry."""

    description: str | None = Field(None, max_length=500, description="Optional description of the validator")
    is_active: bool | None = Field(None, description="Whether the validator is active")


class ValidatorRegistryResponse(ValidatorRegistryBase):
    """Schema for validator registry responses."""

    is_active: bool = Field(..., description="Whether the validator is active")
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")

    model_config = ConfigDict(from_attributes=True)


class ValidatorRegistryListResponse(BaseModel):
    """Paginated response for list of validators."""

    total: int = Field(..., description="Total number of validators matching criteria", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1, le=100)
    data: list[ValidatorRegistryResponse] = Field(..., description="List of validators")

    model_config = ConfigDict(from_attributes=True)
