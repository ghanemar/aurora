"""Commission API endpoints.

This module provides REST API endpoints for commission calculation and viewing operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.models.users import User
from src.core.services.commissions import CommissionService
from src.db.session import get_db

router = APIRouter(prefix="/commissions", tags=["commissions"])


# Response schemas for commissions
class CommissionLineResponse(BaseModel):
    """Response schema for a single commission line."""

    partner_id: UUID = Field(..., description="Partner UUID")
    agreement_id: UUID = Field(..., description="Agreement UUID")
    rule_id: UUID = Field(..., description="Rule UUID")
    chain_id: str = Field(..., description="Chain identifier")
    period_id: UUID = Field(..., description="Period UUID")
    validator_key: str = Field(..., description="Validator public key")
    revenue_component: str = Field(..., description="Revenue component type")
    base_amount_native: str = Field(..., description="Base amount in native units (as string)")
    commission_rate_bps: int = Field(..., description="Commission rate in basis points")
    commission_native: str = Field(..., description="Commission amount in native units (as string)")
    attribution_method: str = Field(..., description="Attribution method used")


class CommissionBreakdownResponse(BaseModel):
    """Response schema for commission breakdown."""

    total_commission: str = Field(..., description="Total commission (as string)")
    exec_fees_commission: str = Field(..., description="Execution fees commission (as string)")
    mev_commission: str = Field(..., description="MEV commission (as string)")
    rewards_commission: str = Field(..., description="Rewards commission (as string)")
    lines: list[CommissionLineResponse] = Field(..., description="Individual commission lines")


@router.get(
    "/partners/{partner_id}",
    response_model=list[CommissionLineResponse],
    summary="Get commission lines for partner",
    description="Calculate and retrieve commission lines for a partner in a specific period",
)
async def get_partner_commissions(
    partner_id: UUID,
    period_id: UUID = Query(..., description="Period UUID to calculate commissions for"),
    chain_id: str | None = Query(None, description="Optional chain filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CommissionLineResponse]:
    """Get commission lines for a partner in a specific period.

    Args:
        partner_id: Partner UUID
        period_id: Period UUID
        chain_id: Optional chain identifier filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of commission lines

    Raises:
        HTTPException: If calculation fails or partner not found
    """
    service = CommissionService(db)

    try:
        commission_lines = await service.calculate_commissions(
            partner_id=partner_id,
            period_id=period_id,
            chain_id=chain_id,
        )

        # Convert Decimal fields to strings for JSON serialization
        return [
            CommissionLineResponse(
                partner_id=line["partner_id"],
                agreement_id=line["agreement_id"],
                rule_id=line["rule_id"],
                chain_id=line["chain_id"],
                period_id=line["period_id"],
                validator_key=line["validator_key"],
                revenue_component=line["revenue_component"],
                base_amount_native=str(line["base_amount_native"]),
                commission_rate_bps=line["commission_rate_bps"],
                commission_native=str(line["commission_native"]),
                attribution_method=line["attribution_method"],
            )
            for line in commission_lines
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate commissions: {str(e)}",
        )


@router.get(
    "/partners/{partner_id}/breakdown",
    response_model=CommissionBreakdownResponse,
    summary="Get commission breakdown for partner",
    description="Get detailed commission breakdown by component for a partner in a period",
)
async def get_commission_breakdown(
    partner_id: UUID,
    period_id: UUID = Query(..., description="Period UUID"),
    validator_key: str | None = Query(None, description="Optional validator filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommissionBreakdownResponse:
    """Get detailed commission breakdown for a partner.

    Args:
        partner_id: Partner UUID
        period_id: Period UUID
        validator_key: Optional validator key filter
        db: Database session
        current_user: Current authenticated user

    Returns:
        Commission breakdown by component

    Raises:
        HTTPException: If calculation fails
    """
    service = CommissionService(db)

    try:
        breakdown = await service.get_commission_breakdown(
            partner_id=partner_id,
            period_id=period_id,
            validator_key=validator_key,
        )

        # Convert commission lines
        commission_lines = [
            CommissionLineResponse(
                partner_id=line["partner_id"],
                agreement_id=line["agreement_id"],
                rule_id=line["rule_id"],
                chain_id=line["chain_id"],
                period_id=line["period_id"],
                validator_key=line["validator_key"],
                revenue_component=line["revenue_component"],
                base_amount_native=str(line["base_amount_native"]),
                commission_rate_bps=line["commission_rate_bps"],
                commission_native=str(line["commission_native"]),
                attribution_method=line["attribution_method"],
            )
            for line in breakdown["lines"]
        ]

        return CommissionBreakdownResponse(
            total_commission=str(breakdown["total_commission"]),
            exec_fees_commission=str(breakdown["exec_fees_commission"]),
            mev_commission=str(breakdown["mev_commission"]),
            rewards_commission=str(breakdown["rewards_commission"]),
            lines=commission_lines,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get commission breakdown: {str(e)}",
        )
