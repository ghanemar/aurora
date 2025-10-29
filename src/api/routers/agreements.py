"""Agreement API endpoints.

This module provides REST API endpoints for commission agreement management operations.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_active_admin, get_current_user
from src.api.schemas.agreements import (
    AgreementCreate,
    AgreementListResponse,
    AgreementResponse,
    AgreementRuleCreate,
    AgreementRuleResponse,
    AgreementUpdate,
)
from src.core.models.computation import AgreementStatus
from src.core.models.users import User
from src.core.services.agreements import AgreementService
from src.db.session import get_db

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.get(
    "",
    response_model=AgreementListResponse,
    summary="List all agreements",
    description="Retrieve a paginated list of agreements with optional filtering",
)
async def list_agreements(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    partner_id: UUID | None = Query(None, description="Filter by partner UUID"),
    status: AgreementStatus | None = Query(None, description="Filter by agreement status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgreementListResponse:
    """List all agreements with pagination.

    Args:
        page: Page number for pagination
        page_size: Number of items per page
        partner_id: Optional filter by partner
        status: Optional filter by status
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of agreements

    Raises:
        HTTPException: If retrieval fails
    """
    service = AgreementService(db)

    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get agreements
        agreements = await service.get_all_agreements(
            offset=offset,
            limit=page_size,
            partner_id=partner_id,
            status=status,
        )

        # Get total count
        total = await service.count_agreements(partner_id=partner_id, status=status)

        # Convert to response models
        data = [AgreementResponse.model_validate(agreement) for agreement in agreements]

        return AgreementListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agreements: {str(e)}",
        )


@router.post(
    "",
    response_model=AgreementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agreement",
    description="Create a new commission agreement (Admin only)",
)
async def create_agreement(
    agreement_data: AgreementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> AgreementResponse:
    """Create a new agreement.

    Args:
        agreement_data: Agreement creation data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created agreement

    Raises:
        HTTPException: If validation fails or creation fails
    """
    service = AgreementService(db)

    try:
        agreement = await service.create_agreement(agreement_data)
        return AgreementResponse.model_validate(agreement)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agreement: {str(e)}",
        )


@router.get(
    "/{agreement_id}",
    response_model=AgreementResponse,
    summary="Get agreement by ID",
    description="Retrieve detailed information for a specific agreement",
)
async def get_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgreementResponse:
    """Get an agreement by ID.

    Args:
        agreement_id: Agreement UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Agreement details

    Raises:
        HTTPException: If agreement not found
    """
    service = AgreementService(db)

    agreement = await service.get_agreement(agreement_id)

    if not agreement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agreement with ID {agreement_id} not found",
        )

    return AgreementResponse.model_validate(agreement)


@router.put(
    "/{agreement_id}",
    response_model=AgreementResponse,
    summary="Update agreement",
    description="Update an existing agreement (Admin only)",
)
async def update_agreement(
    agreement_id: UUID,
    agreement_data: AgreementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> AgreementResponse:
    """Update an existing agreement.

    Args:
        agreement_id: Agreement UUID
        agreement_data: Agreement update data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated agreement

    Raises:
        HTTPException: If agreement not found or update fails
    """
    service = AgreementService(db)

    try:
        agreement = await service.update_agreement(agreement_id, agreement_data)
        return AgreementResponse.model_validate(agreement)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agreement: {str(e)}",
        )


@router.post(
    "/{agreement_id}/activate",
    response_model=AgreementResponse,
    summary="Activate agreement",
    description="Activate an agreement (change status to ACTIVE) (Admin only)",
)
async def activate_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> AgreementResponse:
    """Activate an agreement.

    Args:
        agreement_id: Agreement UUID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Activated agreement

    Raises:
        HTTPException: If agreement not found or cannot be activated
    """
    service = AgreementService(db)

    try:
        agreement = await service.activate_agreement(agreement_id)
        return AgreementResponse.model_validate(agreement)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate agreement: {str(e)}",
        )


@router.delete(
    "/{agreement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate agreement",
    description="Deactivate an agreement (set status to INACTIVE) (Admin only)",
)
async def deactivate_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> None:
    """Deactivate an agreement.

    Args:
        agreement_id: Agreement UUID
        db: Database session
        current_user: Current authenticated admin user

    Raises:
        HTTPException: If agreement not found or deactivation fails
    """
    service = AgreementService(db)

    try:
        await service.deactivate_agreement(agreement_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate agreement: {str(e)}",
        )


@router.get(
    "/{agreement_id}/rules",
    response_model=list[AgreementRuleResponse],
    summary="Get agreement rules",
    description="Retrieve all rules for a specific agreement",
)
async def get_agreement_rules(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgreementRuleResponse]:
    """Get all rules for an agreement.

    Args:
        agreement_id: Agreement UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of agreement rules

    Raises:
        HTTPException: If retrieval fails
    """
    service = AgreementService(db)

    try:
        rules = await service.get_agreement_rules(agreement_id)
        return [AgreementRuleResponse.model_validate(rule) for rule in rules]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve agreement rules: {str(e)}",
        )


@router.post(
    "/{agreement_id}/rules",
    response_model=AgreementRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add rule to agreement",
    description="Add a new commission rule to an agreement (Admin only)",
)
async def add_agreement_rule(
    agreement_id: UUID,
    rule_data: AgreementRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
) -> AgreementRuleResponse:
    """Add a new rule to an agreement.

    Args:
        agreement_id: Agreement UUID
        rule_data: Rule creation data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created rule

    Raises:
        HTTPException: If validation fails or creation fails
    """
    # Ensure the agreement_id in the path matches the one in the body
    if rule_data.agreement_id != agreement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agreement ID in path must match agreement ID in body",
        )

    service = AgreementService(db)

    try:
        rule = await service.add_rule(rule_data)
        return AgreementRuleResponse.model_validate(rule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add rule to agreement: {str(e)}",
        )
