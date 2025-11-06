"""Validator API endpoints.

This module provides REST API endpoints for validator P&L operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_admin, get_current_user
from src.api.schemas.validators import ValidatorPnLListResponse, ValidatorPnLResponse
from src.api.schemas.validators_registry import (
    ValidatorRegistryCreate,
    ValidatorRegistryResponse,
)
from src.core.models.users import User
from src.core.services.validators import ValidatorService
from src.db.session import get_db

router = APIRouter(prefix="/validators", tags=["validators"])



@router.get(
    "/stats",
    summary="Get validator statistics",
    description="Get validator counts by chain for dashboard display",
)
async def get_validator_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get validator statistics grouped by chain.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dictionary with total count and counts per chain

    Raises:
        HTTPException: If retrieval fails
    """
    service = ValidatorService(db)

    try:
        stats = await service.get_validator_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validator statistics: {str(e)}",
        )



@router.get(
    "",
    summary="List validators in registry",
    description="Retrieve a paginated list of validators with optional chain filter",
)
async def list_validators(
    chain_id: str | None = Query(None, description="Filter by chain identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all validators in the registry with pagination.

    Args:
        chain_id: Optional chain identifier filter
        page: Page number for pagination
        page_size: Number of items per page
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of validators

    Raises:
        HTTPException: If retrieval fails
    """
    from src.api.schemas.validators_registry import (
        ValidatorRegistryListResponse,
        ValidatorRegistryResponse,
    )

    service = ValidatorService(db)

    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get validators
        validators = await service.get_all_validators_registry(
            chain_id=chain_id,
            offset=offset,
            limit=page_size,
        )

        # Get total count
        total = await service.count_validators_registry(chain_id=chain_id)

        # Convert to response models
        data = [ValidatorRegistryResponse.model_validate(v) for v in validators]

        return ValidatorRegistryListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=data,
        ).model_dump()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validators: {str(e)}",
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create new validator",
    description="Register a new validator in the platform",
)
async def create_validator(
    validator_data: ValidatorRegistryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> dict:
    """Create a new validator in the registry.

    Args:
        validator_data: Validator creation data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created validator

    Raises:
        HTTPException: If creation fails or validator already exists
    """
    service = ValidatorService(db)

    try:
        validator = await service.create_validator(
            validator_key=validator_data.validator_key,
            chain_id=validator_data.chain_id,
            description=validator_data.description,
        )

        return ValidatorRegistryResponse.model_validate(validator).model_dump()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create validator: {str(e)}",
        )


@router.patch(
    "/{validator_key}/{chain_id}",
    summary="Update validator",
    description="Update an existing validator's information",
)
async def update_validator(
    validator_key: str,
    chain_id: str,
    validator_data: "ValidatorRegistryUpdate",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> dict:
    """Update an existing validator in the registry.

    Args:
        validator_key: Validator identifier
        chain_id: Chain identifier
        validator_data: Validator update data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated validator

    Raises:
        HTTPException: If validator not found or update fails
    """
    from src.api.schemas.validators_registry import (
        ValidatorRegistryResponse,
        ValidatorRegistryUpdate,
    )

    service = ValidatorService(db)

    try:
        validator = await service.update_validator(
            validator_key=validator_key,
            chain_id=chain_id,
            description=validator_data.description,
            is_active=validator_data.is_active,
        )

        if not validator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validator {validator_key} not found for chain {chain_id}",
            )

        return ValidatorRegistryResponse.model_validate(validator).model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validator: {str(e)}",
        )


@router.delete(
    "/{validator_key}/{chain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete validator",
    description="Remove a validator from the registry",
)
async def delete_validator(
    validator_key: str,
    chain_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> None:
    """Delete a validator from the registry.

    Args:
        validator_key: Validator identifier
        chain_id: Chain identifier
        db: Database session
        current_user: Current authenticated admin user

    Raises:
        HTTPException: If validator not found or deletion fails
    """
    service = ValidatorService(db)

    try:
        deleted = await service.delete_validator(
            validator_key=validator_key,
            chain_id=chain_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validator {validator_key} not found for chain {chain_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete validator: {str(e)}",
        )


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
