"""Repository for partner wallet data access.

This module provides repository class for accessing partner wallet
mappings and wallet attribution data.
"""

import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import PartnerWallet

from .base import BaseRepository


class PartnerWalletRepository(BaseRepository[PartnerWallet]):
    """Repository for partner wallet data access.

    Provides methods to query and manage partner-introduced wallet
    mappings for commission attribution.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with PartnerWallet model.

        Args:
            session: The async database session
        """
        super().__init__(PartnerWallet, session)

    async def get(self, id: UUID) -> PartnerWallet | None:
        """Get a partner wallet by ID.

        Overrides base method to use wallet_id instead of generic id.

        Args:
            id: The wallet UUID

        Returns:
            PartnerWallet instance if found, None otherwise
        """
        stmt = select(PartnerWallet).where(PartnerWallet.wallet_id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_address(
        self, chain_id: str, wallet_address: str
    ) -> PartnerWallet | None:
        """Get a partner wallet by chain and address.

        Args:
            chain_id: The chain identifier
            wallet_address: The wallet address

        Returns:
            PartnerWallet instance if found, None otherwise
        """
        stmt = select(PartnerWallet).where(
            and_(
                PartnerWallet.chain_id == chain_id,
                PartnerWallet.wallet_address == wallet_address,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_partner(
        self,
        partner_id: UUID,
        *,
        chain_id: str | None = None,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerWallet]:
        """Get all wallets for a specific partner.

        Args:
            partner_id: The partner UUID
            chain_id: Optional chain filter
            active_only: Only include active wallets (default: False)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of PartnerWallet instances
        """
        stmt = select(PartnerWallet).where(PartnerWallet.partner_id == partner_id)

        if chain_id:
            stmt = stmt.where(PartnerWallet.chain_id == chain_id)

        if active_only:
            stmt = stmt.where(PartnerWallet.is_active.is_(True))

        stmt = (
            stmt.order_by(PartnerWallet.introduced_date.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_chain(
        self,
        chain_id: str,
        *,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerWallet]:
        """Get all partner wallets for a specific chain.

        Args:
            chain_id: The chain identifier
            active_only: Only include active wallets (default: False)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of PartnerWallet instances
        """
        stmt = select(PartnerWallet).where(PartnerWallet.chain_id == chain_id)

        if active_only:
            stmt = stmt.where(PartnerWallet.is_active.is_(True))

        stmt = (
            stmt.order_by(PartnerWallet.introduced_date.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_on_date(
        self, chain_id: str, target_date: datetime.date
    ) -> list[PartnerWallet]:
        """Get all wallets active on a specific date.

        A wallet is considered active if:
        - introduced_date <= target_date
        - is_active = true

        Args:
            chain_id: The chain identifier
            target_date: The date to check wallet activity

        Returns:
            List of PartnerWallet instances active on the target date
        """
        stmt = select(PartnerWallet).where(
            and_(
                PartnerWallet.chain_id == chain_id,
                PartnerWallet.introduced_date <= target_date,
                PartnerWallet.is_active.is_(True),
            )
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(self, wallets_data: list[dict]) -> list[PartnerWallet]:
        """Bulk create multiple partner wallets.

        Args:
            wallets_data: List of dictionaries with wallet data

        Returns:
            List of created PartnerWallet instances
        """
        wallets = [PartnerWallet(**data) for data in wallets_data]
        self.session.add_all(wallets)
        await self.session.flush()

        # Refresh all instances to get database defaults
        for wallet in wallets:
            await self.session.refresh(wallet)

        return wallets

    async def deactivate(self, wallet_id: UUID) -> PartnerWallet | None:
        """Deactivate a partner wallet by setting is_active to False.

        Args:
            wallet_id: The wallet UUID to deactivate

        Returns:
            The updated PartnerWallet instance if found, None otherwise
        """
        stmt = select(PartnerWallet).where(
            PartnerWallet.wallet_id == wallet_id
        ).with_for_update()
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if wallet:
            wallet.is_active = False
            await self.session.flush()
            await self.session.refresh(wallet)

        return wallet

    async def count_by_partner(
        self, partner_id: UUID, *, active_only: bool = False
    ) -> int:
        """Count wallets for a specific partner.

        Args:
            partner_id: The partner UUID
            active_only: Only count active wallets (default: False)

        Returns:
            Count of partner wallets
        """
        if active_only:
            return await self.count(partner_id=partner_id, is_active=True)
        return await self.count(partner_id=partner_id)

    async def exists_for_partner(
        self, partner_id: UUID, chain_id: str, wallet_address: str
    ) -> bool:
        """Check if a wallet already exists for a partner on a chain.

        Args:
            partner_id: The partner UUID
            chain_id: The chain identifier
            wallet_address: The wallet address

        Returns:
            True if wallet exists, False otherwise
        """
        return await self.exists(
            partner_id=partner_id, chain_id=chain_id, wallet_address=wallet_address
        )
