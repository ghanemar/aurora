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
    validator_vote_pubkey: str = Field(..., description="Validator vote account public key")
    validator_name: str = Field(..., description="Validator display name")
    total_active_stake_lamports: int = Field(
        ..., description="Total validator active stake for this epoch"
    )
    partner_stake_lamports: int = Field(
        ..., description="Partner's stake for this epoch"
    )
    stake_percentage: Decimal = Field(
        ..., description="Partner's stake as percentage of total (0.0-1.0)"
    )
    validator_commission_lamports: int = Field(
        ..., description="Total validator commission for this epoch (5%)"
    )
    total_staker_rewards_lamports: int = Field(
        ..., description="Total staker rewards for this epoch (95%)"
    )
    partner_rewards_lamports: int = Field(
        ..., description="Partner's proportional staker rewards (for display)"
    )
    commission_rate: Decimal = Field(
        ..., description="Partner commission rate applied (0.0-1.0)"
    )
    partner_commission_lamports: int = Field(
        ..., description="Partner's commission in lamports (from validator commission)"
    )


class ValidatorSummarySchema(BaseModel):
    """Summary metrics for a validator in the calculation."""

    validator_vote_pubkey: str = Field(..., description="Validator vote account public key")
    validator_name: str = Field(..., description="Validator display name")
    total_stake_lamports: int = Field(..., description="Average total stake at this validator")
    partner_stake_lamports: int = Field(..., description="Average partner stake at this validator")
    stake_percentage: Decimal = Field(
        ..., description="Partner's stake as percentage of validator total"
    )
    partner_commission_lamports: int = Field(
        ..., description="Total partner commission from this validator"
    )


class CommissionCalculationResponseSchema(BaseModel):
    """Response schema for partner commission calculation."""

    partner_id: UUID = Field(..., description="Partner UUID")
    partner_name: str = Field(..., description="Partner name")
    wallet_count: int = Field(..., description="Number of wallets partner brought")
    validator_count: int = Field(..., description="Number of validators partner stakes with")
    start_epoch: int = Field(..., description="First epoch in range")
    end_epoch: int = Field(..., description="Last epoch in range")
    epoch_count: int = Field(..., description="Number of epochs in range")
    total_partner_stake_lamports: int = Field(
        ..., description="Total stake across all epochs"
    )
    total_partner_rewards_lamports: int = Field(
        ..., description="Total staker rewards across all epochs (for display)"
    )
    commission_rate: Decimal = Field(
        ..., description="Partner commission rate applied (0.0-1.0)"
    )
    total_commission_lamports: int = Field(
        ..., description="Total partner commission in lamports (from validator commission)"
    )
    validator_summaries: list[ValidatorSummarySchema] = Field(
        ..., description="Per-validator summary breakdown"
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
