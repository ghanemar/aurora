"""Partner wallet API endpoints.

This module provides REST API endpoints for partner wallet management,
including bulk CSV uploads and wallet validation.
"""

import io
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.schemas.partner_wallets import (
    BulkUploadResponse,
    PartnerWalletCreate,
    PartnerWalletListResponse,
    PartnerWalletResponse,
    PartnerWalletUpdate,
    WalletValidationResponse,
)
from src.core.models.users import User
from src.core.services.partner_wallets import PartnerWalletService
from src.db.session import get_db

router = APIRouter(prefix="/partners/{partner_id}/wallets", tags=["partner-wallets"])


@router.post(
    "",
    response_model=PartnerWalletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single partner wallet",
    description="Register a single wallet address for a partner on a specific chain",
)
async def create_wallet(
    partner_id: UUID,
    wallet_data: PartnerWalletCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerWalletResponse:
    """Create a single partner wallet.

    Args:
        partner_id: Partner UUID
        wallet_data: Wallet creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created partner wallet

    Raises:
        HTTPException: If validation fails or creation fails
    """
    service = PartnerWalletService(db)

    try:
        logger.info(f"Creating wallet for partner {partner_id}: {wallet_data}")
        wallet = await service.create_wallet(
            partner_id=partner_id,
            chain_id=wallet_data.chain_id,
            wallet_address=wallet_data.wallet_address,
            introduced_date=wallet_data.introduced_date,
            notes=wallet_data.notes,
        )

        logger.info(f"Wallet created successfully: {wallet.wallet_id}")
        return PartnerWalletResponse.model_validate(wallet)

    except ValueError as e:
        logger.warning(f"Validation error creating wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error creating wallet: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wallet: {str(e)}",
        ) from e


@router.put(
    "/{wallet_id}",
    response_model=PartnerWalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a partner wallet",
    description="Update wallet address, chain, introduced date, notes, or active status",
)
async def update_wallet(
    partner_id: UUID,
    wallet_id: UUID,
    wallet_data: PartnerWalletUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerWalletResponse:
    """Update an existing partner wallet.

    Args:
        partner_id: Partner UUID
        wallet_id: Wallet UUID to update
        wallet_data: Wallet update data (all fields optional)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated partner wallet

    Raises:
        HTTPException: If validation fails or update fails
    """
    service = PartnerWalletService(db)

    try:
        wallet = await service.update_wallet(
            partner_id=partner_id,
            wallet_id=wallet_id,
            chain_id=wallet_data.chain_id,
            wallet_address=wallet_data.wallet_address,
            introduced_date=wallet_data.introduced_date,
            notes=wallet_data.notes,
            is_active=wallet_data.is_active,
        )

        return PartnerWalletResponse.model_validate(wallet)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update wallet: {str(e)}",
        ) from e


@router.post(
    "/bulk",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk upload partner wallets via CSV",
    description="Upload multiple wallets for a partner using a CSV file",
)
async def bulk_upload_wallets(
    partner_id: UUID,
    file: UploadFile = File(..., description="CSV file with wallet data"),
    skip_duplicates: bool = Query(
        False, description="Skip duplicate wallets instead of failing"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BulkUploadResponse:
    """Bulk upload partner wallets from CSV file.

    Expected CSV format:
    chain_id,wallet_address,introduced_date,notes
    solana,ABC123...,2024-01-15,Optional note

    Args:
        partner_id: Partner UUID
        file: CSV file with wallet data
        skip_duplicates: Skip duplicate wallets
        db: Database session
        current_user: Current authenticated user

    Returns:
        Upload results with success/skip/error counts

    Raises:
        HTTPException: If validation fails or upload fails
    """
    service = PartnerWalletService(db)

    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )

    try:
        # Read file contents
        contents = await file.read()
        csv_file = io.BytesIO(contents)

        # Import wallets
        results = await service.import_wallets_from_csv(
            partner_id=partner_id,
            csv_file=csv_file,
            skip_duplicates=skip_duplicates,
        )

        return BulkUploadResponse(**results)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload wallets: {str(e)}",
        ) from e


@router.get(
    "",
    response_model=PartnerWalletListResponse,
    summary="List partner wallets",
    description="Retrieve a paginated list of wallets for a partner with optional filtering",
)
async def list_wallets(
    partner_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    chain_id: str | None = Query(None, description="Filter by chain"),
    active_only: bool = Query(True, description="Only include active wallets"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerWalletListResponse:
    """List all wallets for a partner with pagination.

    Args:
        partner_id: Partner UUID
        page: Page number for pagination
        page_size: Number of items per page
        chain_id: Optional chain filter
        active_only: Only include active wallets
        db: Database session
        current_user: Current authenticated user

    Returns:
        Paginated list of partner wallets

    Raises:
        HTTPException: If retrieval fails
    """
    service = PartnerWalletService(db)

    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get wallets
        wallets = await service.get_wallets_by_partner(
            partner_id,
            chain_id=chain_id,
            active_only=active_only,
            offset=offset,
            limit=page_size,
        )

        # Get total count
        total = await service.count_wallets_by_partner(
            partner_id, active_only=active_only
        )

        # Convert to response models
        wallet_responses = [
            PartnerWalletResponse.model_validate(wallet) for wallet in wallets
        ]

        return PartnerWalletListResponse(
            total=total,
            page=page,
            page_size=page_size,
            wallets=wallet_responses,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve wallets: {str(e)}",
        ) from e


@router.get(
    "/{wallet_id}",
    response_model=PartnerWalletResponse,
    summary="Get a specific wallet",
    description="Retrieve details of a specific partner wallet",
)
async def get_wallet(
    partner_id: UUID,
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PartnerWalletResponse:
    """Get a specific partner wallet by ID.

    Args:
        partner_id: Partner UUID (for authorization)
        wallet_id: Wallet UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Partner wallet details

    Raises:
        HTTPException: If wallet not found or belongs to different partner
    """
    service = PartnerWalletService(db)

    try:
        wallet = await service.get_wallet(wallet_id)

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet with ID {wallet_id} not found",
            )

        # Verify wallet belongs to specified partner
        if wallet.partner_id != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet does not belong to specified partner",
            )

        return PartnerWalletResponse.model_validate(wallet)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve wallet: {str(e)}",
        ) from e


@router.delete(
    "/{wallet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a wallet",
    description="Soft delete a partner wallet (sets is_active to false)",
)
async def deactivate_wallet(
    partner_id: UUID,
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Deactivate a partner wallet (soft delete).

    Args:
        partner_id: Partner UUID (for authorization)
        wallet_id: Wallet UUID
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If wallet not found or belongs to different partner
    """
    service = PartnerWalletService(db)

    try:
        # First get wallet to verify ownership
        wallet = await service.get_wallet(wallet_id)

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet with ID {wallet_id} not found",
            )

        # Verify wallet belongs to specified partner
        if wallet.partner_id != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet does not belong to specified partner",
            )

        # Deactivate wallet
        await service.deactivate_wallet(wallet_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate wallet: {str(e)}",
        ) from e


@router.get(
    "/export/csv",
    summary="Export wallets to CSV",
    description="Export all wallets for a partner as CSV file",
)
async def export_wallets(
    partner_id: UUID,
    chain_id: str | None = Query(None, description="Filter by chain"),
    active_only: bool = Query(True, description="Only include active wallets"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export partner wallets to CSV file.

    Args:
        partner_id: Partner UUID
        chain_id: Optional chain filter
        active_only: Only include active wallets
        db: Database session
        current_user: Current authenticated user

    Returns:
        CSV file as streaming response

    Raises:
        HTTPException: If retrieval fails
    """
    service = PartnerWalletService(db)

    try:
        # Get all wallets (no pagination for export)
        wallets = await service.get_wallets_by_partner(
            partner_id,
            chain_id=chain_id,
            active_only=active_only,
            offset=0,
            limit=10000,  # Large limit for export
        )

        # Generate CSV content
        output = io.StringIO()
        output.write("chain_id,wallet_address,introduced_date,is_active,notes\n")

        for wallet in wallets:
            notes = wallet.notes or ""
            # Escape quotes and commas in notes
            notes = notes.replace('"', '""')
            if "," in notes or '"' in notes:
                notes = f'"{notes}"'

            output.write(
                f"{wallet.chain_id},{wallet.wallet_address},"
                f"{wallet.introduced_date.isoformat()},{wallet.is_active},{notes}\n"
            )

        # Create streaming response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=partner_{partner_id}_wallets.csv"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export wallets: {str(e)}",
        ) from e


@router.get(
    "/{wallet_id}/validate",
    response_model=WalletValidationResponse,
    summary="Validate wallet stake history",
    description="Check if wallet has valid staking history on the blockchain",
)
async def validate_wallet(
    partner_id: UUID,
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletValidationResponse:
    """Validate that a wallet has staking history on the chain.

    Args:
        partner_id: Partner UUID (for authorization)
        wallet_id: Wallet UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Validation results with stake event counts and dates

    Raises:
        HTTPException: If wallet not found or belongs to different partner
    """
    service = PartnerWalletService(db)

    try:
        # First get wallet to verify ownership
        wallet = await service.get_wallet(wallet_id)

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wallet with ID {wallet_id} not found",
            )

        # Verify wallet belongs to specified partner
        if wallet.partner_id != partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wallet does not belong to specified partner",
            )

        # Validate stake history
        validation_result = await service.validate_wallet_stake_history(
            wallet.chain_id, wallet.wallet_address
        )

        return WalletValidationResponse(**validation_result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate wallet: {str(e)}",
        ) from e
