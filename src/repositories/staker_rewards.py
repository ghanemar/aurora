"""Repository for canonical staker rewards detail data access.

This module provides repository class for accessing per-staker,
per-component reward granularity for wallet attribution.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.chains import CanonicalStakerRewardsDetail

from .base import BaseRepository


class StakerRewardsRepository(BaseRepository[CanonicalStakerRewardsDetail]):
    """Repository for canonical staker rewards detail data access.

    Provides methods to query and manage granular per-staker reward
    data broken down by revenue component (MEV, TIPS, etc).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with CanonicalStakerRewardsDetail model.

        Args:
            session: The async database session
        """
        super().__init__(CanonicalStakerRewardsDetail, session)

    async def get(self, id: UUID) -> CanonicalStakerRewardsDetail | None:
        """Get a staker rewards detail record by ID.

        Overrides base method to use detail_id instead of generic id.

        Args:
            id: The detail record UUID

        Returns:
            CanonicalStakerRewardsDetail instance if found, None otherwise
        """
        stmt = select(CanonicalStakerRewardsDetail).where(
            CanonicalStakerRewardsDetail.detail_id == id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_staker(
        self,
        chain_id: str,
        staker_address: str,
        *,
        validator_key: str | None = None,
        revenue_component: str | None = None,
        period_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakerRewardsDetail]:
        """Get all reward details for a specific staker.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            validator_key: Optional validator filter
            revenue_component: Optional component filter (MEV, TIPS, etc)
            period_id: Optional period filter
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakerRewardsDetail instances
        """
        stmt = select(CanonicalStakerRewardsDetail).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.staker_address == staker_address,
            )
        )

        if validator_key:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.validator_key == validator_key
            )

        if revenue_component:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.revenue_component == revenue_component
            )

        if period_id:
            stmt = stmt.where(CanonicalStakerRewardsDetail.period_id == period_id)

        stmt = stmt.order_by(CanonicalStakerRewardsDetail.normalized_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_validator(
        self,
        chain_id: str,
        validator_key: str,
        *,
        period_id: UUID | None = None,
        revenue_component: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakerRewardsDetail]:
        """Get all reward details for a specific validator.

        Args:
            chain_id: The chain identifier
            validator_key: The validator identifier
            period_id: Optional period filter
            revenue_component: Optional component filter (MEV, TIPS, etc)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakerRewardsDetail instances
        """
        stmt = select(CanonicalStakerRewardsDetail).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.validator_key == validator_key,
            )
        )

        if period_id:
            stmt = stmt.where(CanonicalStakerRewardsDetail.period_id == period_id)

        if revenue_component:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.revenue_component == revenue_component
            )

        stmt = stmt.order_by(CanonicalStakerRewardsDetail.normalized_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_period(
        self,
        period_id: UUID,
        *,
        chain_id: str | None = None,
        validator_key: str | None = None,
        staker_address: str | None = None,
        revenue_component: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakerRewardsDetail]:
        """Get all reward details for a specific period.

        Args:
            period_id: The canonical period UUID
            chain_id: Optional chain filter
            validator_key: Optional validator filter
            staker_address: Optional staker filter
            revenue_component: Optional component filter (MEV, TIPS, etc)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakerRewardsDetail instances
        """
        stmt = select(CanonicalStakerRewardsDetail).where(
            CanonicalStakerRewardsDetail.period_id == period_id
        )

        if chain_id:
            stmt = stmt.where(CanonicalStakerRewardsDetail.chain_id == chain_id)

        if validator_key:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.validator_key == validator_key
            )

        if staker_address:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.staker_address == staker_address
            )

        if revenue_component:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.revenue_component == revenue_component
            )

        stmt = stmt.order_by(CanonicalStakerRewardsDetail.normalized_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_staker_total_rewards(
        self,
        chain_id: str,
        staker_address: str,
        period_id: UUID,
        *,
        validator_key: str | None = None,
    ) -> float:
        """Calculate total rewards for a staker in a period.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            period_id: The canonical period UUID
            validator_key: Optional validator filter

        Returns:
            Total reward amount in native units
        """
        stmt = select(
            func.sum(CanonicalStakerRewardsDetail.reward_amount_native)
        ).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.staker_address == staker_address,
                CanonicalStakerRewardsDetail.period_id == period_id,
            )
        )

        if validator_key:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.validator_key == validator_key
            )

        result = await self.session.execute(stmt)
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0

    async def get_staker_rewards_by_component(
        self,
        chain_id: str,
        staker_address: str,
        period_id: UUID,
        *,
        validator_key: str | None = None,
    ) -> dict[str, float]:
        """Get staker rewards broken down by revenue component.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            period_id: The canonical period UUID
            validator_key: Optional validator filter

        Returns:
            Dictionary mapping revenue component to total reward amount
        """
        stmt = (
            select(
                CanonicalStakerRewardsDetail.revenue_component,
                func.sum(CanonicalStakerRewardsDetail.reward_amount_native),
            )
            .where(
                and_(
                    CanonicalStakerRewardsDetail.chain_id == chain_id,
                    CanonicalStakerRewardsDetail.staker_address == staker_address,
                    CanonicalStakerRewardsDetail.period_id == period_id,
                )
            )
            .group_by(CanonicalStakerRewardsDetail.revenue_component)
        )

        if validator_key:
            stmt = stmt.where(
                CanonicalStakerRewardsDetail.validator_key == validator_key
            )

        result = await self.session.execute(stmt)
        return {component: float(amount) for component, amount in result.all()}

    async def get_validator_total_staker_rewards(
        self,
        chain_id: str,
        validator_key: str,
        period_id: UUID,
    ) -> float:
        """Calculate total staker rewards for a validator in a period.

        Args:
            chain_id: The chain identifier
            validator_key: The validator identifier
            period_id: The canonical period UUID

        Returns:
            Total reward amount in native units
        """
        stmt = select(
            func.sum(CanonicalStakerRewardsDetail.reward_amount_native)
        ).where(
            and_(
                CanonicalStakerRewardsDetail.chain_id == chain_id,
                CanonicalStakerRewardsDetail.validator_key == validator_key,
                CanonicalStakerRewardsDetail.period_id == period_id,
            )
        )

        result = await self.session.execute(stmt)
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0

    async def bulk_create(
        self, rewards_data: list[dict]
    ) -> list[CanonicalStakerRewardsDetail]:
        """Bulk create multiple staker rewards detail records.

        Args:
            rewards_data: List of dictionaries with reward detail data

        Returns:
            List of created CanonicalStakerRewardsDetail instances
        """
        rewards = [CanonicalStakerRewardsDetail(**data) for data in rewards_data]
        self.session.add_all(rewards)
        await self.session.flush()

        # Refresh all instances to get database defaults
        for reward in rewards:
            await self.session.refresh(reward)

        return rewards

    async def count_by_staker(
        self,
        chain_id: str,
        staker_address: str,
        *,
        period_id: UUID | None = None,
    ) -> int:
        """Count reward detail records for a specific staker.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            period_id: Optional period filter

        Returns:
            Count of reward detail records
        """
        if period_id:
            return await self.count(
                chain_id=chain_id, staker_address=staker_address, period_id=period_id
            )
        return await self.count(chain_id=chain_id, staker_address=staker_address)

    async def count_by_validator(
        self,
        chain_id: str,
        validator_key: str,
        *,
        period_id: UUID | None = None,
    ) -> int:
        """Count reward detail records for a specific validator.

        Args:
            chain_id: The chain identifier
            validator_key: The validator identifier
            period_id: Optional period filter

        Returns:
            Count of reward detail records
        """
        if period_id:
            return await self.count(
                chain_id=chain_id, validator_key=validator_key, period_id=period_id
            )
        return await self.count(chain_id=chain_id, validator_key=validator_key)
