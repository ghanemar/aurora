"""Repository for canonical stake events data access.

This module provides repository class for accessing stake lifecycle
events (STAKE, UNSTAKE, RESTAKE) for wallet attribution.
"""

import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.chains import CanonicalStakeEvent, StakeEventType

from .base import BaseRepository


class StakeEventRepository(BaseRepository[CanonicalStakeEvent]):
    """Repository for canonical stake events data access.

    Provides methods to query and manage wallet staking lifecycle events
    for wallet attribution and validation.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with CanonicalStakeEvent model.

        Args:
            session: The async database session
        """
        super().__init__(CanonicalStakeEvent, session)

    async def get(self, id: UUID) -> CanonicalStakeEvent | None:
        """Get a stake event by ID.

        Overrides base method to use stake_event_id instead of generic id.

        Args:
            id: The stake event UUID

        Returns:
            CanonicalStakeEvent instance if found, None otherwise
        """
        stmt = select(CanonicalStakeEvent).where(
            CanonicalStakeEvent.stake_event_id == id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_staker(
        self,
        chain_id: str,
        staker_address: str,
        *,
        validator_key: str | None = None,
        event_type: StakeEventType | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakeEvent]:
        """Get all stake events for a specific staker.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            validator_key: Optional validator filter
            event_type: Optional event type filter (STAKE, UNSTAKE, RESTAKE)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakeEvent instances
        """
        stmt = select(CanonicalStakeEvent).where(
            and_(
                CanonicalStakeEvent.chain_id == chain_id,
                CanonicalStakeEvent.staker_address == staker_address,
            )
        )

        if validator_key:
            stmt = stmt.where(CanonicalStakeEvent.validator_key == validator_key)

        if event_type:
            stmt = stmt.where(CanonicalStakeEvent.event_type == event_type)

        stmt = (
            stmt.order_by(CanonicalStakeEvent.event_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_validator(
        self,
        chain_id: str,
        validator_key: str,
        *,
        event_type: StakeEventType | None = None,
        period_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakeEvent]:
        """Get all stake events for a specific validator.

        Args:
            chain_id: The chain identifier
            validator_key: The validator identifier
            event_type: Optional event type filter (STAKE, UNSTAKE, RESTAKE)
            period_id: Optional period filter
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakeEvent instances
        """
        stmt = select(CanonicalStakeEvent).where(
            and_(
                CanonicalStakeEvent.chain_id == chain_id,
                CanonicalStakeEvent.validator_key == validator_key,
            )
        )

        if event_type:
            stmt = stmt.where(CanonicalStakeEvent.event_type == event_type)

        if period_id:
            stmt = stmt.where(CanonicalStakeEvent.period_id == period_id)

        stmt = (
            stmt.order_by(CanonicalStakeEvent.event_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_period(
        self,
        period_id: UUID,
        *,
        chain_id: str | None = None,
        event_type: StakeEventType | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalStakeEvent]:
        """Get all stake events for a specific period.

        Args:
            period_id: The canonical period UUID
            chain_id: Optional chain filter
            event_type: Optional event type filter (STAKE, UNSTAKE, RESTAKE)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalStakeEvent instances
        """
        stmt = select(CanonicalStakeEvent).where(
            CanonicalStakeEvent.period_id == period_id
        )

        if chain_id:
            stmt = stmt.where(CanonicalStakeEvent.chain_id == chain_id)

        if event_type:
            stmt = stmt.where(CanonicalStakeEvent.event_type == event_type)

        stmt = (
            stmt.order_by(CanonicalStakeEvent.event_timestamp.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self,
        chain_id: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        *,
        validator_key: str | None = None,
        staker_address: str | None = None,
        event_type: StakeEventType | None = None,
    ) -> list[CanonicalStakeEvent]:
        """Get stake events within a specific time range.

        Args:
            chain_id: The chain identifier
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            validator_key: Optional validator filter
            staker_address: Optional staker filter
            event_type: Optional event type filter

        Returns:
            List of CanonicalStakeEvent instances
        """
        stmt = select(CanonicalStakeEvent).where(
            and_(
                CanonicalStakeEvent.chain_id == chain_id,
                CanonicalStakeEvent.event_timestamp >= start_time,
                CanonicalStakeEvent.event_timestamp <= end_time,
            )
        )

        if validator_key:
            stmt = stmt.where(CanonicalStakeEvent.validator_key == validator_key)

        if staker_address:
            stmt = stmt.where(CanonicalStakeEvent.staker_address == staker_address)

        if event_type:
            stmt = stmt.where(CanonicalStakeEvent.event_type == event_type)

        stmt = stmt.order_by(CanonicalStakeEvent.event_timestamp.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_stake_event(
        self,
        chain_id: str,
        staker_address: str,
        validator_key: str,
    ) -> CanonicalStakeEvent | None:
        """Get the most recent stake event for a staker-validator pair.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            validator_key: The validator identifier

        Returns:
            Most recent CanonicalStakeEvent instance if found, None otherwise
        """
        stmt = (
            select(CanonicalStakeEvent)
            .where(
                and_(
                    CanonicalStakeEvent.chain_id == chain_id,
                    CanonicalStakeEvent.staker_address == staker_address,
                    CanonicalStakeEvent.validator_key == validator_key,
                )
            )
            .order_by(CanonicalStakeEvent.event_timestamp.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_create(
        self, events_data: list[dict]
    ) -> list[CanonicalStakeEvent]:
        """Bulk create multiple stake events.

        Args:
            events_data: List of dictionaries with stake event data

        Returns:
            List of created CanonicalStakeEvent instances
        """
        events = [CanonicalStakeEvent(**data) for data in events_data]
        self.session.add_all(events)
        await self.session.flush()

        # Refresh all instances to get database defaults
        for event in events:
            await self.session.refresh(event)

        return events

    async def count_by_validator(
        self,
        chain_id: str,
        validator_key: str,
        *,
        event_type: StakeEventType | None = None,
    ) -> int:
        """Count stake events for a specific validator.

        Args:
            chain_id: The chain identifier
            validator_key: The validator identifier
            event_type: Optional event type filter

        Returns:
            Count of stake events
        """
        filters = {"chain_id": chain_id, "validator_key": validator_key}
        if event_type:
            filters["event_type"] = event_type

        return await self.count(**filters)

    async def count_by_staker(
        self,
        chain_id: str,
        staker_address: str,
        *,
        event_type: StakeEventType | None = None,
    ) -> int:
        """Count stake events for a specific staker.

        Args:
            chain_id: The chain identifier
            staker_address: The staker wallet address
            event_type: Optional event type filter

        Returns:
            Count of stake events
        """
        filters = {"chain_id": chain_id, "staker_address": staker_address}
        if event_type:
            filters["event_type"] = event_type

        return await self.count(**filters)
