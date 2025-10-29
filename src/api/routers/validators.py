"""Validator API endpoints.

This module provides REST API endpoints for validator P&L operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.schemas.validators import ValidatorPnLListResponse, ValidatorPnLResponse
from src.core.models.users import User
from src.core.services.validators import ValidatorService
from src.db.session import get_db

router = APIRouter(prefix="/validators", tags=["validators"])


@router.get(
    "/{validator_key}/pnl",
    response_model=ValidatorPnLListResponse,
    summary="Get validator P&L records",
    description="Retrieve P&L records for a specific validator with optional filtering by chain and period",
)
async def get_validator_pnl(
    validator_key: str,
    chain_id: str | None = Query(None, description="Filter by chain identifier"),
    period_id: UUID | None = Query(None, description="Filter by period UUID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidatorPnLListResponse:
    """Get P&L records for a validator.

    Args:
        validator_key: Validator public key or identifier
        chain_id: Optional chain identifier filter
        period_id: Optional period UUID filter
        page: Page number for pagination
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of P&L records

    Raises:
        HTTPException: If validation fails or data not found
    """
    service = ValidatorService(db)

    try:
        # Get all matching P&L records
        pnl_records = await service.get_validator_pnl(
            validator_key=validator_key,
            chain_id=chain_id,
            period_id=period_id,
        )

        # Calculate pagination
        total = len(pnl_records)
        offset = (page - 1) * page_size
        paginated_records = pnl_records[offset : offset + page_size]

        # Convert to response models
        data = [ValidatorPnLResponse.model_validate(record) for record in paginated_records]

        return ValidatorPnLListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validator P&L: {str(e)}",
        )


@router.get(
    "/{validator_key}/pnl/{period_id}",
    response_model=ValidatorPnLResponse,
    summary="Get validator P&L for specific period",
    description="Retrieve P&L record for a validator in a specific period",
)
async def get_validator_pnl_by_period(
    validator_key: str,
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidatorPnLResponse:
    """Get P&L record for a validator in a specific period.

    Args:
        validator_key: Validator public key or identifier
        period_id: Period UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        P&L record for the specified period

    Raises:
        HTTPException: If validation fails or P&L not found
    """
    service = ValidatorService(db)

    try:
        pnl_record = await service.get_validator_pnl_by_period(
            validator_key=validator_key,
            period_id=period_id,
        )

        if not pnl_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"P&L not found for validator {validator_key} in period {period_id}",
            )

        return ValidatorPnLResponse.model_validate(pnl_record)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validator P&L: {str(e)}",
        )
