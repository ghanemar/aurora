"""Partner API endpoints.

This module provides REST API endpoints for partner (introducer) management operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_admin, get_current_user
from src.api.schemas.partners import (
    PartnerCreate,
    PartnerListResponse,
    PartnerResponse,
    PartnerUpdate,
)
from src.core.models.users import User
from src.core.services.partners import PartnerService
from src.db.session import get_db

router = APIRouter(prefix="/partners", tags=["partners"])



@router.get(
    "/count",
    summary="Get partners count",
    description="Get total count of partners",
)
async def get_partners_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get total count of partners.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dictionary with count field

    Raises:
        HTTPException: If retrieval fails
    """
    service = PartnerService(db)

    try:
        count = await service.count_partners(is_active=True)
        return {"count": count}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve partners count: {str(e)}",
        )


@router.get(
    "",
    response_model=PartnerListResponse,
    summary="List all partners",
    description="Retrieve a paginated list of partners with optional filtering by active status",
)
async def list_partners(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerListResponse:
    """List all partners with pagination.

    Args:
        page: Page number for pagination
        page_size: Number of items per page
        is_active: Optional filter by active status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of partners

    Raises:
        HTTPException: If retrieval fails
    """
    service = PartnerService(db)

    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get partners
        partners = await service.get_all_partners(
            offset=offset,
            limit=page_size,
            is_active=is_active,
        )

        # Get total count
        total = await service.count_partners(is_active=is_active)

        # Convert to response models
        data = [PartnerResponse.model_validate(partner) for partner in partners]

        return PartnerListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve partners: {str(e)}",
        )


@router.post(
    "",
    response_model=PartnerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new partner",
    description="Create a new partner with the provided information (Admin only)",
)
async def create_partner(
    partner_data: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> PartnerResponse:
    """Create a new partner.

    Args:
        partner_data: Partner creation data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created partner

    Raises:
        HTTPException: If validation fails or creation fails
    """
    service = PartnerService(db)

    try:
        partner = await service.create_partner(partner_data)
        return PartnerResponse.model_validate(partner)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create partner: {str(e)}",
        )


@router.get(
    "/{partner_id}",
    response_model=PartnerResponse,
    summary="Get partner by ID",
    description="Retrieve detailed information for a specific partner",
)
async def get_partner(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerResponse:
    """Get a partner by ID.

    Args:
        partner_id: Partner UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Partner details

    Raises:
        HTTPException: If partner not found
    """
    service = PartnerService(db)

    partner = await service.get_partner(partner_id)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner with ID {partner_id} not found",
        )

    return PartnerResponse.model_validate(partner)


@router.put(
    "/{partner_id}",
    response_model=PartnerResponse,
    summary="Update partner",
    description="Update an existing partner's information (Admin only)",
)
async def update_partner(
    partner_id: UUID,
    partner_data: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> PartnerResponse:
    """Update an existing partner.

    Args:
        partner_id: Partner UUID
        partner_data: Partner update data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated partner

    Raises:
        HTTPException: If partner not found or update fails
    """
    service = PartnerService(db)

    try:
        partner = await service.update_partner(partner_id, partner_data)
        return PartnerResponse.model_validate(partner)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update partner: {str(e)}",
        )


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete partner",
    description="Soft delete a partner by setting is_active to False (Admin only)",
)
async def delete_partner(
    partner_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> None:
    """Soft delete a partner.

    Args:
        partner_id: Partner UUID
        db: Database session
        current_user: Current authenticated admin user

    Raises:
        HTTPException: If partner not found or deletion fails
    """
    service = PartnerService(db)

    try:
        deleted = await service.delete_partner(partner_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Partner with ID {partner_id} not found",
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete partner: {str(e)}",
        )
