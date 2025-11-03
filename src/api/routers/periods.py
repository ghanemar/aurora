"""Periods API endpoints.

This module provides REST API endpoints for canonical periods (epochs) listing.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.models.chains import CanonicalPeriod
from src.core.models.users import User
from src.db.session import get_db

router = APIRouter(prefix="/periods", tags=["periods"])


class PeriodResponse(BaseModel):
    """Response schema for a canonical period."""

    period_id: UUID = Field(..., description="Period UUID")
    chain_id: str = Field(..., description="Chain identifier")
    epoch_number: int | None = Field(None, description="Epoch number (blockchain-specific)")
    start_time: str = Field(..., description="Period start timestamp")
    end_time: str = Field(..., description="Period end timestamp")


class PeriodsListResponse(BaseModel):
    """Response schema for periods list."""

    total: int = Field(..., description="Total number of periods")
    data: list[PeriodResponse] = Field(..., description="List of periods")


@router.get(
    "",
    response_model=PeriodsListResponse,
    summary="List canonical periods",
    description="Retrieve list of canonical periods (epochs) with optional chain filter",
)
async def list_periods(
    chain_id: str | None = Query(None, description="Filter by chain ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PeriodsListResponse:
    """List canonical periods with pagination and optional chain filter.

    Args:
        chain_id: Optional chain identifier filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of periods
    """
    # Build query
    query = select(CanonicalPeriod).order_by(
        CanonicalPeriod.chain_id, CanonicalPeriod.epoch_number.desc()
    )

    if chain_id:
        query = query.where(CanonicalPeriod.chain_id == chain_id)

    # Get total count
    count_query = select(CanonicalPeriod)
    if chain_id:
        count_query = count_query.where(CanonicalPeriod.chain_id == chain_id)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    periods = result.scalars().all()

    # Convert to response format
    period_responses = [
        PeriodResponse(
            period_id=period.period_id,
            chain_id=period.chain_id,
            epoch_number=period.epoch_number,
            start_time=period.start_time.isoformat(),
            end_time=period.end_time.isoformat(),
        )
        for period in periods
    ]

    return PeriodsListResponse(total=total, data=period_responses)
