"""Repository for commission agreement data access.

This module provides repository classes for accessing partner commission
agreements and their associated rules.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import (
    AgreementRules,
    Agreements,
    AgreementStatus,
    RevenueComponent,
)

from .base import BaseRepository


class AgreementRepository(BaseRepository[Agreements]):
    """Repository for commission agreement data access.

    Provides methods to query and manage partner commission agreements
    including versioning and lifecycle management.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with Agreements model.

        Args:
            session: The async database session
        """
        super().__init__(Agreements, session)

    async def get(self, id: UUID) -> Agreements | None:
        """Get an agreement by ID.

        Overrides base method to use agreement_id instead of generic id.

        Args:
            id: The agreement UUID

        Returns:
            Agreements instance if found, None otherwise
        """
        stmt = select(Agreements).where(Agreements.agreement_id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_partner(
        self,
        partner_id: UUID,
        *,
        status: AgreementStatus | None = None,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Agreements]:
        """Get agreements for a specific partner.

        Args:
            partner_id: Partner UUID
            status: Optional agreement status filter
            active_only: Only include currently active agreements (effective dates)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of Agreements instances
        """
        stmt = select(Agreements).where(Agreements.partner_id == partner_id)

        if status:
            stmt = stmt.where(Agreements.status == status)

        if active_only:
            now = datetime.utcnow()
            stmt = stmt.where(
                Agreements.effective_from <= now,
                (Agreements.effective_until.is_(None)) | (Agreements.effective_until >= now),
            )

        stmt = stmt.order_by(Agreements.effective_from.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_agreements(
        self,
        *,
        as_of_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Agreements]:
        """Get all currently active agreements.

        Args:
            as_of_date: Date to check for active agreements (default: now)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of active Agreements instances
        """
        check_date = as_of_date or datetime.utcnow()

        stmt = (
            select(Agreements)
            .where(
                Agreements.status == AgreementStatus.ACTIVE,
                Agreements.effective_from <= check_date,
                (Agreements.effective_until.is_(None)) | (Agreements.effective_until >= check_date),
            )
            .order_by(Agreements.partner_id, Agreements.effective_from.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: UUID, **data: dict) -> Agreements | None:
        """Update an existing agreement by ID.

        Overrides base method to use agreement_id instead of generic id.

        Args:
            id: The agreement UUID to update
            **data: Column name and value pairs to update

        Returns:
            The updated Agreements instance if found, None otherwise
        """
        # Remove any primary key from update data
        data.pop("agreement_id", None)

        stmt = select(Agreements).where(Agreements.agreement_id == id).with_for_update()
        result = await self.session.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement:
            for key, value in data.items():
                if hasattr(agreement, key):
                    setattr(agreement, key, value)

            await self.session.flush()
            await self.session.refresh(agreement)

        return agreement


class AgreementRuleRepository(BaseRepository[AgreementRules]):
    """Repository for agreement rule data access.

    Provides methods to query and manage commission rules that define
    how partner commissions are calculated.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with AgreementRules model.

        Args:
            session: The async database session
        """
        super().__init__(AgreementRules, session)

    async def get(self, id: UUID) -> AgreementRules | None:
        """Get a rule by ID.

        Overrides base method to use rule_id instead of generic id.

        Args:
            id: The rule UUID

        Returns:
            AgreementRules instance if found, None otherwise
        """
        stmt = select(AgreementRules).where(AgreementRules.rule_id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_agreement(
        self,
        agreement_id: UUID,
        *,
        version_number: int | None = None,
        active_only: bool = False,
    ) -> list[AgreementRules]:
        """Get rules for a specific agreement.

        Args:
            agreement_id: Agreement UUID
            version_number: Optional filter for specific version
            active_only: Only include active rules (default: False)

        Returns:
            List of AgreementRules instances
        """
        stmt = select(AgreementRules).where(AgreementRules.agreement_id == agreement_id)

        if version_number is not None:
            stmt = stmt.where(AgreementRules.version_number == version_number)

        if active_only:
            stmt = stmt.where(AgreementRules.is_active.is_(True))

        stmt = stmt.order_by(AgreementRules.version_number, AgreementRules.rule_order)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_rules_by_agreement(
        self,
        agreement_id: UUID,
        *,
        version_number: int | None = None,
        active_only: bool = False,
    ) -> list[AgreementRules]:
        """Alias for get_by_agreement for backward compatibility."""
        return await self.get_by_agreement(
            agreement_id,
            version_number=version_number,
            active_only=active_only,
        )

    async def get_active_rules(
        self,
        agreement_id: UUID,
        version_number: int,
    ) -> list[AgreementRules]:
        """Get active rules for a specific agreement version."""
        return await self.get_by_agreement(
            agreement_id,
            version_number=version_number,
            active_only=True,
        )

    async def get_by_revenue_component(
        self,
        agreement_id: UUID,
        revenue_component: RevenueComponent,
        *,
        version_number: int | None = None,
    ) -> list[AgreementRules]:
        """Get rules for a specific revenue component.

        Args:
            agreement_id: Agreement UUID
            revenue_component: Revenue component type
            version_number: Optional filter for specific version

        Returns:
            List of AgreementRules instances
        """
        stmt = select(AgreementRules).where(
            AgreementRules.agreement_id == agreement_id,
            AgreementRules.revenue_component == revenue_component,
        )

        if version_number is not None:
            stmt = stmt.where(AgreementRules.version_number == version_number)

        stmt = stmt.order_by(AgreementRules.version_number)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_version(self, agreement_id: UUID, version_number: int) -> int:
        """Deactivate all rules for a specific agreement version.

        Args:
            agreement_id: Agreement UUID
            version_number: Version number to deactivate

        Returns:
            Number of rules deactivated
        """
        stmt = select(AgreementRules).where(
            AgreementRules.agreement_id == agreement_id,
            AgreementRules.version_number == version_number,
            AgreementRules.is_active.is_(True),
        )

        result = await self.session.execute(stmt)
        rules = result.scalars().all()

        count = 0
        for rule in rules:
            rule.is_active = False
            count += 1

        if count > 0:
            await self.session.flush()

        return count
