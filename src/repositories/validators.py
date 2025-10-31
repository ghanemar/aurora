"""Repository for validator-related data access.

This module provides repository classes for accessing validator P&L
and metadata information.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.canonical import CanonicalValidatorMeta
from src.core.models.computation import ValidatorPnL

from .base import BaseRepository


class ValidatorPnLRepository(BaseRepository[ValidatorPnL]):
    """Repository for validator P&L data access.

    Provides methods to query and retrieve validator profit & loss
    information with various filtering options.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with ValidatorPnL model.

        Args:
            session: The async database session
        """
        super().__init__(ValidatorPnL, session)

    async def get_by_chain_period_validator(
        self,
        chain_id: str,
        period_id: UUID,
        validator_key: str,
    ) -> ValidatorPnL | None:
        """Get P&L record by unique composite key.

        Args:
            chain_id: Chain identifier
            period_id: Canonical period UUID
            validator_key: Validator identifier

        Returns:
            ValidatorPnL instance if found, None otherwise
        """
        stmt = select(ValidatorPnL).where(
            ValidatorPnL.chain_id == chain_id,
            ValidatorPnL.period_id == period_id,
            ValidatorPnL.validator_key == validator_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chain_and_period(
        self,
        chain_id: str,
        period_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ValidatorPnL]:
        """Get all P&L records for a specific chain and period.

        Args:
            chain_id: Chain identifier
            period_id: Canonical period UUID
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of ValidatorPnL instances
        """
        stmt = (
            select(ValidatorPnL)
            .where(
                ValidatorPnL.chain_id == chain_id,
                ValidatorPnL.period_id == period_id,
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_validator(
        self,
        validator_key: str,
        *,
        chain_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ValidatorPnL]:
        """Get P&L records for a specific validator with optional filters.

        Args:
            validator_key: Validator identifier
            chain_id: Optional chain filter
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of ValidatorPnL instances ordered by computed_at DESC
        """
        stmt = select(ValidatorPnL).where(ValidatorPnL.validator_key == validator_key)

        if chain_id:
            stmt = stmt.where(ValidatorPnL.chain_id == chain_id)

        if start_date:
            stmt = stmt.where(ValidatorPnL.computed_at >= start_date)

        if end_date:
            stmt = stmt.where(ValidatorPnL.computed_at <= end_date)

        stmt = stmt.order_by(ValidatorPnL.computed_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ValidatorMetaRepository(BaseRepository[CanonicalValidatorMeta]):
    """Repository for validator metadata access.

    Provides methods to query validator configuration and status
    metadata with various filtering options.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with CanonicalValidatorMeta model.

        Args:
            session: The async database session
        """
        super().__init__(CanonicalValidatorMeta, session)

    async def get_by_chain_period_validator(
        self,
        chain_id: str,
        period_id: UUID,
        validator_key: str,
    ) -> CanonicalValidatorMeta | None:
        """Get metadata record by unique composite key.

        Args:
            chain_id: Chain identifier
            period_id: Canonical period UUID
            validator_key: Validator identifier

        Returns:
            CanonicalValidatorMeta instance if found, None otherwise
        """
        stmt = select(CanonicalValidatorMeta).where(
            CanonicalValidatorMeta.chain_id == chain_id,
            CanonicalValidatorMeta.period_id == period_id,
            CanonicalValidatorMeta.validator_key == validator_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chain_and_period(
        self,
        chain_id: str,
        period_id: UUID,
        *,
        mev_enabled_only: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalValidatorMeta]:
        """Get all metadata records for a specific chain and period.

        Args:
            chain_id: Chain identifier
            period_id: Canonical period UUID
            mev_enabled_only: Optional filter for MEV-enabled validators
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalValidatorMeta instances
        """
        stmt = select(CanonicalValidatorMeta).where(
            CanonicalValidatorMeta.chain_id == chain_id,
            CanonicalValidatorMeta.period_id == period_id,
        )

        if mev_enabled_only is not None:
            stmt = stmt.where(CanonicalValidatorMeta.is_mev_enabled == mev_enabled_only)

        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_validator(
        self,
        validator_key: str,
        *,
        chain_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CanonicalValidatorMeta]:
        """Get metadata records for a specific validator.

        Args:
            validator_key: Validator identifier
            chain_id: Optional chain filter
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of CanonicalValidatorMeta instances ordered by normalized_at DESC
        """
        stmt = select(CanonicalValidatorMeta).where(
            CanonicalValidatorMeta.validator_key == validator_key
        )

        if chain_id:
            stmt = stmt.where(CanonicalValidatorMeta.chain_id == chain_id)

        stmt = stmt.order_by(CanonicalValidatorMeta.normalized_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# Convenience class for accessing both validator repositories


class ValidatorRegistryRepository(BaseRepository["Validator"]):
    """Repository for validator registry data access.

    Provides methods to query and manage validators in the platform registry.
    This is separate from P&L tracking and focuses on validator CRUD operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with Validator model.

        Args:
            session: The async database session
        """
        from src.core.models.chains import Validator

        super().__init__(Validator, session)

    async def get_by_key_and_chain(
        self,
        validator_key: str,
        chain_id: str,
    ) -> "Validator | None":
        """Get validator by composite key.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier

        Returns:
            Validator instance if found, None otherwise
        """
        from src.core.models.chains import Validator

        stmt = select(Validator).where(
            Validator.validator_key == validator_key,
            Validator.chain_id == chain_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chain(
        self,
        chain_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list["Validator"]:
        """Get all validators for a specific chain.

        Args:
            chain_id: Chain identifier
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Validator instances
        """
        from src.core.models.chains import Validator

        stmt = (
            select(Validator)
            .where(Validator.chain_id == chain_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_by_composite_key(
        self,
        validator_key: str,
        chain_id: str,
        data: dict,
    ) -> "Validator | None":
        """Update validator by composite key.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier
            data: Fields to update

        Returns:
            Updated Validator instance if found, None otherwise
        """
        validator = await self.get_by_key_and_chain(validator_key, chain_id)
        if not validator:
            return None

        for key, value in data.items():
            if hasattr(validator, key):
                setattr(validator, key, value)

        await self.session.commit()
        await self.session.refresh(validator)
        return validator

    async def delete_by_composite_key(
        self,
        validator_key: str,
        chain_id: str,
    ) -> bool:
        """Delete validator by composite key.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier

        Returns:
            True if deleted, False if not found
        """
        validator = await self.get_by_key_and_chain(validator_key, chain_id)
        if not validator:
            return False

        await self.session.delete(validator)
        await self.session.commit()
        return True


class ValidatorRepository:
    """Combined repository for validator data access.

    Provides convenient access to P&L, metadata, and registry repositories
    through a single interface.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with P&L, metadata, and registry repositories.

        Args:
            session: The async database session
        """
        self.pnl = ValidatorPnLRepository(session)
        self.meta = ValidatorMetaRepository(session)
        self.registry = ValidatorRegistryRepository(session)
