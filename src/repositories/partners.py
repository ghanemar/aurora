"""Repository for partner data access.

This module provides repository class for accessing partner
(introducer) information.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import Partners

from .base import BaseRepository


class PartnerRepository(BaseRepository[Partners]):
    """Repository for partner data access.

    Provides methods to query and manage partner organizations
    that introduce validators and earn commissions.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with Partners model.

        Args:
            session: The async database session
        """
        super().__init__(Partners, session)

    async def get(self, id: UUID) -> Partners | None:
        """Get a partner by ID.

        Overrides base method to use partner_id instead of generic id.

        Args:
            id: The partner UUID

        Returns:
            Partners instance if found, None otherwise
        """
        stmt = select(Partners).where(Partners.partner_id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Partners | None:
        """Get a partner by contact email.

        Args:
            email: The contact email address

        Returns:
            Partners instance if found, None otherwise
        """
        stmt = select(Partners).where(Partners.contact_email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_partners(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Partners]:
        """Get all active partners.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of active Partners instances
        """
        stmt = (
            select(Partners)
            .where(Partners.is_active.is_(True))
            .order_by(Partners.partner_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(
        self,
        search_term: str,
        *,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Partners]:
        """Search partners by name (case-insensitive partial match).

        Args:
            search_term: The search term to match against partner name
            active_only: Only include active partners (default: False)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of matching Partners instances
        """
        stmt = select(Partners).where(Partners.partner_name.ilike(f"%{search_term}%"))

        if active_only:
            stmt = stmt.where(Partners.is_active.is_(True))

        stmt = stmt.order_by(Partners.partner_name).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: UUID, **data: dict) -> Partners | None:
        """Update an existing partner by ID.

        Overrides base method to use partner_id instead of generic id.

        Args:
            id: The partner UUID to update
            **data: Column name and value pairs to update

        Returns:
            The updated Partners instance if found, None otherwise
        """
        # Remove any primary key from update data
        data.pop("partner_id", None)

        stmt = (
            select(Partners)
            .where(Partners.partner_id == id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        partner = result.scalar_one_or_none()

        if partner:
            for key, value in data.items():
                if hasattr(partner, key):
                    setattr(partner, key, value)

            await self.session.flush()
            await self.session.refresh(partner)

        return partner

    async def delete(self, id: UUID) -> bool:
        """Soft-delete a partner by setting is_active to False.

        Overrides base method to use soft delete instead of hard delete.

        Args:
            id: The partner UUID to delete

        Returns:
            True if partner was soft-deleted, False if not found
        """
        partner = await self.update(id, is_active=False)
        return partner is not None

    async def count_active(self) -> int:
        """Count total active partners.

        Returns:
            Count of active partners
        """
        return await self.count(is_active=True)
