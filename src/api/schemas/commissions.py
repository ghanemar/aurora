"""Pydantic schemas for commission calculation endpoints.

This module defines request/response schemas for partner commission
calculation API endpoints.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class EpochCommissionDetailSchema(BaseModel):
    """Commission details for a single epoch."""

    epoch: int = Field(..., description="Epoch number")
    total_active_stake_lamports: int = Field(
        ..., description="Total validator active stake for this epoch"
    )
    partner_stake_lamports: int = Field(
        ..., description="Partner's stake for this epoch"
    )
    stake_percentage: Decimal = Field(
        ..., description="Partner's stake as percentage of total (0.0-1.0)"
    )
    total_staker_rewards_lamports: int = Field(
        ..., description="Total staker rewards for this epoch"
    )
    partner_rewards_lamports: int = Field(
        ..., description="Partner's proportional rewards"
    )
    commission_rate: Decimal = Field(
        ..., description="Commission rate applied (0.0-1.0)"
    )
    partner_commission_lamports: int = Field(
        ..., description="Partner's commission in lamports"
    )


class CommissionCalculationResponseSchema(BaseModel):
    """Response schema for partner commission calculation."""

    partner_id: UUID = Field(..., description="Partner UUID")
    partner_name: str = Field(..., description="Partner name")
    start_epoch: int = Field(..., description="First epoch in range")
    end_epoch: int = Field(..., description="Last epoch in range")
    epoch_count: int = Field(..., description="Number of epochs in range")
    total_partner_stake_lamports: int = Field(
        ..., description="Total stake across all epochs"
    )
    total_partner_rewards_lamports: int = Field(
        ..., description="Total rewards across all epochs"
    )
    commission_rate: Decimal = Field(
        ..., description="Commission rate applied (0.0-1.0)"
    )
    total_commission_lamports: int = Field(
        ..., description="Total commission in lamports"
    )
    epoch_details: list[EpochCommissionDetailSchema] = Field(
        ..., description="Per-epoch commission breakdown"
    )


class AllPartnersCommissionResponseSchema(BaseModel):
    """Response schema for all partners commission calculation."""

    start_epoch: int = Field(..., description="First epoch in range")
    end_epoch: int = Field(..., description="Last epoch in range")
    epoch_count: int = Field(..., description="Number of epochs in range")
    commission_rate: Decimal = Field(
        ..., description="Commission rate applied (0.0-1.0)"
    )
    partners: list[CommissionCalculationResponseSchema] = Field(
        ..., description="Commission data for each partner"
    )
