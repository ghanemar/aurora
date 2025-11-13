"""Sample data commission calculation API endpoints.

This module provides REST API endpoints for calculating partner commissions
based on the GlobalStake sample data (epochs 800-860).
"""

import logging
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.schemas.commissions import (
    AllPartnersCommissionResponseSchema,
    CommissionCalculationResponseSchema,
)
from src.core.models.sample_data import SampleEpochReward
from src.core.models.users import User
from src.core.services.commission_calculator import CommissionCalculator
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sample-commissions", tags=["sample-commissions"])


class EpochInfo(BaseModel):
    """Sample data epoch information."""

    epoch: int = Field(..., description="Epoch number")
    total_active_stake_lamports: int = Field(..., description="Total active stake")
    total_staker_rewards_lamports: int = Field(..., description="Total staker rewards")


class EpochsListResponse(BaseModel):
    """Response schema for epochs list."""

    epochs: list[EpochInfo] = Field(..., description="List of available epochs")


@router.get(
    "/epochs",
    response_model=EpochsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available sample data epochs",
    description="Get list of all available epochs in the sample data (800-860)",
)
async def list_sample_epochs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EpochsListResponse:
    """List all available epochs in the sample data.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of epochs with basic information
    """
    try:
        # Query distinct epochs from sample_epoch_rewards and aggregate data
        from sqlalchemy import func

        query = (
            select(
                SampleEpochReward.epoch,
                func.sum(SampleEpochReward.active_stake_lamports).label(
                    "total_active_stake"
                ),
                func.sum(SampleEpochReward.staker_rewards_lamports).label(
                    "total_staker_rewards"
                ),
            )
            .group_by(SampleEpochReward.epoch)
            .order_by(SampleEpochReward.epoch)
        )

        result = await db.execute(query)
        epoch_data = result.all()

        # Convert to response format
        epochs = [
            EpochInfo(
                epoch=row.epoch,
                total_active_stake_lamports=row.total_active_stake,
                total_staker_rewards_lamports=row.total_staker_rewards,
            )
            for row in epoch_data
        ]

        logger.info(f"Retrieved {len(epochs)} sample epochs")
        return EpochsListResponse(epochs=epochs)

    except Exception as e:
        logger.error(
            f"Error retrieving sample epochs: {type(e).__name__}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve epochs: {str(e)}",
        ) from e


@router.get(
    "/partners/{partner_id}",
    response_model=CommissionCalculationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Calculate commission for a specific partner (sample data)",
    description="Calculate commission for a partner across a continuous epoch range using sample data",
)
async def calculate_partner_commission(
    partner_id: UUID,
    start_epoch: int = Query(..., description="First epoch in range (inclusive)", ge=0),
    end_epoch: int = Query(..., description="Last epoch in range (inclusive)", ge=0),
    commission_rate: Decimal = Query(
        Decimal("0.50"),
        description="Partner commission rate as decimal (0.50 = 50% of validator commission)",
        ge=0.0,
        le=1.0,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommissionCalculationResponseSchema:
    """Calculate commission for a specific partner using sample data.

    This endpoint calculates the commission owed to a partner based on:
    - Their stake (via withdrawer wallets) in each epoch
    - Proportional share of validator commission (5%)
    - Partner commission rate applied to validator commission

    The epoch range must be continuous (no gaps).

    Args:
        partner_id: Partner UUID
        start_epoch: First epoch in range
        end_epoch: Last epoch in range
        commission_rate: Commission rate (default 10%)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Commission calculation with per-epoch details

    Raises:
        HTTPException: If validation fails or calculation fails
    """
    calculator = CommissionCalculator(db)

    try:
        logger.info(
            f"Calculating commission for partner {partner_id}: "
            f"epochs {start_epoch}-{end_epoch}, rate {commission_rate}"
        )

        result = await calculator.calculate_partner_commission(
            partner_id=partner_id,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            commission_rate=commission_rate,
        )

        logger.info(
            f"Commission calculated: {result['total_commission_lamports'] / 1e9:.2f} SOL "
            f"for {result['epoch_count']} epochs"
        )

        return CommissionCalculationResponseSchema(**result)

    except ValueError as e:
        logger.warning(f"Validation error calculating commission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            f"Error calculating commission: {type(e).__name__}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate commission: {str(e)}",
        ) from e


@router.get(
    "/all",
    response_model=AllPartnersCommissionResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Calculate commissions for all active partners (sample data)",
    description="Calculate commissions for all active partners with stake in the epoch range",
)
async def calculate_all_partners_commission(
    start_epoch: int = Query(..., description="First epoch in range (inclusive)", ge=0),
    end_epoch: int = Query(..., description="Last epoch in range (inclusive)", ge=0),
    commission_rate: Decimal = Query(
        Decimal("0.50"),
        description="Partner commission rate as decimal (0.50 = 50% of validator commission)",
        ge=0.0,
        le=1.0,
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AllPartnersCommissionResponseSchema:
    """Calculate commissions for all active partners using sample data.

    This endpoint calculates commissions for all active partners
    with stake in the specified epoch range.

    Args:
        start_epoch: First epoch in range
        end_epoch: Last epoch in range
        commission_rate: Commission rate (default 10%)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Commission calculations for all partners

    Raises:
        HTTPException: If validation fails or calculation fails
    """
    calculator = CommissionCalculator(db)

    try:
        logger.info(
            f"Calculating commissions for all partners: "
            f"epochs {start_epoch}-{end_epoch}, rate {commission_rate}"
        )

        results = await calculator.calculate_all_partners_commission(
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            commission_rate=commission_rate,
        )

        partner_schemas = [
            CommissionCalculationResponseSchema(**result) for result in results
        ]

        logger.info(f"Calculated commissions for {len(partner_schemas)} partners")

        return AllPartnersCommissionResponseSchema(
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            epoch_count=end_epoch - start_epoch + 1,
            commission_rate=commission_rate,
            partners=partner_schemas,
        )

    except ValueError as e:
        logger.warning(f"Validation error calculating commissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            f"Error calculating commissions: {type(e).__name__}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate commissions: {str(e)}",
        ) from e
